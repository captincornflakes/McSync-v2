import logging
from datetime import datetime

# Configure the logger
logging.basicConfig(
    filename="events.log",  # Log file name
    level=logging.INFO,  # Log level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    datefmt="%Y-%m-%d %H:%M:%S"  # Date format
)

def log_event(message, level="info"):
    """
    Log an event message with the specified log level.

    Args:
        message (str): The message to log.
        level (str): The log level ('info', 'warning', 'error', 'debug').
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{timestamp} - {message}"

    if level.lower() == "info":
        logging.info(log_message)
    elif level.lower() == "warning":
        logging.warning(log_message)
    elif level.lower() == "error":
        logging.error(log_message)
    elif level.lower() == "debug":
        logging.debug(log_message)
    else:
        logging.info(log_message)  # Default to info level

def datalog(conn, type, string):
    """
    Log an event to the database.

    Args:
        conn: The database connection object.
        type (str): The type of the log event.
        string (str): The content of the log event.

    Returns:
        bool: True if logging was successful, False otherwise.
    """
    time = datetime.now().strftime("%m-%d-%Y %I:%M:%S %p")
    insert_sql = "INSERT INTO logs(time, type, content) VALUES (%s, %s, %s)"
    server_data = (time, type, string)
    try:
        with conn.cursor() as cursor:
            cursor.execute(insert_sql, server_data)
            conn.commit()
        return True
    except Exception as e:
        print(f"Logging error: {e}")
        return False