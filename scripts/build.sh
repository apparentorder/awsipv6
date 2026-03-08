#!/bin/sh
# Build static site (Tailwind, assets, Zola)

set -e

URLBASE="${1:-https://awsipv6.neveragain.de/beta}"

# Build Tailwind CSS
npx tailwindcss -i web/misc/uglyshit.tailwind -o web/zola/static/assets/uglyshit.css

# Copy HTMX
cp node_modules/htmx.org/dist/htmx.min.js web/zola/static/assets/htmx.min.js

# Copy SQLite with workaround for CloudFront compression
cp web/zola/static/endpoints.sqlite web/zola/static/endpoints-matrix/assets/endpoints.sqlite--but.cloudfront.does.not.want.to.compress.binary.data.so.lets.just.call.it.xml

# Copy sql.js
rsync -a --delete node_modules/sql.js/dist/ web/zola/static/endpoints-matrix/assets/sql.js/

# Copy static assets
rsync -a web/misc/static/ web/zola/static/

# Gzip JSON and SQLite for smaller downloads
gzip --best --keep --force web/zola/static/endpoints.sqlite
gzip --best --keep --force web/zola/static/endpoints.json

# Build Zola site
zola --root web/zola build --base-url "$URLBASE" --force
