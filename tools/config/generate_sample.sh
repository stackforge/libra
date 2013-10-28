#!/usr/bin/env bash

print_hint() {
    echo "Try \`${0##*/} --help' for more information." >&2
}

PARSED_OPTIONS=$(getopt -n "${0##*/}" -o hb:p:o: \
                 --long help,base-dir:,package-name:,output-dir: -- "$@")

if [ $? != 0 ] ; then print_hint ; exit 1 ; fi

eval set -- "$PARSED_OPTIONS"

while true; do
    case "$1" in
        -h|--help)
            echo "${0##*/} [options]"
            echo ""
            echo "options:"
            echo "-h, --help                show brief help"
            echo "-b, --base-dir=DIR        project base directory"
            echo "-p, --package-name=NAME   project package name"
            echo "-o, --output-dir=DIR      file output directory"
            exit 0
            ;;
        -b|--base-dir)
            shift
            BASEDIR=`echo $1 | sed -e 's/\/*$//g'`
            shift
            ;;
        -p|--package-name)
            shift
            PACKAGENAME=`echo $1`
            shift
            ;;
        -o|--output-dir)
            shift
            OUTPUTDIR=`echo $1 | sed -e 's/\/*$//g'`
            shift
            ;;
        --)
            break
            ;;
    esac
done

BASEDIR=${BASEDIR:-`pwd`}
if ! [ -d $BASEDIR ]
then
    echo "${0##*/}: missing project base directory" >&2 ; print_hint ; exit 1
elif [[ $BASEDIR != /* ]]
then
    BASEDIR=$(cd "$BASEDIR" && pwd)
fi

PACKAGENAME=${PACKAGENAME:-${BASEDIR##*/}}
TARGETDIR=$BASEDIR/$PACKAGENAME
if ! [ -d $TARGETDIR ]
then
    echo "${0##*/}: invalid project package name" >&2 ; print_hint ; exit 1
fi

OUTPUTDIR=${OUTPUTDIR:-$BASEDIR/etc}
# NOTE(bnemec): Some projects put their sample config in etc/,
#               some in etc/$PACKAGENAME/
if [ -d $OUTPUTDIR/$PACKAGENAME ]
then
    OUTPUTDIR=$OUTPUTDIR/$PACKAGENAME
elif ! [ -d $OUTPUTDIR ]
then
    echo "${0##*/}: cannot access \`$OUTPUTDIR': No such file or directory" >&2
    exit 1
fi

BASEDIRESC=`echo $BASEDIR | sed -e 's/\//\\\\\//g'`
find $TARGETDIR -type f -name "*.pyc" -delete
FILES=$(find $TARGETDIR -type f -name "*.py" ! -path "*/tests/*" \
        -exec grep -l "Opt(" {} + | sed -e "s/^$BASEDIRESC\///g" | sort -u)

export EVENTLET_NO_GREENDNS=yes

OS_VARS=$(set | sed -n '/^OS_/s/=[^=]*$//gp' | xargs)
[ "$OS_VARS" ] && eval "unset \$OS_VARS"

MODULEPATH=libra.openstack.common.config.generator
OUTPUTFILE=$OUTPUTDIR/$PACKAGENAME.cfg.sample
python -m $MODULEPATH $FILES > $OUTPUTFILE