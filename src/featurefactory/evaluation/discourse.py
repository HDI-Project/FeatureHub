import os
import textwrap
from pydiscourse import DiscourseClient
from pydiscourse.exceptions import DiscourseClientError

class DiscourseFeatureTopicTemplate(object):
    indent = "    "
    bullet = " * "

    def __init__(self):
        self.title = "[New Feature] {title}"
        self.header = "## A new feature was submitted!\n\n"
        self.problem_name = "* _Problem name_: {problem_name}\n"
        self.feature_description = "* _Feature description_: {feature_description}\n"
        self.feature_code = "* _Feature code_:\n\n{feature_code}\n\n"
        self.feature_metrics = "* _Feature metrics_:\n{feature_metrics}\n\n"
        self.prompt = ("What do you think? What do you like about this "
                       "feature? How could it be improved? Leave your "
                       "comments below, or get to work with your ideas!\n\n")
        self.author = ("----------\n\n"
                      "(submitted by user <em>{user_name}</em>)\n")

    def render(self, problem_name, feature_description, feature_code,
            feature_metrics, user_name):
        result = ""

        result += self.header
        result += self.problem_name.format(
                problem_name=problem_name)
        result += self.feature_description.format(
                feature_description=feature_description)
        result += self.feature_code.format(
                feature_code=feature_code)
        result += self.prompt
        result += self.author.format(
                user_name=user_name)

        return result

    def render_title(self, title):
        return self.title.format(title=title)

class DiscourseFeatureTopic(object):

    def __init__(self, feature, metrics):
        self.feature = feature
        self.metrics = metrics

        client = DiscourseClient(
                host="https://{}".format(os.environ.get("DISCOURSE_DOMAIN_NAME")),
                api_username=os.environ.get("DISCOURSE_CLIENT_API_USERNAME"),
                api_key=os.environ.get("DISCOURSE_CLIENT_API_TOKEN"))
        self.client = client


    def format_code(self):
        code = self.feature.code
        indent = DiscourseFeatureTopicTemplate.indent
        tmp = []
        tmp.append(indent + "```")
        for line in code.split("\n"):
            tmp.append(indent + line)
        tmp.append(indent + "```")
        feature_code = "\n".join(tmp)
        return feature_code

    def format_metrics(self):
        metrics = self.metrics
        bullet = DiscourseFeatureTopicTemplate.bullet
        tmp = []
        for metric in metrics:
            d = metric.convert(kind="db")
            tmp.append(bullet + "{}: {}".format(d["name"], d["value"]))
        feature_metrics = "\n".join(tmp)
        return feature_metrics

    def get_params(self):
        params = [
            self.feature.problem.name,
            self.feature.description,
            self.format_code(),
            self.format_metrics(),
            feature.user.name,
        ]
        return params

    def _escape_user_name(name):
        """Replace `_` in name with `&lowbar;`."""
        return name.replace("_", "&lowbar;")

    def post_feature(self):
        params = self.get_params()
        content = DiscourseFeatureTopicTemplate().render(*params)
        try:
            post = client.create_post(
                    category=os.environ.get("DISCOURSE_FEATURE_CATEGORY_NAME"),
                    title=format(feature.description),
                    content=content)

            # return the url of the new post
            url = "https://{}/t/{}".format(
                    os.environ.get("DISCOURSE_DOMAIN_NAME"),
                    post["topic_slug"])
        except Exception as err:
            # TODO
            url = ""
            raise err

        return url

def _render_feature_post_template(problem_name, feature_description,
        code, metrics, user_name):



    # user_name = _escape_user_name(user_name)

    # render template
    return _template.format(problem_name=problem_name,
            feature_description=feature_description,
            feature_code=feature_code,
            feature_metrics=feature_metrics,
            user_name=user_name)
