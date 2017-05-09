import os

def get_config():
    # load config vars
    c = {}
    script_dir = os.path.dirname(__file__)
    c.update(_read_config(os.path.join(script_dir,".env")))
    c.update(_read_config(os.path.join(script_dir,".env.local")))

    return c

def _read_config(filename):
    """
    Read config file into `c`. Variables in config file are formatted
    as `KEY=VALUE`.
    """

    c = {}
    with open(filename, "r") as f:
        for line in f:
            key, val = line.split("=")
            key = key.strip()
            val = val.strip()
            c[key] = val
    return c
