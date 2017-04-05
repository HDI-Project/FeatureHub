# Hub Not available until jupyterhub release 0.8.0
# Source: https://github.com/jupyterhub/jupyterhub/blob/master/jupyterhub/services/auth.py

from jupyterhub.utils import url_path_join
from jupyterhub.services.auth import _ExpiringDict, HubAuth as HubAuthStable
from urllib.parse import quote
import requests
import socket
from tornado.log import app_log
from tornado.web import HTTPError
from traitlets import Integer, Instance, default

class HubAuth(HubAuthStable):

    cache_max_age = Integer(300,
        help="""The maximum time (in seconds) to cache the Hub's responses for authentication.

        A larger value reduces load on the Hub and occasional response lag.
        A smaller value reduces propagation time of changes on the Hub (rare).

        Default: 300 (five minutes)
        """
    ).tag(config=True)
    cache = Instance(_ExpiringDict, allow_none=False)
    @default('cache')
    def _default_cache(self):
        return _ExpiringDict(self.cache_max_age)

    def user_for_token(self, token, use_cache=True):
        """Ask the Hub to identify the user for a given token.
        Args:
            token (str): the token
            use_cache (bool): Specify use_cache=False to skip cached cookie values (default: True)
        Returns:
            user_model (dict): The user model, if a user is identified, None if authentication fails.
            The 'name' field contains the user's name.
        """
        return self._check_hub_authorization(
            url=url_path_join(self.api_url,
                "authorizations/token",
                quote(token, safe='')),
            cache_key='token:%s' % token,
            use_cache=use_cache,
        )

    def _check_hub_authorization(self, url, cache_key=None, use_cache=True):
        """Identify a user with the Hub
        
        Args:
            url (str): The API URL to check the Hub for authorization
                       (e.g. http://127.0.0.1:8081/hub/api/authorizations/token/abc-def)
            cache_key (str): The key for checking the cache
            use_cache (bool): Specify use_cache=False to skip cached cookie values (default: True)

        Returns:
            user_model (dict): The user model, if a user is identified, None if authentication fails.

        Raises an HTTPError if the request failed for a reason other than no such user.
        """
        if use_cache:
            if cache_key is None:
                raise ValueError("cache_key is required when using cache")
            # check for a cached reply, so we don't check with the Hub if we don't have to
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        try:
            r = requests.get(url,
                headers = {
                    'Authorization' : 'token %s' % self.api_token,
                },
            )
        except requests.ConnectionError:
            msg = "Failed to connect to Hub API at %r." % self.api_url
            msg += "  Is the Hub accessible at this URL (from host: %s)?" % socket.gethostname()
            if '127.0.0.1' in self.api_url:
                msg += "  Make sure to set c.JupyterHub.hub_ip to an IP accessible to" + \
                       " single-user servers if the servers are not on the same host as the Hub."
            raise HTTPError(500, msg)

        data = None
        if r.status_code == 404:
            app_log.warning("No Hub user identified for request")
        elif r.status_code == 403:
            app_log.error("I don't have permission to check authorization with JupyterHub, my auth token may have expired: [%i] %s", r.status_code, r.reason)
            raise HTTPError(500, "Permission failure checking authorization, I may need a new token")
        elif r.status_code >= 500:
            app_log.error("Upstream failure verifying auth token: [%i] %s", r.status_code, r.reason)
            raise HTTPError(502, "Failed to check authorization (upstream problem)")
        elif r.status_code >= 400:
            app_log.warning("Failed to check authorization: [%i] %s", r.status_code, r.reason)
            raise HTTPError(500, "Failed to check authorization")
        else:
            data = r.json()
            app_log.debug("Received request from Hub user %s", data)

        if use_cache:
            # cache result
            self.cache[cache_key] = data
        return data
