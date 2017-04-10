import sys
#from multiprocessing import Pool
from pathos.multiprocessing import ProcessPool as Pool
import inspect
import hashlib
from textwrap import dedent

def run_isolated(f, *args):
    """Apply `f` to arguments in an isolated environment."""

    with Pool(1) as pool:
        # hack, as pool is somehow not open on further invocations
        pool.close()
        pool.restart()
        return pool.map(f, args)[0]

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

    # figure out which functions were defined
    names = list(namespace.keys())
    names.remove("__builtins__")
    if not names:
        raise ValueError("No function was defined in source.")
    names_copy = list(names)

    # Figure out which is the top-level function. The top-level function is
    # defined as the function that is not a name in any other functions.
    # co_names is a tuple of local names.
    # We could make more efficient, using constant lookups of names, stopping
    # when there is only name left, and confirming this name is not called by
    # anyone; but hard to anticipate a situation where user defines function
    # chain that is long enough that this efficiency is required.
    for name in list(names):
        locals_ = namespace[name].__code__.co_names
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

    return namespace[names[0]]

def compute_dataset_hash(dataset):
    """Return array of hash values of dataset contents (one per DataFrame)."""

    return [hashlib.md5(d.to_msgpack()).hexdigest() for d in dataset]
