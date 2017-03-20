import imp
import sys

from featurefactory.user.session import Session
from featurefactory.admin.admin import Commands


for problem in Commands().get_problems():
    # Crete a session for each problem and make it importable
    commands = Session(problem)
    module = imp.new_module(problem)
    module.__dict__['commands'] = commands
    sys.modules['problems.' + problem] = module
