import imp
import sys

from sqlalchemy.exc import ProgrammingError

from featurefactory.user.session import Session
from featurefactory.admin.admin import Commands

try:
    for problem in Commands().get_problems():
        # Create a session for each problem and make it importable
        commands = Session(problem)
        module = imp.new_module(problem)
        module.__dict__['commands'] = commands
        sys.modules['problems.' + problem] = module
except ProgrammingError:
    print("Competition not initialized properly. User commands "
          "unavailable. Please contact the competition administrator.",
          file=sys.stderr)

