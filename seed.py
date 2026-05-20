from smartpark.db import init_db


if __name__ == "__main__":
    init_db(reset=True, seed=True)
    print("SmartPark demo database was reset and seeded.")
