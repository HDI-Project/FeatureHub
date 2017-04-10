# Add docker to the jupyterhub/jupyterhub image.

# Adapted from jupyterhub/jupyterhub-deploy-docker
FROM jupyterhub/jupyterhub:0.7.2

# Install docker on the jupyterhub container
RUN wget https://get.docker.com -q -O /tmp/getdocker && \
    chmod +=x /tmp/getdocker && \
    sh /tmp/getdocker
