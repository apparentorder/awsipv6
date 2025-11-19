+++
title = "Introduction"
date = 2025-11-19
updated = 2025-11-19
+++

# AWS IPv6 Information Hub

Welcome, adventurer!

## This page is work in progress. Maybe in a few weeks? ##

## Introduction

The world is finally moving on from IPv4. AWS has started
[charging for public IPv4 addresses](https://aws.amazon.com/blogs/aws/new-aws-public-ipv4-address-charge-public-ip-insights/)
years ago, arguing it would be "accelerating your adoption of IPv6". Each public IPv4 address now has a significant price tag.

Around 50% of all clients globally now have IPv6 connectivity. In many countries,
IPv6 actually reduces latency for end users! ([Google IPv6 statistics](https://www.google.com/intl/en/ipv6/statistics.html#tab=per-country-ipv6-adoption))

IPv4 usually requires NAT, and AWS Managed NAT Gateway's per-gigabyte traffic charges can be very expensive.

IPv6 can bring serious savings, better performance, has no more NAT, no more subnet sizing guesswork,
no more address collisions.

This site provides up-to-date technical information to get you started with
IPv6 on AWS.

## Overview

### IPv6 Connectivity

You will find information on [ingress](@/ingress.md) traffic -- that is, allowing IPv6 clients to
connect to your services.

There is information on [egress](@/egress.md) traffic -- allowing your AWS resources to
connect to AWS and third-party services like Docker Hub using IPv6 (reducing NAT Gateway traffic!).

### AWS SDKs

An introduction to [using the AWS SDKs](@/sdk-programming.md) with IPv6, which isn't as straight-forward
as you'd expect.

### Service API Endpoints

Years ago, this site started as single page providing detailed data on IPv6 support for public AWS service API endpoints.
A modernized version of the original full endpoints matrix is available [here](@/endpoints-matrix.md), in addition
to a new [summary](@/endpoints-services.md) for those endpoints.

## Audience

The information on this site assumes familiarity with IPv6 in general. If you are not familiar with IPv6, check out
[book6](https://github.com/becarpenter/book6/blob/main/Contents.md),
*"a practical introduction to IPv6 for technical people".*
