import sqlite3

DATABASE_NAME = "inventory.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Ensure foreign key support is enabled
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 2. Physical Locations Table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS locations
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       shelf_name
                       TEXT
                       NOT
                       NULL,
                       box_number
                       TEXT
                       NOT
                       NULL
                       UNIQUE
                   )
                   ''')

    # 3. Hardware Items Table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS hardware_items
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       category
                       TEXT
                       NOT
                       NULL,
                       brand
                       TEXT
                       NOT
                       NULL,
                       model
                       TEXT
                       NOT
                       NULL,
                       quantity
                       INTEGER
                       NOT
                       NULL
                       DEFAULT
                       1,
                       location_id
                       INTEGER,
                       FOREIGN
                       KEY
                   (
                       location_id
                   ) REFERENCES locations
                   (
                       id
                   ) ON DELETE CASCADE
                       )
                   ''')

    # 4. Dynamic Technical Specs Table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS technical_specs
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       item_id
                       INTEGER
                       NOT
                       NULL,
                       spec_key
                       TEXT
                       NOT
                       NULL,
                       spec_value
                       TEXT
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       item_id
                   ) REFERENCES hardware_items
                   (
                       id
                   ) ON DELETE CASCADE
                       )
                   ''')

    # Absolute Check: Force Box A and Box B initialization if absent
    cursor.execute("SELECT COUNT(*) FROM locations")
    count = cursor.fetchone()[0]

    if count == 0:
        print("Empty database state detected. Forcing closet seed parameters...")
        # Add primary container slots
        cursor.execute("INSERT INTO locations (shelf_name, box_number) VALUES ('Top Shelf', 'Box A')")
        cursor.execute("INSERT INTO locations (shelf_name, box_number) VALUES ('Middle Shelf', 'Box B')")

        # Seed an initial RAM item into Box A (ID: 1)
        cursor.execute(
            "INSERT INTO hardware_items (category, brand, model, quantity, location_id) VALUES ('RAM', 'Corsair', 'Vengeance LPX', 2, 1)")
        cursor.execute("INSERT INTO technical_specs (item_id, spec_key, spec_value) VALUES (1, 'Generation', 'DDR4')")
        cursor.execute("INSERT INTO technical_specs (item_id, spec_key, spec_value) VALUES (1, 'Speed', '3200MHz')")
        cursor.execute("INSERT INTO technical_specs (item_id, spec_key, spec_value) VALUES (1, 'Capacity', '16GB')")

        # Seed an initial SSD item into Box B (ID: 2)
        cursor.execute(
            "INSERT INTO hardware_items (category, brand, model, quantity, location_id) VALUES ('SSD', 'Samsung', '980 Pro', 1, 2)")
        cursor.execute("INSERT INTO technical_specs (item_id, spec_key, spec_value) VALUES (2, 'Type', 'NVMe M.2')")
        cursor.execute("INSERT INTO technical_specs (item_id, spec_key, spec_value) VALUES (2, 'Capacity', '1TB')")
        print("Seed completion successful!")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
