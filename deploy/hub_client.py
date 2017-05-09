#!/usr/bin/env python3

import os
from jupyterhub_client import JupyterHubClient
import fire

from deploy_util import get_config

def _create_hub_client():
    c = get_config()

    hub_api_token = c["HUB_CLIENT_API_TOKEN"]
    hub_api_url = "http://{}:{}/hub/api".format(
        "127.0.0.1",
        c["HUB_API_PORT"]
    )
    return JupyterHubClient(token=hub_api_token, url=hub_api_url)

hub_client = _create_hub_client()

if __name__ == "__main__":
    fire.Fire(hub_client)
