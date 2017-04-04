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

# feature factory imports
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from featurefactory.evaluation.response import EvaluationResponse
from featurefactory.admin.sqlalchemy_main import ORMManager
from featurefactory.admin.sqlalchemy_declarative import Feature, Problem, User
from featurefactory.util import get_function
import hashlib

# setup
prefix = "/services/eval-server"
hub_api_token = os.environ["EVAL_API_TOKEN"]
hub_api_url = "http://{}:{}/hub/api".format(
    os.environ["HUB_CONTAINER_NAME"],
    os.environ["HUB_API_PORT"]
)
auth = HubAuth(
    api_token            = hub_api_token,
    api_url              = hub_api_url,
    cookie_cache_max_age = 60,
)
log_filename = os.path.join(os.environ["FF_DATA_DIR"], "log", "eval-server",
        "log.log")
if not os.path.exists(os.path.dirname(log_filename)):
    os.makedirs(os.path.dirname(log_filename))

# app
app = Flask("eval-server")

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
    # required inputs include
    # - the database
    # - the problem id, for lookup in database
    # - the feature code
    # - the user-provided feature description
    database    = request.form["database"]
    problem_id  = request.form["problem_id"]
    code        = request.form["code"]
    description = request.form["description"]

    # preprocessing
    # - look up the problem in the databasse
    # - look up the user in the database
    # - compute the md5 hash of the feature code
    # - convert the feature code into a function
    orm = ORMManager(database, admin=True)
    try:
        problem_obj = orm.session.query(Problem).filter(Problem.id == problem_id).one()
    except (NoResultFound, MultipleResultsFound) as e:
        app.logger.exception(
            "Couldn't access problem (id {}) from db".format(problem_id))
        return EvaluationResponse(
            status_code = EvaluationResponse.STATUS_CODE_BAD_REQUEST
        )

    user_name = user["name"]
    try:
        user_obj = orm.session.query(User).filter(User.name == user_name).one()
    except (NoResultFound, MultipleResultsFound) as e:
        app.logger.exception(
            "Couldn't access user (name {}) from db".format(user_name))
        return EvaluationResponse(
            status_code = EvaluationResponse.STATUS_CODE_BAD_REQUEST
        )

    md5 = hashlib.md5(code).hexdigest()
    feature = get_function(code)

    # processing
    # - compute the CV score
    # - compute any other metrics
    score_cv = -1.0

    # write to db
    # TODO error handling
    feature_obj = Feature(
        description = description,
        score       = score_cv,
        code        = code,
        md5         = md5,
        user        = user_obj,
        problem     = problem_obj
    )
    orm.session.add(feature_obj)
    orm.session.commit()

    # return
    # - status code
    # - metrics dict
    status_code = EvaluationResponse.STATUS_CODE_OKAY
    metrics = {"score_cv" : score_cv}

    return EvaluationResponse(status_code, metrics)

@app.route(prefix + '/')
@authenticated
def whoami(user):
    return Response(
        json.dumps(user, indent=1, sort_keys=True),
        mimetype='application/json',
        )

if __name__ == "__main__":
    handler = RotatingFileHandler(log_filename, maxBytes=1024 * 1024 * 5,
            backupCount=5)
    formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} "
                                  "%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)

    host  = "0.0.0.0"
    port  = int(os.environ.get("EVAL_CONTAINER_PORT", 5000))
    debug = bool(os.environ.get("EVAL_FLASK_DEBUG", False))
    app.run(
        host  = host,
        port  = port,
        debug = debug
    )
