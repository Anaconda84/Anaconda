#!/bin/sh
cd `dirname $0` 
XUL_VERSION=1.9.1.5
IDL_PREFIX=/usr/share/idl/xulrunner-$XUL_VERSION
XPIDL=/usr/lib/xulrunner-$XUL_VERSION/xpidl

for i in tribeIChannel; do
    XPT=../tribe/components/$i.xpt
    IDL=$i.idl
    $XPIDL -m typelib -w -v -I $IDL_PREFIX/stable -e $XPT $IDL
done
