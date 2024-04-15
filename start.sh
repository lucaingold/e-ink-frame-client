#! /usr/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo -n 'db' | gnome-keyring-daemon --unlock
cd ${SCRIPT_DIR}
git pull
source .venv/bin/activate
python3 app.py
deactivate