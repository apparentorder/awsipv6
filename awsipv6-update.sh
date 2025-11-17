#!/bin/sh

set -e

BOTOCORE_REPO=~/environment/botocore
S3BASE="s3://awsipv6/beta"
URLBASE="https://awsipv6.neveragain.de/beta"
CDK_DSQL_STACK_NAME="Awsipv6BetaStack"
CDK_STACK_TO_DEPLOY="Awsipv6BetaStack"
LIVE_ARG=""
SKIP_GET=0
export AWS_DEFAULT_REGION=eu-west-1

if test "$1" = "--live"; then
    S3BASE="s3://awsipv6"
    LIVE_ARG="--live"
    CDK_DSQL_STACK_NAME="Awsipv6Stack"
    CDK_STACK_TO_DEPLOY="--all"
    URLBASE="https://awsipv6.neveragain.de"
    shift
fi

if test "$1" = "--skip-get"; then
    SKIP_GET=1
    shift
fi

if test "$SKIP_GET" = 1; then
    # Keep previous change list if we do not collect new data.
    aws s3 cp "$S3BASE"/endpoints.text output/endpoints.text
else
    rm -rf output
    mkdir output
    mkdir output/assets
    mkdir output/endpoints-matrix
    mkdir output/endpoints-matrix/assets

    if ! test -d "$BOTOCORE_REPO"; then
        git clone -b master https://github.com/boto/botocore.git "$BOTOCORE_REPO"
        sed -i.orig "s/^__version__ = '/__version__ = 'awsipv6-git-/" "$BOTOCORE_REPO/botocore/__init__.py"
    else
        ( cd "$BOTOCORE_REPO" && git pull )
    fi

    export DSQL_ENDPOINT=$(
        aws cloudformation describe-stacks --stack-name "$CDK_DSQL_STACK_NAME" \
        | jq -j '.Stacks[].Outputs[] | select(.OutputKey == "DsqlClusterEndpoint") | .OutputValue'
    )
    python3 -u update-data/awsipv6-get.py "$BOTOCORE_REPO" $LIVE_ARG
fi

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

if test "$SKIP_GET" -ne 1; then
    python3 -u update-data/awsipv6-html.py "$BOTOCORE_REPO" $LIVE_ARG > output/endpoints.html
fi

if ! test -d web/zola/generated; then
    mkdir web/zola/generated
fi

if ! test -d output/endpoints-services; then
    mkdir output/endpoints-services
fi

for f in web/build/generate*py; do
    python3 $f
done

npx tailwindcss -i web/uglyshit.tailwind -o output/assets/uglyshit.css

zola --root web/zola build --output-dir tmp-zola-build --base-url "$URLBASE" --force
rsync -a tmp-zola-build/ output/

# provide .gz versions for smaller downloads
gzip --best --keep --force output/endpoints.sqlite
gzip --best --keep --force output/endpoints.json

cp node_modules/htmx.org/dist/htmx.min.js output/assets/htmx.min.js

cp web/zola/static/assets/endpoints-matrix.js output/endpoints-matrix/assets/
cp output/endpoints.sqlite output/endpoints-matrix/assets/endpoints.sqlite--but.cloudfront.does.not.want.to.compress.binary.data.so.lets.just.call.it.xml
rsync -a --delete node_modules/sql.js/dist/ output/endpoints-matrix/assets/sql.js/

aws s3 sync --delete output/ "$S3BASE"/
#aws s3 sync web/static/ "$S3BASE"/

npx cdk diff   $CDK_STACK_TO_DEPLOY --app "python3 awsipv6-cdk.py"
npx cdk deploy $CDK_STACK_TO_DEPLOY --app "python3 awsipv6-cdk.py"
