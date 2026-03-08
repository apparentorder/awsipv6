#!/bin/sh
# Generate subsetted Amazon Ember fonts for the website
# Run this script when updating fonts: bash scripts/subset-fonts.sh

set -e

# Install fonttools if needed
pip install -q fonttools brotli

# Download from
# https://developer.amazon.com/en-US/alexa/branding/echo-guidelines/identity-guidelines/typography
# Per Usage Guidelines: "To include these designs in your work there are no licenses payments,
# no royalties, no copyright or attribution notices required."
FONT_DIR="Amazon_Typefaces_Complete_Font_Set_Mar2020/Ember"
OUTPUT_DIR="web/misc/static/assets"

# Characters needed for the website (basic Latin + Latin extended)
# Format: use hex strings without 'U+' prefix for ranges
UNICODES="0020-007E,00A0-00FF,0100-017F,0180-024F"

echo "Generating subsetted Amazon Ember fonts..."

# Regular (400)
pyftsubset "$FONT_DIR/AmazonEmber_Rg.ttf" \
    --flavor=woff2 \
    --layout-features='*' \
    --unicodes="$UNICODES" \
    --output-file="$OUTPUT_DIR/ember-rg.woff2"

# Italic (400)
pyftsubset "$FONT_DIR/AmazonEmber_RgIt.ttf" \
    --flavor=woff2 \
    --layout-features='*' \
    --unicodes="$UNICODES" \
    --output-file="$OUTPUT_DIR/ember-rg-it.woff2"

# Bold (700)
pyftsubset "$FONT_DIR/AmazonEmber_Bd.ttf" \
    --flavor=woff2 \
    --layout-features='*' \
    --unicodes="$UNICODES" \
    --output-file="$OUTPUT_DIR/ember-bd.woff2"

# Bold Italic (700)
pyftsubset "$FONT_DIR/AmazonEmber_BdIt.ttf" \
    --flavor=woff2 \
    --layout-features='*' \
    --unicodes="$UNICODES" \
    --output-file="$OUTPUT_DIR/ember-bd-it.woff2"

echo "Done! Subsetted fonts saved to $OUTPUT_DIR/"
ls -la "$OUTPUT_DIR"/ember-*.woff2
