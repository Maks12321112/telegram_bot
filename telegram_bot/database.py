import sqlite3


conn = sqlite3.connect('script.sql')
cursor = conn.cursor()

def create():
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                phone TEXT,
                password INTEGER
            )
        ''')


    conn.commit()

    conn.close()

def reset_database( name_table='users'):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute(f'DELETE FROM {name_table}')
    conn.commit()
    conn.close()


def write_to_database(data, name_table='users'):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute(f'REPLACE INTO {name_table} VALUES ({", ".join(["?"] * len(data))})', data)
    conn.commit()
    conn.close()

def load_database( name_table='users'):
    conn = sqlite3.connect('database1.db')
    c = conn.cursor()
    c.execute(f'SELECT * FROM {name_table} where name like  "%в"')
    data = c.fetchone()
    print((data))
    conn.close()
    return list(data)


load_database(name_table='city')