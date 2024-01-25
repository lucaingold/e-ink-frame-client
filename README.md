##E-Ink-Frame Client

Client for the hardware frame. 

### Installation
sudo apt-get update
sudo apt full-upgrade

#### Git
sudo apt-get install -y git

#### Git clone
git clone https://github.com/lucaingold/e-ink-frame-client.git
cd e-ink-frame-client

#### Install & Config ufw
sudo apt-get install ufw
sudo ufw allow 22
sudo ufw allow 8883
sudo ufw enable

#### Install Python
sudo apt-get install -y python3-pip
sudo apt-get install -y python3-pil
sudo pip3 install -y RPi.GPIO
sudo apt-get install  -y python3-venv

#### Enable SPI
sudo raspi-config
Choose Interface Option->SPI->Yes
or
sudo dietpi-config
SPI State = On

### Enable VENV
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
sudo apt-get install libopenjp2-7

### Install OMNI EPD Library 
pip3 install git+https://github.com/robweber/omni-epd.git#egg=waveshare_epd.it8951
 
### Start
sudo chmod +x start.sh 

