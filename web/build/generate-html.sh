#!/bin/sh

python3 web/build/generate-main-endpoints-overview.py "$@"
python3 web/build/generate-main-endpoints-services.py "$@"
python3 web/build/generate-main-endpoints-regions.py "$@"

for page in overview regions services; do
    # This may be the first time in history that `cat` is used to CONCATENATE files.
    cat \
        web/build/html-start \
        "output/endpoints-${page}-main.html" \
        web/build/html-end \
        > "output/endpoints-$page.html"
done