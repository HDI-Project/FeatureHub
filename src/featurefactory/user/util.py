from multiprocessing import Pool
from threading import Event

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

    def __init__(self):
        self.description = ""
        self.event = Event()

    def before_prompt(self):
        """
        Preparing to issue the prompt by clearing the description flag.
        """
        self.event.clear() # flag is false
        self.description = ""

    def set_description(self, description):
        """
        Set the description and set the description flag.
        """
        self.description = description
        self.event.set() # flag is true, waiters notified
        print("[set_description] description set to {}".format(description))

    def get_description(self, timeout=None):
        """
        Wait for the description to be available, then return it.
        """
        if not timeout:
            timeout = self.TIMEOUT

        # wait returns True *unless* it times out.
        not_timed_out = self.event.wait(timeout=timeout) # wake

        if not not_timed_out:
            print("Timed out waiting for set_description event.")

        return self.description
