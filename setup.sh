#! /usr/bin/bash

# Set the local directory
LOCAL_DIR="$HOME/e-ink-frame-client"

# Color code variables
RED="\e[0;91m"
YELLOW="\e[0;93m"
GREEN='\033[0;32m'
RESET="\e[0m"

# File paths
SERVICE_DIR=/etc/systemd/system
SERVICE_FILE=einkscreen.service
SERVICE_FILE_TEMPLATE=einkscreen.service.template

function service_installed(){
  # return 0 if the service is installed, 1 if no
  if [ -f "$SERVICE_DIR/$SERVICE_FILE" ]; then
    return 0
  else
    return 1
  fi
}

function copy_service_file(){
  sudo mv $SERVICE_FILE $SERVICE_DIR
  sudo systemctl daemon-reload
}

function install_service(){
  if [ -d "${LOCAL_DIR}" ]; then
    cd "$LOCAL_DIR" || return

    # generate the service file
    envsubst <$SERVICE_FILE_TEMPLATE > $SERVICE_FILE

    if ! (service_installed); then
      # install the service files and enable
      copy_service_file
      sudo systemctl enable einkscreen

      echo -e "einkscreen service installed! Use '${GREEN}sudo systemctl restart einkscreen${RESET}' to test"
    else
      echo -e "${YELLOW}einkscreen service is installed, checking if it needs an update${RESET}"
      if ! (cmp -s "einkscreen.service" "/etc/systemd/system/einkscreen.service"); then
        copy_service_file
        echo -e "Updating einkscreen service file"
      else
        # remove the generated service file
        echo -e "No update needed"
        rm $SERVICE_FILE
      fi
    fi
  else
    echo -e "${RED}einkscreen repo does not exist! Use option 1 - Install/Upgrade einkscreen first${RESET}"
  fi

  # go back to home
  cd "$HOME" || return
}

install_service