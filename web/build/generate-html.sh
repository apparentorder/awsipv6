#!/bin/sh

set -e

page_list="
    intro
    ingress
    egress
    sdk-programming
    faq

    endpoints-overview
    endpoints-regions
    endpoints-services
    endpoints-matrix
    endpoints-changes
"

for page in $page_list; do
    python3 "web/build/generate-main-endpoints-${page}.py" "$@"

    # This may be the first time in history that `cat` is used to CONCATENATE files.
    cat \
        web/build/html-start \
        "output/endpoints-${page}-main.html" \
        web/build/html-end \
        > "output/endpoints-$page.html"
done
