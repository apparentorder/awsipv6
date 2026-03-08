#!/bin/sh
# Fetch endpoint data using botocore

set -e

BOTOCORE_REPO=~/environment/botocore
LIVE_ARG="${1:-}"

if ! test -d "$BOTOCORE_REPO"; then
    git clone -b master https://github.com/boto/botocore.git "$BOTOCORE_REPO"
    sed -i.orig "s/^__version__ = '/__version__ = 'awsipv6-git-/" "$BOTOCORE_REPO/botocore/__init__.py"
else
    ( cd "$BOTOCORE_REPO" && git pull )
fi

python3 -u update-data/awsipv6-get.py "$BOTOCORE_REPO" $LIVE_ARG
