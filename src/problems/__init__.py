import imp
import sys

sys.path.insert(1, '..')

from factory import Session

# >>> import imp
# >>> foo = imp.new_module("foo")
# >>> foo_code = """
# ... class Foo:
# ...     pass
# ... """
# >>> exec foo_code in foo.__dict__
# >>> foo.Foo.__module__
# 'foo'
# >>>

def get_problem_names():
    # Imported here to avoid having it visible at Module level
    from orm.admin import Commands
    admin_commands = Commands()
    return admin_commands.get_problems()


for problem in get_problem_names():
    # Crete a session for each problem and make it importable
    commands = Session(problem)
    module = imp.new_module(problem)
    module.__dict__['commands'] = commands
    sys.modules['problems.' + problem] = module
