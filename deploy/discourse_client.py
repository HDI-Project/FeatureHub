import os
import pydiscourse
import fire

from deploy_util import get_config

def _create_discourse_client():
    c = get_config()

    hub_api_token = c["HUB_CLIENT_API_TOKEN"]
    hub_api_url = "http://{}:{}/hub/api".format(
        "127.0.0.1",
        c["HUB_API_PORT"]
    )
    client = pydiscourse.DiscourseClient(
        host="https://{}".format(c["DISCOURSE_DOMAIN_NAME"]),
        api_username=c["DISCOURSE_CLIENT_API_USERNAME"],
        api_key=c["DISCOURSE_CLIENT_API_TOKEN"])

    return client

discourse_client = _create_discourse_client()

if __name__ == "__main__":
    fire.Fire(discourse_client)
