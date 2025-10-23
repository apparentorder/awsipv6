#!/bin/sh

set -e

for page in overview regions services matrix changes; do
    python3 "web/build/generate-main-endpoints-${page}.py" "$@"

    # This may be the first time in history that `cat` is used to CONCATENATE files.
    cat \
        web/build/html-start \
        "output/endpoints-${page}-main.html" \
        web/build/html-end \
        > "output/endpoints-$page.html"
done
