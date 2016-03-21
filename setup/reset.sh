#!/bin/bash

IFS='/' read -a array <<< pwd

if [[ "$(pwd)" != *setup ]]
then
	cd ./setup
fi

# reset the database
rm ../data/empyre.db
./setup_database.py
cd ..

# remove the debug file if it exists
rm empyre.debug

# remove the download folders
rm -rf ./downloads/

# start up EmPyre
./empyre --debug

# Support non-root instalation of DB
chown $(logname):$(logname) ../data/empyre.db
