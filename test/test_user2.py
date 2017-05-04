# Test of airbnb problem

from featurefactory.problems import commands
dataset, target = commands.get_sample_dataset()

def example_feature(dataset):
    1+1
    return dataset["users"][["age"]].fillna(0)

def example_feature2(dataset):
    1+2
    return dataset["users"][["age"]].fillna(0)

# register example_feature (should succeed)
print("Trying new feature (should succeed)...")
print("executing 'commands.evaluate(example_feature)'")
commands.evaluate(example_feature)
description="Age"
print("executing 'commands.submit(example_feature, description=description)'")
commands.submit(example_feature, description=description)
print("Re-registering existing feature (should fail)...done")

# re-register example_feature (should fail)
print("Trying existing feature (should fail)...")
print("executing 'commands.evaluate(example_feature)'")
commands.evaluate(example_feature)
description="Age"
print("executing 'commands.submit(example_feature, description=description)'")
commands.submit(example_feature, description=description)
print("Re-registering existing feature (should fail)...done")

# register example_feature2 (should succeed)
print("Trying new feature (should succeed)...")
print("executing 'commands.evaluate(example_feature2)'")
commands.evaluate(example_feature2)
description="Age"
print("executing 'commands.submit(example_feature2, description=description)'")
commands.submit(example_feature2, description=description)
print("Registering new feature (should succeed)...done")

# test feature discovery
print("executing 'commands.discover_features()'")
commands.discover_features()
print("executing 'commands.print_my_features()'")
commands.print_my_features()
