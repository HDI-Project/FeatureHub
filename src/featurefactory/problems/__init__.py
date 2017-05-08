import imp
import sys

from sqlalchemy.exc import ProgrammingError

from featurefactory.user.session import Session
from featurefactory.admin.admin import Commands

try:
    for _problem in Commands().get_problems():
        # Create a session for each problem and make it importable
        _commands = Session(_problem)
        _module = imp.new_module(_problem)
        _module.__dict__['commands'] = _commands
        sys.modules['featurefactory.problems.' + _problem] = _module
except ProgrammingError:
    print("Competition not initialized properly. User commands "
          "unavailable. Please contact the competition administrator.",
          file=sys.stderr)
