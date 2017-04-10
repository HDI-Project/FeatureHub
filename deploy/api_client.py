#!/usr/bin/env python3

import os
from jupyterhub_client import JupyterHubClient
import fire

class ApiClient(object):
    def __init__(self):
        self.load_config()

        hub_api_token = self.c["API_CLIENT_API_TOKEN"]
        hub_api_url = "http://{}:{}/hub/api".format(
            "127.0.0.1",
            self.c["HUB_API_PORT"]
        )
        self.hub = JupyterHubClient(token=hub_api_token, url=hub_api_url)

    def load_config(self):
        # load config vars
        self.c = {}
        script_dir = os.path.dirname(__file__)
        self.c.update(self._read_config(os.path.join(script_dir,".env")))
        self.c.update(self._read_config(os.path.join(script_dir,".env.local")))

    @staticmethod
    def _read_config(filename):
        """
        Read config file into `c`. Variables in config file are formatted
        as `KEY=VALUE`.
        """

        c = {}
        with open(filename, "r") as f:
            for line in f:
                key, val = line.split("=")
                key = key.strip()
                val = val.strip()
                c[key] = val
        return c

if __name__ == "__main__":
    client = ApiClient()
    fire.Fire(client.hub)
