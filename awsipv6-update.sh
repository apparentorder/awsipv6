#!/bin/sh

set -e

BOTOCORE_REPO=~/environment/botocore
S3BASE="s3://awsipv6/beta"
LIVE_ARG=""

if test "$1" = "--live"; then
    S3BASE="s3://awsipv6"
    LIVE_ARG="--live"
fi

if ! test -d output; then
    mkdir output
fi

if ! test -d "$BOTOCORE_REPO"; then
    git clone -b master https://github.com/boto/botocore.git "$BOTOCORE_REPO"
    sed -i.orig "s/^__version__ = '/__version__ = 'awsipv6-git-/" "$BOTOCORE_REPO/botocore/__init__.py"
else
    ( cd "$BOTOCORE_REPO" && git pull )
fi

python3 -u awsipv6-get.py "$BOTOCORE_REPO" $LIVE_ARG

changes_output="output/changes"
changes_prev=$(mktemp /tmp/awsipv6-changes_prev.XXXXXX)
changes_today=$(mktemp /tmp/awsipv6-changes_today.XXXXXX)
endpoints_text_prev=$(mktemp /tmp/awsipv6-text_prev.XXXXXX)
trap "rm -f $changes_today $changes_prev $text_prev" INT TERM EXIT

today=$(date +%Y-%m-%d)

aws s3 cp "$S3BASE"/changes "$changes_prev"
aws s3 cp "$S3BASE"/endpoints.text "$endpoints_text_prev"

diff -wu0 "$endpoints_text_prev" output/endpoints.text \
    | sed 1,2d \
    | grep -v 'amazonwebservices.com.cn ' \
    | grep '^[-+]' \
    > "$changes_today" \
    || true

: > "$changes_output"
if test -s "$changes_today"; then
    echo "$today" >> "$changes_output"
    cat "$changes_today" >> "$changes_output"
fi
cat "$changes_prev" >> "$changes_output"

python3 -u awsipv6-html.py "$BOTOCORE_REPO" $LIVE_ARG > output/endpoints.html

cp uglyshit.js output/
cp fonts.css output/
cp og-image.png output/
cp robots.txt output/
npx tailwindcss -i uglyshit.css -o output/uglyshit.css

aws s3 sync output/ "$S3BASE"/
