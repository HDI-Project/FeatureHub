from featurefactory.admin.admin import Commands
commands = Commands()
commands.set_up(drop=True)

problem_params = {
    "name"                           : "airbnb",
    "problem_type"                   : "classification",
    "data_dir_train"                 : "/data/train/airbnb",
    "data_dir_train"                 : "/data/test/airbnb",
    "files"                          : ["users.csv", "users_features.csv", "target.csv", "sessions.csv", "countries.csv", "age_gender_bkts.csv"],
    "table_names"                    : ["users", "users_features", "target", "sessions", "countries", "age_gender_bkts"],
    "entities_table_name"            : "users",
    "entities_featurized_table_name" : "users_features",
    "target_table_name"              : "target",
}
commands.create_problem(**problem_params)

# more testing :)
commands.get_problems()
commands.get_features()
