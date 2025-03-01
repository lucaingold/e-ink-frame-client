import logging

logger = logging.getLogger(__name__)

class EPD:
    def __init__(self):
        self.width = 1600
        self.height = 1200
        logger.info("Initialized Mocked EPD")
        
    def init(self):
        logger.info("Mocked EPD init")
        
    def display(self, image):
        logger.info("Mocked EPD display")
        
    def sleep(self):
        logger.info("Mocked EPD sleep")
        
    def Clear(self):
        logger.info("Mocked EPD Clear")