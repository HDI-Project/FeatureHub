# test of Tutorial

# coding: utf-8

# # Feature Factory Tutorial
# 
# In this tutorial, we will go through the functionality offered by the Feature Factory library.

# ## Prepare your session
# 
# We import `commands`, the Feature Factory client, into our workspace. We'll use this client to acquire data, evaluate our features, and register them with the Feature database.

# In[ ]:

from featurefactory.problems.demo import commands


# ## Acquire dataset
# 
# We use `get_sample_dataset()` to load the training data into our workspace. The result is a tuple where the first element is `dataset`, a dictionary mapping table names to Pandas `DataFrame`s, and the second element is `target`, a Pandas `DataFrame` with one column. This one column is what we are trying to predict.

# In[ ]:

dataset, target = commands.get_sample_dataset()


# We can explore our data inline in the Notebook.

# In[ ]:

dataset.keys()


# In[ ]:

dataset["users"].head()


# In[ ]:

dataset["groups"].head()


# In[ ]:

target.head()


# ## Explore existing features
# 
# We can use several methods to see what features have already been registered to the Feature database.
# 
# The first method, `print_my_features`, prints the features that you have registered to the database.

# In[ ]:

commands.print_my_features()


# We can also pass additional parameters to `print_my_features` to filter by code fragments or to see a certain type of metric, if available.

# In[ ]:

commands.print_my_features(code_fragment="""dataset["faculty"]["name"]""", metric_name="Accuracy")


# To see detailed documentation, try using Jupyter Notebook's built-in documentation system by appending a `?` to the end of a method name.

# In[ ]:

get_ipython().magic('pinfo commands.print_my_features')


# The second method, `discover_features`, prints features that other participants have registered to the Feature database. This allows you to discover code that has already been written, so you can either avoid duplicating work or come up with new ideas.

# In[ ]:

commands.discover_features()


# The same additional parameters, `code_fragment` and `metric_name`, are available.

# In[ ]:

commands.discover_features(code_fragment="""fillna(""")


# ## Write a new feature
# 
# Feature Factory asks you to observe some rudimentary scaffolding when you write a new feature.
# 
# Your feature is a function that should
# 
# <ul style="list-style: none;">
# <li>✓ accept a single parameter, `dataset` </li>
# <li>✓ return a *single column* of values
#     <ul>
#         <li> that has as many rows as there are examples in the dataset </li>
#         <li> that can be coerced to a `DataFrame` </li>
#     </ul>
# </li>
# <li> ✓ be defined in the global scope </li>
# <li> ✓ import all required modules that it requires within the function body </li>
# </ul>
#     
# Your feature should *not*
# <ul style="list-style: none;">
# <li> ✗ modify the underlying dataset </li>
# <li> ✗ use other variables or external module members defined at the global scope (see below) </li>
# </ul>
# 
# Here are some trivial examples:
# 
#     # good - one parameter, imports numpy within function scope,
#     #        returns column of values of the right shape.
#     def all_zeros(dataset):
#         from numpy import zeros
#         n = len(dataset["users"])
#         return zeros((n,1))
#         
#     # bad - wrong number of parameters
#     def two_parameters(users, groups):
#         return users["age"]
#        
#     # bad - return value cannot be coerced to DataFrame
#     def scalar_zero(dataset):
#         return 0
# 
#     # bad - return value is not correct shape
#     def row_of_zeros(dataset):
#         from numpy import zeros
#         return zeros((20,20))
#         
#     # bad - modifies underlying dataset!
#     def modify_dataset(dataset):
#         dataset["users"].iloc[0,0] += 1
#         return None
#         
# 
# Your feature will be evaluated by Feature Factory in an isolated namespace. This means that your feature cannot expect variables that you have defined at the global scope to exist. Similarly, *all module imports should be done within your function*.
# 
# The first feature below is *invalid*, because it uses a variable defined at the global scope:
# 
#     # bad
#     cutoff = 30
#     def hi_lo_age(dataset):
#         from sklearn.preprocessing import binarize
#         return binarize(dataset["users"]["age"].values.reshape(-1,1), cutoff)
#         
#     # better
#     def hi_lo_age(dataset):
#         from sklearn.preprocessing import binarize
#         cutoff = 30
#         return binarize(dataset["users"]["age"].values.reshape(-1,1), cutoff)
#         
# However, you can use helper *functions* that you define at the global scope:
# 
#     def first_name_is_longer(name):
#         first, last = name.split(" ")
#         return len(first) > len(last)
#      
#     # okay
#     def long_first_name(dataset):
#         return dataset["users"]["name"].apply(first_name_is_longer)
#         

# As an initial check that our feature does what we want it to, and doesn't have any bugs, we can run it on the dataset.

# In[ ]:

def hi_lo_age(dataset):
    from sklearn.preprocessing import binarize
    cutoff = 30
    return binarize(dataset["users"]["age"].values.reshape(-1,1), cutoff)

hi_lo_age(dataset)


# ## Evaluate a feature on training data
# 
# Now that we have written a candidate feature, we can evaluate it on training data. The evaluation routine proceeds as follows.
# 
# 1. Obtains a valid dataset. That is, if the `dataset` has been modified, it is reloaded.
# 2. Extracts features. That is, your function is called with the dataset as its parameter, returning a column of values.
# 3. Verifies the integrity of the dataset, in that it was not changed by executing the feature.
# 4. Validates feature values, to ensure they meet the requirements listed above.
# 5. Builds full feature matrix, by combining extracted feature values with pre-processed entity features.
# 6. Fits model and computes metrics. Given the task (classification, regression, etc.), a model is chosen and fit given the full feature matrix. Then, appropriate metrics are computed via cross-validation and displayed.
# 
# In your workflow, you may run the `evaluate` function several times. At first, it may reveal bugs or syntax errors that you will fix. Next, it may reveal that your feature did not meet some of the Feature Factory requirements, such as returning a single column of values or using function-scope imports. Finally, you may find that your feature's performance, in terms of metrics like classification accuracy or mean squared error, are not as good as you hoped, and you may modify it or jettison it altogether.
# 
# The `evaluate` function takes a single argument: the candidate feature.

# In[ ]:

commands.evaluate(hi_lo_age)


# ## Submit a feature to Feature database
# 
# Now that you have evaluated your feature locally on training data, and are happy with its performance, you can submit it to the Feature Evaluation Server. The evaluation server will essentially repeat the steps in `evaluate`, with some slight changes. For example, it fits the model on the training dataset and evaluates it on the *test dataset*, without performing cross-validation.
# 
# During submission, you are asked to write a natural language description (in English) of your feature. Imagine that you are explaining your code to a non-technical colleague. This description should be 
# - *clear*
# - *concise*
# - *informative* to a domain expert who is not a data scientist
# - *accurate* (in that your description matches what the code actually does)
# 
# You will be prompted to type in a description to a textbox input. Alternately, you can pass a string using the keyword argument `description`.
# 
# If there are no issues, the feature and its associated performance metrics are added to the Feature database ("registered").

# In[ ]:

description = "Age above 30 years"
commands.submit(hi_lo_age, description=description)
