from featurefactory.admin.admin import Commands
commands = Commands()
commands.set_up()

import os
demo_path = os.path.expanduser("~/problems/demo.yml")
commands.create_problem_yml(demo_path)

airbnb_path = os.path.expanduser("~/problems/airbnb.yml")
commands.create_problem_yml(airbnb_path)

sberbank_path = os.path.expanduser("~/problems/sberbank.yml")
commands.create_problem_yml(sberbank_path)

# more testing :)
commands.get_problems()
commands.get_features()
