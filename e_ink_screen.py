from typing import Tuple, Optional
import logging
import time
from omni_epd import displayfactory, EPDNotFoundError

# Constants
DISPLAY_TYPE = "waveshare_epd.it8951"
DEFAULT_WIDTH = 1600
DEFAULT_HEIGHT = 1200
ROTATION_FACTOR = 90
MAX_RETRIES = 3
RETRY_DELAY = 2

logger = logging.getLogger(__name__)

class EInkScreen:
    """Manages the E-Ink display operations."""
    
    def __init__(self, screen_width: int = DEFAULT_WIDTH, screen_height: int = DEFAULT_HEIGHT) -> None:
        """
        Initialize the E-Ink screen with specified dimensions.
        
        Args:
            screen_width (int): Width of the screen in pixels
            screen_height (int): Height of the screen in pixels
        """
        self.width = screen_width
        self.height = screen_height
        self.config_dict = {
            'spi_bus': 0,
            'spi_device': 0,
            'spi_hz': 2000000,
            'vcom': -2.27
        }
        self.epd = None
        self.image_display = None

    def run(self) -> None:
        """Initialize and configure the E-Ink display."""
        logger.info("Initializing E-Ink display")
        try:
            self._initialize_display_with_retry()
        except EPDNotFoundError:
            logger.error(f"Display type {DISPLAY_TYPE} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize display after {MAX_RETRIES} attempts: {e}")
            raise

    def _initialize_display_with_retry(self) -> None:
        """Set up the display with proper configuration and retry mechanism."""
        for attempt in range(MAX_RETRIES):
            try:
                logger.debug(f"Display initialization attempt {attempt + 1}/{MAX_RETRIES}")
                self.epd = displayfactory.load_display_driver(DISPLAY_TYPE, self.config_dict)
                self.epd.width = self.width
                self.epd.height = self.height
                self.width, self.height = self._set_rotate(self.epd.width, self.epd.height)
                logger.info(f"Display initialized with dimensions: {self.width}x{self.height}")
                return
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    raise

    def display_image_on_epd(self, display_image) -> None:
        """
        Display an image on the E-Ink screen.
        
        Args:
            display_image: PIL Image to display
        """
        try:
            self.image_display = display_image.copy()
            logger.info("Preparing E-Ink screen")
            self.epd.prepare()
            self.epd.display(self.image_display)
        except Exception as e:
            logger.error(f"Failed to display image: {e}")
            raise
        finally:
            self._sleep_display()

    def _sleep_display(self) -> None:
        """Put the display to sleep and close connection."""
        try:
            logger.info("Putting E-Ink screen to sleep")
            self.epd.sleep()
            self.epd.close()
        except Exception as e:
            logger.error(f"Failed to sleep display: {e}")
            raise

    @staticmethod
    def _set_rotate(width: int, height: int, rotate: int = 0) -> Tuple[int, int]:
        """
        Calculate dimensions after rotation.
        
        Args:
            width (int): Original width
            height (int): Original height
            rotate (int): Rotation angle in degrees
            
        Returns:
            Tuple[int, int]: New width and height
        """
        if (rotate / ROTATION_FACTOR) % 2 == 1:
            return height, width
        return width, height
