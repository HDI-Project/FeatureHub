from multiprocessing import Pool

def run_isolated(f, *args):

    """Apply `f` to arguments in an isolated environment."""
    pool = Pool(processes=1)
    try:
        result = pool.map(f, args)[0]
    finally:
        pool.close()

    return result
