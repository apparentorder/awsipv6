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
    sed -i "s/^__version__ = '/__version__ = 'awsipv6-git-/" "$BOTOCORE_REPO/botocore/__init__.py"
else
    ( cd "$BOTOCORE_REPO" && git pull )
fi

python3 awsipv6-get.py "$BOTOCORE_REPO" $LIVE_ARG

changes="output/changes"
changes_today=$(mktemp /tmp/awsipv6-changes_today.XXXXXX)
text_prev=$(mktemp /tmp/awsipv6-text_prev.XXXXXX)
trap "rm -f $changes_today $text_prev" SIGINT SIGTERM EXIT

today=$(date +%Y-%m-%d)

aws s3 cp "$S3BASE"/changes "$changes"
aws s3 cp "$S3BASE"/endpoints.text "$text_prev"

diff -wu0 "$text_prev" output/endpoints.text > "$changes_today" || true

if test -s "$changes_today"; then
    # write complete history to changes_today, beginning with today's changes
    echo "$today" > "$changes_today"
    (
        diff -wu0 "$text_prev" output/endpoints.text \
        | sed 1,2d \
        | grep '^[-+]'
    ) >> "$changes_today"
    cat "$changes" >> "$changes_today"
    mv "$changes_today" "$changes"
    
    aws s3 cp "$changes" "$S3BASE"/changes
fi

python3 awsipv6-html.py "$BOTOCORE_REPO" $LIVE_ARG > output/endpoints.html

cp uglyshit.js  output/
cp fonts.css  output/
npx tailwindcss -i uglyshit.css -o output/uglyshit.css

aws s3 sync output/ "$S3BASE"/
