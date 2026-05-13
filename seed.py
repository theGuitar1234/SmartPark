from smartpark.db import init_db, seed_items


if __name__ == "__main__":
    init_db()
    inserted = seed_items(100)
    if inserted:
        print(f"Seeded {inserted} new records. The items table now has at least 100 rows.")
    else:
        print("No new records needed. The items table already has at least 100 rows.")
