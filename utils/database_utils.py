import mysql.connector

def setup_database_connection(config):
    if not config.get('use_DB', False):
        print("Database usage is disabled in the configuration.")
        return None

    if 'database' not in config:
        print("Database configuration not found in config.")
        return None

    db_config = config['database']
    try:
        db_connection = mysql.connector.connect(
            host=db_config.get('host', ''),
            user=db_config.get('user', ''),
            password=db_config.get('password', ''),
            database=db_config.get('database', ''),
            autocommit=True,
            connection_timeout=6000
        )
        print("Database connection established successfully.")
        return db_connection
    except mysql.connector.Error as err:
        print(f"Error connecting to the database: {err}")
        return None

def reconnect_database(conn):
    try:
        conn.ping(reconnect=True, attempts=3, delay=5)
    except Exception as e:
        print(f"Error reconnecting to the database: {e}")

def db_write(conn, query, params=None):
    """Insert or update data in the database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            conn.commit()
        return True
    except Exception as e:
        print(f"Database write error: {e}")
        conn.rollback()
        return False

def db_get(conn, query, params=None, fetchone=False):
    """Retrieve data from the database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone() if fetchone else cursor.fetchall()
    except Exception as e:
        print(f"Database get error: {e}")
        return None

def db_update(conn, query, params=None):
    """Update data in the database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            conn.commit()
        return True
    except Exception as e:
        print(f"Database update error: {e}")
        conn.rollback()
        return False

def db_delete(conn, query, params=None):
    """Delete data from the database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            conn.commit()
        return True
    except Exception as e:
        print(f"Database delete error: {e}")
        conn.rollback()
        return False

def get_active_connection_count(conn):
    """Returns the number of active connections for the current user/database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW PROCESSLIST")
            processes = cursor.fetchall()
            # Get current user and database
            cursor.execute("SELECT USER(), DATABASE()")
            current_user, current_db = cursor.fetchone()
            # Count only connections from this user and database
            count = sum(
                1 for p in processes
                if (p[1] == current_user.split('@')[0]) and (not current_db or p[3] == current_db)
            )
            return count
    except Exception as e:
        print(f"Error checking active database connections: {e}")
        return None
