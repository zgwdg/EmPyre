#!/bin/bash

openssl req -new -x509 -keyout ../data/empyre.pem -out ../data/empyre.pem -days 365 -nodes -subj "/C=US" >/dev/null 2>&1

echo -e "\n\n [*] Certificate written to ../data/empyre.pem\n"
