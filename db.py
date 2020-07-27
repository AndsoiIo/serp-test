from sqlite3 import connect


def setup_db(db_name: str):
    # connect to db with autocommit mode
    db = connect(db_name, isolation_level=None, check_same_thread=False)  # check_same_thread=False for thread mode :)
    cursor = db.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS allo (
            query TEXT,
            suggestion TEXT,
            type TEXT
        )
    ''')
    cursor.close()
    return db