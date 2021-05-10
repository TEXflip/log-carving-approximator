#!/usr/bin/sh

# Installing the pip3 package manager
sudo apt-get install software-properties-common
sudo apt-add-repository universe
sudo apt-get update
sudo apt-get install python3-pip

# Installing python libraries
pip3 install pyglet
pip3 install pywavefront
pip3 install numpy
pip3 install trimesh
pip3 install scipy
pip3 install shapely
pip3 install networkx
pip3 install rtree
pip3 install triangle

echo "Success!"
