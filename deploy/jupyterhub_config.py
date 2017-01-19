# Configuration file for jupyterhub.

## Standard, system-independent Feature Factory config options.
# The public facing port of the proxy
c.JupyterHub.port = 443
# The class to use for spawning single-user servers.
c.JupyterHub.spawner_class = 'dockerspawner.SystemUserSpawner'
# Path to the notebook directory for the single-user server.
c.Spawner.notebook_dir = '~/FeatureFactory'
#  If empty, does not perform any additional restriction.
c.Authenticator.whitelist = {''}

