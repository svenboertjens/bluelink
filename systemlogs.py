#!/opt/pypackages/bin/python

from systemd.journal import JournalHandler
import logging

# Set up the logger
logger = logging.getLogger("bluelink")
logger.setLevel(logging.DEBUG)

# Create a journal handler
journal_handler = JournalHandler()
journal_handler.setLevel(logging.DEBUG)

# Set a formatter for the journal handler
formatter = logging.Formatter('%(message)s')
journal_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(journal_handler)

# The debugging levels and their respective functions
levels = {
    "info": logger.info,
    "error": logger.error,
    "debug": logger.debug,
    "warning": logger.warning,
    "critical": logger.critical,
    "debug": logger.debug
}

# The function to log stuff with a given level
def log(message, level):
    # Default the level to debug if not exists
    if level not in levels:
        level = "debug"
        
    # Log the message to the given level
    levels[level](message)

