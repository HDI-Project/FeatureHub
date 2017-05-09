#!/usr/bin/env python3

import os
from os.path import join as pjoin
import sys
import shutil
import subprocess
import binascii
import docker
from pydiscourse.exceptions import DiscourseClientError
import fire

from hub_client import hub_client
from discourse_client import discourse_client
from deploy_util import get_config

MINIMUM_DOCKER_VERSION = (0,0,0)
DISCOURSE_MIN_PASSWORD_LENGTH = 10

c = get_config()

docker_client    = None

def add_user(username, password, admin=False, discourse=False, email=""):
    if discourse:
        if len(password) < DISCOURSE_MIN_PASSWORD_LENGTH:
            raise ValueError("Password too short (minimum {})."
                    .format(DISCOURSE_MIN_PASSWORD_LENGTH))

        if not email:
            email = username + "@example.com"
            has_email = False
        else:
            has_email = True

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
        shutil.copytree(pjoin(c["FF_DATA_DIR"],"notebooks","admin"),
                        pjoin(c["FF_DATA_DIR"], "users", username,
                            "notebooks", "admin"))
        shutil.copytree(pjoin(c["FF_DATA_DIR"], "problems"),
                        pjoin(c["FF_DATA_DIR"], "users", username,
                            "problems"))
    else:
        shutil.copytree(pjoin(c["FF_DATA_DIR"],"notebooks"),
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

    hub_client.create_user(name=username, admin=admin)

    if discourse:
        user = discourse_client.create_user(
            name = "",
            username = username,
            email = email,
            password = password,
            active = "true")

        userid=user["user_id"]
        if not has_email:
            try:
                discourse_client._put("/admin/users/{0}/activate".format(userid))
            except DiscourseClientError:
                print("Failed to activate user {}".format(username),
                        file=sys.stderr)

        if c["DISCOURSE_FEATURE_GROUP_NAME"]:
            groups = discourse_client.groups()
            groupid = None
            for group in groups:
                if group["name"] == c["DISCOURSE_FEATURE_GROUP_NAME"]:
                    groupid = group["id"]
                    break

            if groupid is not None:
                result = discourse_client.add_group_member(
                    username = username,
                    groupid = groupid)
            else:
                print("Couldn't add to group (name not found).")

def delete_user(username, discourse=False):

    subprocess.call(\
"""
docker exec -i {hub_container_name} \
    userdel -f {username}
""".format(hub_container_name=c["HUB_CONTAINER_NAME"], username=username),
        shell=True)

    hub_client.delete_user(username)

    subprocess.call(
        "sudo rm -rf {ff_data_dir}/users/{username}".format(
            ff_data_dir=c["FF_DATA_DIR"], username=username),
        shell=True)


    subprocess.call(\
"""
docker exec -i {mysql_container_name} \
    mysql \
        --user={mysql_root_username} \
        --password={mysql_root_password} <<EOF
DROP USER IF EXISTS '{username}'@'%';
EOF
""".format(mysql_container_name=c["MYSQL_CONTAINER_NAME"],
           mysql_root_username=c["MYSQL_ROOT_USERNAME"],
           mysql_root_password=c["MYSQL_ROOT_PASSWORD"],
           username=username),
        shell=True)

    if discourse:
        user = discourse_client.user(username)
        userid = user["id"]
        discourse_client.delete_user(userid)

if __name__ == "__main__":
    assert docker.version_info >= MINIMUM_DOCKER_VERSION
    docker_client = docker.from_env(version="auto")

    fire.Fire({
        "add": add_user,
        "delete": delete_user,
    })
