import logging
import os

logger = logging.getLogger(__name__)
# Kubernetes has a log collector, so we don't need to write logs to a file
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s]: %(message)s'))
logger.addHandler(console_handler)
# Set level to DEBUG for development
print(os.getenv("DEV_MODE", None))
if os.getenv("DEV_MODE", None) == 'True':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

logger.info("Logger initialized...")
LOGGER = logger
