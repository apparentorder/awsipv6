#!/bin/sh
# Deploy to S3

set -e

S3BASE="${1:-s3://awsipv6/beta}"

aws s3 sync web/zola/public/ "$S3BASE"/
