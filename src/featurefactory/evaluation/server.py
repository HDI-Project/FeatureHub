#!/usr/bin/env python3
"""
Evaluation server for Feature Factory user notebooks
"""

from functools import wraps
import json
import os
import sys
from urllib.parse import quote

from flask import Flask, redirect, request, Response

from jupyterhub.services.auth import HubAuth

# setup
prefix = "/services/eval-server"
hub_api_token = os.environ["EVAL_API_TOKEN"]
hub_api_url = "http://{}:{}/hub/api".format(
    os.environ["HUB_CONTAINER_NAME"],
    os.environ["HUB_API_PORT"]
)
print("token: " + hub_api_token, file=sys.stderr)
print("url: " + hub_api_url, file=sys.stderr)
auth = HubAuth(
    api_token            = hub_api_token,
    api_url              = hub_api_url,
    cookie_cache_max_age = 60,
)

# app
app = Flask(__name__)

def authenticated(f):
    """Decorator for authenticating with the Hub"""
    @wraps(f)
    def decorated(*args, **kwargs):
        cookie = request.cookies.get(auth.cookie_name)
        if cookie:
            user = auth.user_for_cookie(cookie)
        else:
            user = None
        if user:
            return f(user, *args, **kwargs)
        else:
            # redirect to login url on failed auth
            return redirect(auth.login_url + "?next=%s" % quote(request.path))
    return decorated

@app.route(prefix + "/evaluate", methods=["POST"])
@authenticated
def evaluate(user):
    # post elements
    code        = request.form["code"]
    description = request.form["description"]
    problem     = request.form["problem"]

    score = -1.0
    return Response(
        json.dumps(score, indent=1, sort_keys=True),
        mimetype="application/json",
        )

@app.route(prefix + '/')
@authenticated
def whoami(user):
    return Response(
        json.dumps(user, indent=1, sort_keys=True),
        mimetype='application/json',
        )

if __name__ == "__main__":
    host  = "0.0.0.0"
    port  = int(os.environ.get("EVAL_CONTAINER_PORT", 5000))
    debug = bool(os.environ.get("EVAL_FLASK_DEBUG", False))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    )
