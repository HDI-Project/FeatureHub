# Test of sberbank problem

from featurefactory.problems.sberbank import commands
dataset, target = commands.get_sample_dataset()

def male_female_ratio(dataset):
    return dataset["transactions"]["male_f"]/dataset["transactions"]["female_f"]

def healthcare_centers_normalized(dataset):
    from sklearn.preprocessing import StandardScaler
    return StandardScaler().fit_transform(dataset["transactions"]["healthcare_centers_raion"])

# register male_female_ratio (should succeed)
print("Trying new feature (should succeed)...")
print("executing 'commands.evaluate(male_female_ratio)'")
commands.evaluate(male_female_ratio)
description="Age"
print("executing 'commands.submit(male_female_ratio, description=description)'")
commands.submit(male_female_ratio, description=description)
print("Re-registering existing feature (should fail)...done")

# re-register male_female_ratio (should fail)
print("Trying existing feature (should fail)...")
print("executing 'commands.evaluate(male_female_ratio)'")
commands.evaluate(male_female_ratio)
description="Male-female ratio"
print("executing 'commands.submit(male_female_ratio, description=description)'")
commands.submit(male_female_ratio, description=description)
print("Re-registering existing feature (should fail)...done")

# register healthcare_centers_normalized (should succeed)
print("Trying new feature (should succeed)...")
print("executing 'commands.evaluate(healthcare_centers_normalized)'")
commands.evaluate(healthcare_centers_normalized)
description="Healthcare centers in Raion (standardized)"
print("executing 'commands.submit(healthcare_centers_normalized, description=description)'")
commands.submit(healthcare_centers_normalized, description=description)
print("Registering new feature (should succeed)...done")

# test feature discovery
print("executing 'commands.discover_features()'")
commands.discover_features()
print("executing 'commands.print_my_features()'")
commands.print_my_features()
