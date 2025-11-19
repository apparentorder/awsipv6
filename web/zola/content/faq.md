+++
title = "FAQ"
date = 2025-11-19
updated = 2025-11-19
+++

# Frequently Asked Questions

## This page is work in progress. Maybe in a few weeks?

This page will host FAQs regarding IPv6 support on AWS in general.
It will also cover a few items for this site, mainly regarding the service endpoint data
collection.

## Service API Endpoints: Raw Data

First of all, the raw data is available in several formats:

- {{baselink(filename="endpoints.json.gz", description="JSON (gzip)", download=true)}}
- {{baselink(filename="endpoints.sqlite.gz", description="SQLite (gzip)", download=true)}}
- {{baselink(filename="endpoints.text", description="Plain text")}}

## Service API Endpoints: Notes

- Data is generated almost daily (Tue - Sat) from botocore's `get_available_services()` and
  `create_client()`
- This site has been fully rebuilt in 2025-10; the {{baselink(filename="endpoints.html", description="original endpoints page")}}
  (a massive blob of HTML) is still available and being updated for a while longer
- IPv4 and IPv6 support is determined by DNS only (i.e. if an endpoint returns any AAAA
  records, it is considered IPv6-enabled)
- AWS partitions that are marked as `_UNSUPPORTED_DUALSTACK_PARTITIONS` have been excluded;
  same for partitions that seemingly should have been flagged
  non-dualstack but weren't (`aws-iso-e`, `aws-iso-f`)
- Service APIs that require additional parameters have been excluded (currently only
  `cloudfront-keyvaluestore` and `s3control`)
- Regions that are not available for a service are not checked, according to botocore's
  `get_available_services()` (which seems to be wrong sometimes)
- Non-regionalized services (that have only one partition-wide endpoint, e.g. IAM or
  Route53) are not properly supported yet
- Fun fact: In about 2/3 of regions, there isn't just `s3.$region.amazonaws.com`, but also a
  version with dash, `s3-$region.amazonaws.com`, and that also works. Reasons unknown, but
  the [documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/VirtualHosting.html)
  calls them "legacy endpoints"
- The China regions' DNS resolution has been unreliable for years, at least from both AWS
  eu-central-1 and GitHub runners, so their entries might occasionally "flicker" in the
  data; this affects about a handful of endpoints per week or so. All entries with
  `amazonwebservices.com.cn` or `amazonaws.com.cn` names are therefore excluded when
  generating the list of recent changes.
