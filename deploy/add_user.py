#!/usr/bin/env python3

import os
from os.path import join as pjoin
import shutil
import subprocess
import binascii
import docker
import pydiscourse
import fire

from api_client import ApiClient

MINIMUM_DOCKER_VERSION = (0,0,0)
c = None
docker_client = None
discourse_client = None

def load_config():
    # load config vars

    def _read_config(filename):
        c = {}
        with open(filename, "r") as f:
            for line in f:
                key, val = line.split("=")
                key = key.strip()
                val = val.strip()
                c[key] = val
        return c

    c = {}
    script_dir = os.path.dirname(__file__)
    c.update(_read_config(os.path.join(script_dir,".env")))
    c.update(_read_config(os.path.join(script_dir,".env.local")))

    return c


def add_user(username, password, admin=False, discourse=False, email=""):
    # create user on hub machine
    subprocess.call(\
"""
docker exec -i {0} bash <<EOM
if id {1} >/dev/null 2>&1; then
    userdel {1}
fi
useradd -m -U {1}
echo {1}:{2} | /usr/sbin/chpasswd
EOM
""".format(c["HUB_CONTAINER_NAME"],username,password), shell=True)

    os.makedirs(pjoin(c["FF_DATA_DIR"], "users", username), exist_ok=True)
    if admin:
        shutil.copytree(pjoin("..","notebooks","admin"),
                        pjoin(c["FF_DATA_DIR"], "users", username,
                            "notebooks", "admin"))
        shutil.copytree(pjoin(c["FF_DATA_DIR"], "problems"),
                        pjoin(c["FF_DATA_DIR"], "users", username))
    else:
        shutil.copytree(pjoin("..","notebooks"),
                        pjoin(c["FF_DATA_DIR"], "users", username, "notebooks"))
        shutil.rmtree(pjoin(c["FF_DATA_DIR"], "users", username, "notebooks",
            "admin"))

    subprocess.call("sudo chmod -R 777 {}/users/{}".format(c["FF_DATA_DIR"],
        username).split(" "))

    # Create user in database with correct permissions. Create .my.cnf file for
    # user. The password for mysql db is generated randomly and is not the same as the system user account password.
    password_mysql = binascii.b2a_hex(os.urandom(16)).decode("utf-8")
    if admin:
        cmd2 = "GRANT ALL ON *.* TO '{}'@'%' WITH GRANT OPTION;".format(username)
    else:
        cmd2 = "GRANT SELECT ON {}.* TO '{}'@'%';".format(c["MYSQL_DATABASE"],
                username)

    subprocess.call(\
"""
docker exec -i {0} mysql --user={1} --password={2} <<EOM
DROP USER IF EXISTS '{3}'@'%';
CREATE USER '{3}'@'%' IDENTIFIED BY '{4}';
{5}
EOM
""".format(c["MYSQL_CONTAINER_NAME"], c["MYSQL_ROOT_USERNAME"],
           c["MYSQL_ROOT_PASSWORD"], username, password_mysql, cmd2), shell=True)

    with open(pjoin(c["FF_DATA_DIR"], "users", username, ".my.cnf"), "w") as f:
        f.write(
            "[client]\n"
            "user={0}\n"
            "password={1}\n".format(username, password_mysql))


    client = ApiClient()
    client.hub.create_user(name=username, admin=admin)

if __name__ == "__main__":
    assert docker.version_info >= MINIMUM_DOCKER_VERSION
    docker_client = docker.from_env(version="auto")

    c = load_config()
    fire.Fire(add_user)
