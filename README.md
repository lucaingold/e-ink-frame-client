##E-Ink-Frame Client

Client for the hardware frame. 

### Installation
```
sudo apt-get update
sudo apt full-upgrade
```

#### Git
```
sudo apt-get install -y git
```

#### Git clone
```
git clone https://github.com/lucaingold/e-ink-frame-client.git
cd e-ink-frame-client
```

#### Install & Config ufw
```
sudo apt-get install ufw
sudo ufw allow 22
sudo ufw allow 8883
sudo ufw enable
```

#### Edit Config
ifconfig > mac-address
```
sudo nano config.ini
```

#### Install Python
```
sudo apt-get install -y python3-pip
sudo apt-get install -y python3-pil
sudo pip3 install -y RPi.GPIO
sudo apt-get install  -y python3-venv

sudo apt-get install libopenjp2-7
```

##### dietpi
sudo apt-get install build-essential
sudo apt-get install python3-dev
sudo apt install libopenblas-dev
Y
#### Enable SPI
```
sudo raspi-config
```
Choose Interface Option->SPI->Yes
or
```
sudo dietpi-config
```
SPI State = On

#### Enable VENV
```
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

#### Install OMNI EPD Library 
```
pip3 install git+https://github.com/robweber/omni-epd.git#egg=waveshare_epd.it8951
pip3 install git+https://github.com/robweber/omni-epd.git#egg=omni-epd
```

##### Alternative

```
git clone https://github.com/robweber/omni-epd.git
cd omni-epd
pip3 install --prefer-binary .
```

#### Configure Path
```
export PATH="$PATH:/home/luca/.local/bin"
source ~/.bashrc
```

#### Start
```
sudo chmod +x start.sh 
```

#### PiJuice
sudo apt-get install pijuice-base
pijuice_cli

### Lowering Raspberry Pi Zero WH power consumption
https://www.cnx-software.com/2021/12/09/raspberry-pi-zero-2-w-power-consumption/