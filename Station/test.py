#! /opt/micropython.git/ports/unix/micropython
import sys

sys.path.insert(0, 'src')
from lib import logging

logging.basicConfig(level=logging.INFO, filename=True)
logger = logging.getLogger(__name__)

for i in range(1000):
    logger.info("HELLO THERE")
