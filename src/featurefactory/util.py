import sys
import os
import dill
from multiprocessing import Pool
import inspect
from textwrap import dedent
import xxhash
import tempfile
import importlib.util
from types import ModuleType

def _get_function_and_execute(source, *args):
    f = get_function(source)
    return f(*args)

def run_isolated(f, *args):
    """
    Execute `f(args)` in an isolated environment.
    
    First, uses dill to serialize the function. Unfortunately, pickle is unable
    to serialize some functions, so we must serialize and deserialize the
    function ourselves.
    """
    source = get_source(f)
    with Pool(1) as pool:
        return pool.apply(_get_function_and_execute, (source, *args))

def _get_function_and_execute2(f_dill, *args):
    f = dill.loads(f_dill)
    return f(*args)

def run_isolated2(f, *args):
    f_dill = dill.dumps(f)
    with Pool(1) as pool:
        return pool.apply(_get_function_and_execute2, (f_dill, *args))

def get_source(function):
    """
    Extract the source code from a given function.

    Recursively extracts the source code for all local functions called by given
    function. The resulting source code is encoded in utf-8.

    Limitations: Cannot use `get_source` on function defined interactively in
    normal Python terminal. Functions defined interactively in IPython are still
    okay.
    """

    # Use nested function to allow us to ultimately encode as utf-8 string.
    def _get_source(function):
        out = []
        try:
            # Python 2
            # TODO __code__ and __globals__ should even work in Python 2
            func_code, func_globals = function.func_code, function.func_globals
        except AttributeError:
            # Python 3
            func_code, func_globals = function.__code__, function.__globals__

        # known limitation: cannot use from stdin
        if func_code.co_filename == '<stdin>':
            raise ValueError("Cannot use `get_source` on function defined interactively.")

        for name in func_code.co_names:
            obj = func_globals.get(name)
            if obj and inspect.isfunction(obj):
                out.append(_get_source(obj))

        out.append(inspect.getsource(function))

        seen = set()
        return "\n".join(x for x in out if not (x in seen or seen.add(x)))

    code = _get_source(function)

    # post-processing
    code = dedent(code)
    code = code.encode("utf-8")
    return code

def get_function(source):
    """
    Return a function from given source code that was extracted using `get_source`.

    Note that the source code produced by get_source includes the source for the
    top-level function as well as any other local functions it calls. Here, we
    return the top-level function directly.

    Args
    ----
        source : str, bytes
    """

    # decode into str
    if isinstance(source, bytes):
        code = source.decode("utf-8")
    elif isinstance(source, str):
        code = source
    else:
        raise ValueError

    # exec code in empty namespace
    try:
        namespace = {}
        exec(code, namespace)
    except (SyntaxError, IndentationError) as e:
        print(code)
        raise e

    # Get top-level function from list of functions
    name = get_top_level_function_name(namespace)
    return namespace[name]

def get_top_level_function_name(namespace, remove_names=["__builtins__"]):
    """
    Figure out which is the top-level function in a namespace.
    
    The top-level function is defined as the function that is not a name in any
    other functions.  co_names is a tuple of local names.  We could make more
    efficient, using constant lookups of names, stopping when there is only name
    left, and confirming this name is not called by anyone; but hard to
    anticipate a situation where user defines function chain that is long enough
    that this efficiency is required.
    """
    if isinstance(namespace, dict):
        names = list(namespace.keys())
        def get_name(name):
            return namespace[name]
    elif isinstance(namespace, ModuleType):
        names = dir(namespace)
        def get_name(name):
            return getattr(namespace, name)
    else:
        raise ValueError("Invalid argument")

    for name in remove_names:
        names.remove(name)
    if not names:
        raise ValueError("No function was defined in source.")
    names_copy = list(names)

    for name in list(names):
        locals_ = get_name(name).__code__.co_names
        for local in locals_:
            if local != name and local in names:
                names.remove(local)

    # at this point, the only name remaining in names should be top-level
    # function
    if len(names) != 1:
        print("Something went wrong.", file=sys.stderr)
        print("\tnames (original): {}".format(names_copy), file=sys.stderr)
        print("\tnames (modified): {}".format(names), file=sys.stderr)
        raise ValueError

    return names[0]

def get_function2(source):
    """
    Return a function from given source code that was extracted using
    `get_source`. This function differs from `get_function` in the method used
    is to write the source code to a file and then import that file as a new
    module.

    Note that the source code produced by get_source includes the source for the
    top-level function as well as any other local functions it calls. Here, we
    return the top-level function directly.

    Args
    ----
        source : str, bytes
    """

    # decode into str
    if isinstance(source, bytes):
        code = source.decode("utf-8")
    elif isinstance(source, str):
        code = source
    else:
        raise ValueError

    # first, write source to a file
    with tempfile.TemporaryDirectory() as d:
        module_name = "temp"
        file_name = os.path.join(d, module_name + ".py")
        with open(file_name, "w") as f:
            f.write(code)

        # next, import/exec that file
        spec = importlib.util.spec_from_file_location(module_name, file_name)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(dir(module))
        top_level_name = get_top_level_function_name(module,
                remove_names=["__builtins__", "__cached__", "__doc__",
                              "__file__", "__loader__", "__name__",
                              "__package__", "__spec__"])
        return getattr(module, top_level_name)

def compute_dataset_hash(dataset):
    """
    Return hash value of dataset contents.

    Args
    ----
        dataset : list of DataFrame
    """
    h = xxhash.xxh64()
    for d in dataset:
        h.update(d.to_msgpack())

    return h.intdigest()
