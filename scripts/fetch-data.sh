#!/bin/sh
# Fetch endpoint data using botocore

set -e

BOTOCORE_REPO=~/environment/botocore
LIVE_ARG="${1:-}"
BOTOCORE_INIT="$BOTOCORE_REPO/botocore/__init__.py"

if ! test -d "$BOTOCORE_REPO"; then
    git clone -b master https://github.com/boto/botocore.git "$BOTOCORE_REPO"
else
    # Undo the version tag so git pull and pip see upstream __init__.py
    if test -f "$BOTOCORE_INIT.orig"; then
        mv "$BOTOCORE_INIT.orig" "$BOTOCORE_INIT"
    fi
    ( cd "$BOTOCORE_REPO" && git pull )
fi

# Runtime deps of this checkout (jmespath, python-dateutil, urllib3, ...).
# awsipv6-get.py still imports the clone via sys.path, not PyPI botocore.
# Install before tagging __version__; awsipv6-git-* is not PEP 440.
python3 -m pip install -e "$BOTOCORE_REPO"

sed -i.orig "s/^__version__ = '/__version__ = 'awsipv6-git-/" "$BOTOCORE_INIT"

python3 -u update-data/awsipv6-get.py "$BOTOCORE_REPO" $LIVE_ARG
