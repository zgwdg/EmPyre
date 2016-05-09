#!/bin/bash

if [[ $EUID -ne 0 ]]; then
   echo "[!]This script must be run as root" 1>&2
   exit 1
fi

IFS='/' read -a array <<< pwd

if [[ "$(pwd)" != *setup ]]
then
	cd ./setup
fi

# reset the database
rm ../data/empyre.db
./setup_database.py
cd ..
# Support non-root instalation of DB
chown $(logname):$(logname) ./data/empyre.db

# remove the debug file if it exists
if [ -e empyre.debug ]
then
    rm empyre.debug
fi

# remove the download folders
rm -rf ./downloads/

# start up EmPyre
./empyre
