# Configuration file for jupyterhub.

## Standard, system-independent Feature Factory config options.
# The public facing port of the proxy
c.JupyterHub.port = 443
# The class to use for spawning single-user servers.
c.JupyterHub.spawner_class = 'dockerspawner.SystemUserSpawner'
# Path to the notebook directory for the single-user server.
c.Spawner.notebook_dir = '~/notebooks'
#  If empty, does not perform any additional restriction.
# c.Authenticator.whitelist = {''}
# Remove and recreate container if necessary.
c.DockerSpawner.remove_containers = True

# Networking
c.JupyterHub.hub_ip = 'featurefactoryhub' #$HUB_IP
c.JupyterHub.hub_port = 8080 #$HUB_PORT
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = 'featurefactory-network' #$NETWORK_NAME
c.DockerSpawner.extra_host_config = { 
    'network_mode': 'featurefactory-network', # '$NETWORK_NAME' }
}

c.JupyterHub.ssl_key = '/var/lib/featurefactory/config/jupyterhub/key.pem' #'$JUPYTERHUB_CONFIG_DIR/$KEY_NAME'
c.JupyterHub.ssl_cert = '/var/lib/featurefactory/config/jupyterhub/cert.pem' #'$JUPYTERHUB_CONFIG_DIR/$CERT_NAME'
c.DockerSpawner.read_only_volumes = {
    #'$JUPYTERHUB_CONFIG_DIR/featurefactory':'/etc/featurefactory',
    '/var/lib/featurefactory/config/featurefactory':'/etc/featurefactory',
    #'$FF_DATA_DIR/data':'/data',
    '/var/lib/featurefactory/data':'/data',
}
c.SystemUserSpawner.host_homedir_format_string = '/var/lib/featurefactory/users/{username}' #'$FF_DATA_DIR/users/{username}'
c.SystemUserSpawner.container_image = 'featurefactoryuser' # "$FF_IMAGE_NAME"
