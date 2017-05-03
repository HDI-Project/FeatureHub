# Configuration file for jupyterhub.

import os
import jupyterhub

c = get_config()

# Setup some variables
network_name               = os.environ["DOCKER_NETWORK_NAME"]
ff_data_dir                = os.environ["FF_DATA_DIR"]
ff_image_name              = os.environ["FF_IMAGE_NAME"]
ff_container_name          = os.environ["FF_CONTAINER_NAME"]
hub_container_name         = os.environ["HUB_CONTAINER_NAME"]
hub_port                   = int(os.environ["HUB_API_PORT"])
mysql_container_name       = os.environ["MYSQL_CONTAINER_NAME"]

jupyterhub_config_dir      = os.path.join(ff_data_dir, "config", "jupyterhub")

logo_file             = os.path.join(ff_data_dir, "config", "jupyterhub", "featurefactory.png")
cull_idle_filename    = os.path.join(jupyterhub_config_dir, "cull_idle_servers.py")
if "FF_IDLE_SERVER_TIMEOUT" in os.environ:
    cull_idle_timeout = os.environ["FF_IDLE_SERVER_TIMEOUT"]
else:
    cull_idle_timeout = 3600

eval_container_name   = os.environ["EVAL_CONTAINER_NAME"]
eval_container_port   = os.environ["EVAL_CONTAINER_PORT"]
eval_server_url       = "http://{}:{}".format(eval_container_name,
    eval_container_port)
eval_server_api_token = os.environ["EVAL_API_TOKEN"]

api_client_api_token = os.environ["API_CLIENT_API_TOKEN"]

# General Hub config
c.JupyterHub.logo_file               = logo_file

# Spawned containers
c.JupyterHub.spawner_class          = "dockerspawner.SystemUserSpawner"
c.SystemUserSpawner.container_image = ff_image_name
c.DockerSpawner.container_prefix    = ff_container_name
c.DockerSpawner.remove_containers   = True
if jupyterhub.version_info[0:2] >= (0, 7):
    c.Spawner.mem_limit             = os.environ["FF_CONTAINER_MEMLIMIT"]

# Networking
c.JupyterHub.port                 = 443
c.JupyterHub.hub_ip               = hub_container_name
c.JupyterHub.hub_port             = hub_port
c.DockerSpawner.use_internal_ip   = True
c.DockerSpawner.network_name      = network_name
c.DockerSpawner.extra_host_config = {
    "network_mode" : network_name,
}
c.Spawner.environment             = {
    "HUB_CONTAINER_NAME"   : hub_container_name,
    "MYSQL_CONTAINER_NAME" : mysql_container_name,
    "EVAL_CONTAINER_NAME"  : eval_container_name,
    "EVAL_CONTAINER_PORT"  : eval_container_port,
}

# Security
c.JupyterHub.ssl_key = os.environ["SSL_KEY"]
c.JupyterHub.ssl_cert = os.environ["SSL_CERT"]
# c.Authenticator.whitelist = {""}

# Data/directories
c.JupyterHub.db_url                            = os.path.join("sqlite:///", jupyterhub_config_dir, "jupyterhub.sqlite")
c.JupyterHub.cookie_secret_file                = os.path.join(jupyterhub_config_dir, "jupyterhub_cookie_secret")
c.JupyterHub.extra_log_file                    = os.path.join(jupyterhub_config_dir, "jupyterhub.log")
c.Spawner.notebook_dir                         = "~/notebooks"
c.DockerSpawner.read_only_volumes              = { os.path.join(ff_data_dir, "data/train") : "/data/train" }
c.SystemUserSpawner.host_homedir_format_string = os.path.join(ff_data_dir, "users", "{username}")

# Services - definitions
c.JupyterHub.services = [
    {
        "name": "cull-idle",
        "admin": True,
        "command": ["python", cull_idle_filename,
                    "--timeout="+cull_idle_timeout,
                    "--cull_every=300"],
    },
    {
        "name": "eval-server",
        "url": eval_server_url,
        "api_token": eval_server_api_token,
    },
    {
        "name": "api-client",
        "admin": True,
        "url": "0.0.0.0",
        "api_token": api_client_api_token,
    }
]

# Whitelist users and admins
c.Authenticator.whitelist   = whitelist = set()
c.Authenticator.admin_users = admin = set()
c.JupyterHub.admin_access   = True

whitelist.add("root")
admin.add("root")

userlist_filename = os.path.join(jupyterhub_config_dir, "userlist")
if os.path.isfile(userlist_filename):
    with open(userlist_filename, "r") as f:
        for line in f:
            if not line:
                continue
            parts = line.split()
            name = parts[0]
            whitelist.add(name)
            if len(parts) > 1 and parts[1] == "admin":
                admin.add(name)
