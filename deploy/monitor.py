#!/usr/bin/env python3

import os
import sys
import signal

from time import sleep
from hashlib import md5
from collections import OrderedDict

import docker

# constants
RESOURCES_DIRNAME = "/var/log/featurehub/resources/"
STATS_TYPES = [
    "pids_stats",
    "memory_stats",
    "cpu_stats",
    "networks",
    "blkio_stats",
    "precpu_stats",
]
INTERVAL = 60
PID_FILE_NAME = "pid.pid"
MINIMUM_DOCKER_VERSION = (2, 0, 0)
    
def flatten_dict(obj, prefix=""):
    sep = ":"
    result = {}
    for key in obj:
        if isinstance(obj[key], dict):
            result.update(flatten_dict(obj[key], prefix+sep+key))
        elif isinstance(obj[key], list):
            result[prefix+sep+key] = "\"{}\"".format(obj[key])
        else:
            result[prefix+sep+key] = obj[key]
    for key in result:
        if key[:len(sep)] == sep:
            result[key[len(sep):]] = result.pop(key)
    return result

def myhash(keys):
    return md5(",".join(list(keys)).encode("utf-8")).hexdigest()

class Monitor(object):
    def __init__(self, interval=INTERVAL):
        self.interval = interval

        self.c = {}
        self.read_config(".env")
        self.read_config(".env.local")

        # Use v1 API as it appears to be the version installed along with Docker
        # Engine with yum
        assert docker.version_info >= MINIMUM_DOCKER_VERSION
        self.client = docker.from_env(version="auto")

    def start(self):
        """
        Start monitoring, recording the pid of the monitoring process into the
        logging directory.
        """

        if not os.path.exists(RESOURCES_DIRNAME):
            os.makedirs(RESOURCES_DIRNAME)

        pid_path = os.path.join(RESOURCES_DIRNAME, PID_FILE_NAME)
        if not os.path.isfile(pid_path):
            with open(pid_path, "w") as f:
                f.write("{}\n".format(os.getpid()))
        else:
            print("Pid file exists. Try running stop first.", file=sys.stderr)

        self.run()

    def stop(self):
        """
        Stop another process that is monitoring. 
        """
        pid_path = os.path.join(RESOURCES_DIRNAME, PID_FILE_NAME)
        if os.path.exists(pid_path):
            with open(os.path.join(RESOURCES_DIRNAME, PID_FILE_NAME), "r") as f:
                pid = f.readline().strip()

            try:
                pid = int(pid)
                os.kill(pid, signal.SIGTERM)
            except ValueError:
                print("Could not parse pid '{}'".format(pid))

    def read_config(self, filename):
        """
        Read config file into `self.c`. Variables in config file are formatted
        as `KEY=VALUE`.
        """
        with open(filename, "r") as f:
            for line in f:
                key, val = line.strip().split("=")
                self.c[key] = val

    def get_matching_containers(self):
        """
        Return the ids of containers that are descended from the FeatureHub 
        user image, or match the name of the JupyterHub or MySQL container, as
        set in the config variables.
        """
        ids = []
        for container in \
            self.client.containers.list(filters={"ancestor": self.c["FF_IMAGE_NAME"]}) + \
            self.client.containers.list(filters={"name": self.c["HUB_CONTAINER_NAME"]}) + \
            self.client.containers.list(filters={"name": self.c["MYSQL_CONTAINER_NAME"]}):
            ids.append(container.id)

        return ids

    def run(self):

        if os.path.exists(RESOURCES_DIRNAME) and \
            os.path.isdir(RESOURCES_DIRNAME):
            files = os.listdir(RESOURCES_DIRNAME)
            if files and (len(files) > 1 or PID_FILE_NAME not in files):
                print("Refusing to overwrite existing logs in {}.".format(
                    RESOURCES_DIRNAME))
                print("Either delete files or rename existing log directory.")
                sys.exit(1)

        is_first_write = True
        while True:
            matching_containers = self.get_matching_containers()
            for id_ in matching_containers:
                all_stats = self.client.containers.get(id_).stats(decode=True, stream=False) 
                read_time = all_stats.pop("read")

                for stat in all_stats:
                    # bare minimum check on stat types
                    if stat not in STATS_TYPES:
                        with open(os.path.join(RESOURCES_DIRNAME, "log.txt"),
                            "a") as f:
                            f.write("Unexpected stat: {}\n".format(stat))
                        continue

                    # normal processing
                    this_stat = OrderedDict(flatten_dict(all_stats[stat]))
                    this_stat_items = [a[1] for a in this_stat.items()]
                    with open(os.path.join(RESOURCES_DIRNAME, stat +
                        ".csv"), "a") as f:
                        if is_first_write:
                            f.write(",".join(str(v) for v in \
                                ["id,read_time"] + list(this_stat.keys()) + \
                                ["keys_hash"]))
                            f.write("\n")

                        this_stat_keys_hash = myhash(this_stat.keys())
                        f.write(",".join(str(v) for v in \
                            [id_,read_time] + this_stat_items + \
                            [this_stat_keys_hash]))
                        f.write("\n")

                is_first_write = False

            sleep(self.interval)

def start():
    monitor = Monitor()
    monitor.start()

def stop():
    monitor = Monitor()
    monitor.stop()

def delete():
    for f in os.listdir(RESOURCES_DIRNAME):
        fa = os.path.join(RESOURCES_DIRNAME, f)
        print("Removing {}...".format(fa))
        os.remove(fa)

if __name__ == "__main__":
    if sys.argv[1] == "start":
        start()
    elif sys.argv[1] == "stop":
        stop()
    elif sys.argv[1] == "delete":
        delete()
    else:
        print("Unrecognized option: {}".format(sys.argv[1]), file=sys.stderr)
        sys.exit(1)
