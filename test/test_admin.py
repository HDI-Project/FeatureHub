from featurefactory.admin.admin import Commands
commands = Commands()
commands.set_up(drop=True)

name = "airbnb"
problem_type = "classification"
data_path = "/data/airbnb"
files = ["train_users_2.csv", "sessions.csv", "countries.csv", "age_gender_bkts.csv"]
table_names = ["users", "sessions", "countries", "age_gender_bkts"]
target_table_name = "users"
y_column = "country_destination"

commands.create_problem(name, problem_type, data_path, files, table_names,
        target_table_name, y_column)

# more testing :)
commands.get_problems()
commands.get_features()
