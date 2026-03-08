#!/bin/sh
# Main update script - calls subscripts for modular execution

set -e

S3BASE="s3://awsipv6/beta"
URLBASE="https://awsipv6.neveragain.de/beta"
LIVE_ARG=""
SKIP_GET=0

# In Ireland. Historic reasons: earlier iteration used DSQL which wasn't available
# in Frankfurt at the time.
export AWS_DEFAULT_REGION=eu-west-1

if test "$1" = "--live"; then
    S3BASE="s3://awsipv6"
    LIVE_ARG="--live"
    URLBASE="https://awsipv6.neveragain.de"
    shift
fi

if test "$1" = "--skip-get"; then
    SKIP_GET=1
    shift
fi

# Step 1: Fetch data (or restore from S3 if skipping)
if test "$SKIP_GET" = 1; then
    echo "Skipping data fetch, restoring from S3..."
    aws s3 cp "$S3BASE"/endpoints.text web/zola/static/endpoints.text
else
    scripts/fetch-data.sh $LIVE_ARG
fi

# Step 2: Generate changes file
changes_output="web/zola/static/changes"
changes_prev=$(mktemp /tmp/awsipv6-changes_prev.XXXXXX)
changes_today=$(mktemp /tmp/awsipv6-changes_today.XXXXXX)
endpoints_text_prev=$(mktemp /tmp/awsipv6-text_prev.XXXXXX)
trap "rm -f $changes_today $changes_prev $endpoints_text_prev" INT TERM EXIT

today=$(date +%Y-%m-%d)

aws s3 cp "$S3BASE"/changes "$changes_prev"
aws s3 cp "$S3BASE"/endpoints.text "$endpoints_text_prev"

diff -wu0 "$endpoints_text_prev" web/zola/static/endpoints.text \
    | sed 1,2d \
    | grep -v 'amazonwebservices.com.cn ' \
    | grep -v 'amazonaws.com.cn ' \
    | grep '^[-+]' \
    > "$changes_today" \
    || true

: > "$changes_output"
if test -s "$changes_today"; then
    echo "$today" >> "$changes_output"
    cat "$changes_today" >> "$changes_output"
fi
cat "$changes_prev" >> "$changes_output"

# Step 3: Generate static files
scripts/generate.sh

# Step 4: Build site
scripts/build.sh "$URLBASE"

# Step 5: Deploy
scripts/deploy.sh "$S3BASE"
