import os
import textwrap
from pydiscourse import DiscourseClient


def post_feature(feature, metrics):
    client = DiscourseClient(
            host="https://{}".format(os.environ.get("DISCOURSE_DOMAIN_NAME")),
            api_username=os.environ.get("DISCOURSE_CLIENT_API_USERNAME"),
            api_key=os.environ.get("DISCOURSE_CLIENT_API_TOKEN"))

    params = [
        feature.problem.name,
        feature.description,
        feature.code,
        metrics,
        feature.user.name,
    ]
    content = _render_feature_post_template(*params)

    client.create_post(
            category=os.environ.get("DISCOURSE_FEATURE_CATEGORY_NAME"),
            title="[New Feature] {}".format(feature.description),
            content=content)

_template = \
"""
## A new feature was submitted!

* _Problem name_: {problem_name}
* _Feature description_: {feature_description}
* _Feature code_:

{feature_code}
* _Feature metrics_:
{feature_metrics}

What do you think? What do you like about this feature? How could it be improved? Leave your comments below, or get to work with your ideas!

----------

(submitted by user {user_name})
"""

def _render_feature_post_template(problem_name, feature_description,
        code, metrics, user_name):

    # format a couple objects
    indent = "    "
    bullet = " * "
    feature_code = textwrap.indent(code, indent)

    tmp = []
    for metric in metrics:
        d = metric.convert(kind="db")
        tmp.append(bullet + "{}: {}".format(d["name"], d["value"]))
    feature_metrics = "\n".join(tmp)

    user_name = escape_user_name(user_name)

    # render template
    return _template.format(problem_name=problem_name,
            feature_description=feature_description,
            feature_code=feature_code,
            feature_metrics=feature_metrics,
            user_name=user_name)

def escape_user_name(name):
    return name.replace("_", "&lowbar;")
