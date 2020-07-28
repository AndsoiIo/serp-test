from sqlite3 import connect


def setup_db(dbconfig: dict):
    # connect to db with autocommit mode
    db = connect(dbconfig['name'], isolation_level=None, check_same_thread=False)
    cursor = db.cursor()

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {dbconfig['table']} (
            query TEXT,
            suggestion TEXT,
            type TEXT
        )
    ''')
    cursor.close()
    return db