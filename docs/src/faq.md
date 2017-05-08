# FAQ

## How do I restart my Feature Factory server?

You may want or be asked to restart your notebook server, possibly in order to access
software udpates. If you follow these instructions, you will be able to do this without
loss of any data or work.

1. *Save all of your notebooks.* Your notebooks should autosave on any changes, but you can
   save them manually to be sure. Press *File -> Save and Checkpoint*.
2. *Stop your server.* Press the *Control Panel* icon at the top right. Press *Stop Server*.
   After a few moments, your server should stop and the button should disappear.
3. *Start your server.* You can now press *My Server* to restart your server.

```eval_rst
.. note::

   Restarting your Feature Factory server is different than restarting the IPython kernel.
```

## Why is my feature rejected by the submit function?

You may try to submit a feature only to receive a message that it was invalid and was
rejected. This can happen if any of the requirements Feature Factory imposes on your feature
are not met. Try evaluating your feature locally to see more detailed debugging information.

If your feature evaluates successfully locally but still is rejected by the server, make
sure that you do all of your imports within the function body and do not use global
variables.

If you are still having problems, contact an administrator or post for help in the forum (if
available).

## How can I see every column of a wide DataFrame?

By default, Jupyter Notebook shows columns at the beginning and end of the list of
columns when displaying a DataFrame. To force more columns to be displayed, try this:

```python
import pandas as pd
pd.set_option("display.max_columns", 500)
```
