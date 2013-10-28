#!/bin/sh
TEMPDIR=`mktemp -d`
CFGFILE=libra.conf.sample
tools/config/generate_sample.sh -b ./ -p libra -o $TEMPDIR
if ! diff $TEMPDIR/$CFGFILE etc/libra/$CFGFILE
then
    echo "E: libra.conf.sample is not up to date, please run tools/config/generate_sample.sh"
    exit 42
fi