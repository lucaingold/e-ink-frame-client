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
VCOM = -2.27  # Specific VCOM value for your hardware

logger = logging.getLogger(__name__)

class EInkScreen:
    """Manages the E-Ink display operations."""
    
    def __init__(self, width: int, height: int, mock_epd: bool = False):
        """
        Initialize the E-Ink screen with specified dimensions.
        
        Args:
            width (int): Width of the screen in pixels
            height (int): Height of the screen in pixels
            mock_epd (bool): Flag to use mock EPD for testing
        """
        self.width = width
        self.height = height
        self.mock_epd = mock_epd
        self.epd = None
        
        # Update configuration dictionary structure
        self.config_dict = {
            'EPD': {
                'type': DISPLAY_TYPE,
                'vcom': VCOM,
                'mode': 'gray16'
            },
            'waveshare_epd.it8951': {
                'spi_bus': 0,
                'spi_device': 0,
                'spi_hz': 24000000,  # 24MHz SPI clock
                'reset_pin': 17,
                'busy_pin': 24,
                'vcom': VCOM
            },
            'Image Enhancements': {
                'color': 1,
                'contrast': 1
            }
        }
        
        if mock_epd:
            try:
                from mocked_epd import EPD
                self.epd = EPD()
                logger.info("Using mock EPD")
            except ImportError:
                logger.error("Mock EPD requested but mocked_epd.py not found")
                raise
        else:
            try:
                # Try to initialize the display with retries
                for attempt in range(MAX_RETRIES):
                    try:
                        logger.debug(f"Attempting to initialize display (attempt {attempt + 1}/{MAX_RETRIES})")
                        self.epd = displayfactory.load_display_driver(DISPLAY_TYPE, self.config_dict)
                        self.epd.width = self.width
                        self.epd.height = self.height
                        logger.info("Display initialized successfully")
                        break
                    except RuntimeError as e:
                        if "communication with device failed" in str(e):
                            if attempt < MAX_RETRIES - 1:
                                logger.warning(f"Communication failed, retrying in {RETRY_DELAY} seconds...")
                                time.sleep(RETRY_DELAY)
                            else:
                                logger.error("Failed to communicate with display after all retries")
                                raise RuntimeError("Could not establish communication with display")
                        else:
                            raise
            except Exception as e:
                logger.error(f"Failed to initialize display driver: {e}")
                raise

        logger.info(f"Initialized E-Ink screen with mock_epd={mock_epd}")
        self.image_display = None

    def run(self) -> None:
        """Initialize and configure the E-Ink display."""
        logger.info("Initializing E-Ink display")
        try:
            self.epd.prepare()
            logger.info("Display prepared successfully")
        except Exception as e:
            logger.error(f"Failed to prepare display: {e}")
            raise

    def display_image_on_epd(self, display_image) -> None:
        """
        Display an image on the E-Ink screen.
        
        Args:
            display_image: PIL Image to display
        """
        try:
            logger.info("Preparing to display image")
            self.epd.prepare()
            resized_image = display_image.resize((self.width, self.height))
            logger.info("Displaying image")
            self.epd.display(resized_image)
            logger.info("Image displayed successfully")
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
