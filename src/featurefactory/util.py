from multiprocessing import Pool
import inspect
import hashlib

def run_isolated(f, *args):

    """Apply `f` to arguments in an isolated environment."""
    pool = Pool(processes=1)
    try:
        result = pool.map(f, args)[0]
    finally:
        pool.close()

    return result

def get_source(function):
    """
    Extract the source code from a given function.
    """

    # Use nested function to allow us to ultimately encode as utf-8 string.
    def _get_source(function):
        out = []
        try:
            # Python 2
            func_code, func_globals = function.func_code, function.func_globals
        except AttributeError:
            # Python 3
            func_code, func_globals = function.__code__, function.__globals__

        for name in func_code.co_names:
            obj = func_globals.get(name)
            if obj and inspect.isfunction(obj):
                out.append(_get_source(obj))

        out.append(inspect.getsource(function))

        seen = set()
        return "\n".join(x for x in out if not (x in seen or seen.add(x)))

    code = _get_source(function)
    return code.encode("utf-8")

def compute_dataset_hash(dataset):
    """Return array of hash values of dataset contents (one per DataFrame)."""
    return [hashlib.md5(d.to_msgpack()).hexdigest() for d in dataset]
