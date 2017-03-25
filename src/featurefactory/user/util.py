from multiprocessing import Pool
from IPython.core.magics.display import Javascript

def run_isolated(f, *args):

    """Apply `f` to arguments in an isolated environment."""
    pool = Pool(processes=1)
    try:
        result = pool.map(f, args)[0]
    finally:
        pool.close()

    return result

class DescriptionStore:
    TIMEOUT = 5
    MAX_ATTEMPTS = 10

    def __init__(self):
        self.description = ""

    def set_description(self, description):
        self.description = description

    def get_description(self):
        attempts = 0
        while not self.description:
            time.sleep(self.TIMEOUT) 
            attempts += 1
            if attempts >= self.MAX_ATTEMPTS:
                return ""

        return self.description
