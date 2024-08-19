from setuptools import setup, find_packages
from Cython.Build import cythonize
import sys

# Function to determine if we should include specific extensions or dependencies
def should_include_extension(extension_name):
    # Example condition: Check if running on a specific platform
    # Modify this function as needed for your conditions
    return "raspberry" in sys.platform

# Define base requirements
install_requires = [
    "paho-mqtt==1.6.1",
    "pillow==10.2.0",
    "asyncio-atexit==1.0.1",
    "schedule==1.2.1",
    "fastapi==0.111.0",
    "uvicorn==0.30.1",
    "PyYAML==6.0.1",
    "pydantic==2.8.0",
    "setuptools",
    "wheel",
    "Cython"
]

# Conditionally add RPi.GPIO if on a Raspberry Pi
if "raspberry" in sys.platform:
    install_requires.append("RPi.GPIO")

# Define extensions conditionally
extensions = []
if should_include_extension("IT8951"):
    extensions = cythonize([
        "src/IT8951/spi.pyx",
        "src/IT8951/img_manip.pyx"
    ])

setup(
    name="e-ink-frame-client",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=install_requires,
    ext_modules=extensions,
    include_package_data=True,
    python_requires='>=3.8',
)
