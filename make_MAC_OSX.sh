#!/bin/sh


rm -R build
rm -R dist

python setup.py py2app

