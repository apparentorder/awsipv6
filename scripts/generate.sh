#!/bin/sh
# Generate static files from data

set -e

# Create directories
for dir in \
    web/zola/generated \
    web/zola/static/assets \
    web/zola/static/endpoints-matrix/assets \
    web/zola/static/endpoints-services/assets; do

    if ! test -d "$dir"; then
        mkdir -p "$dir"
    fi
done

# Run all generate-*.py scripts
for f in web/build/generate*py; do
    python3 $f
done
