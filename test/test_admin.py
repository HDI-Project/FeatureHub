from featurefactory.admin.admin import Commands
commands = Commands()
commands.set_up(drop=True)

import os
demo_path = os.path.expanduser("~/problems/demo.yml")
commands.create_problem_yml(demo_path)

# more testing :)
commands.get_problems()
commands.get_features()
