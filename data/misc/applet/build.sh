#!/bin/bash

rm -rf ./host/
mkdir host
javac Java.java
jar cvf Update.jar Java.class
jar ufm Update.jar manifest.mf
mv Java.class ./host/
mv Update.jar ./host/
cp applet.html ./host/
