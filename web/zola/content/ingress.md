+++
title = "Ingress"
date = 2025-11-19
updated = 2026-03-08
toc = true
+++

<div class="card">

# Introduction

Ingress traffic refers to all requests initiated by clients, like end user browsers, customer agents or app users.

Since
[around 50%](https://www.google.com/intl/en/ipv6/statistics.html#tab=per-country-ipv6-adoption)
of clients globally now have IPv6 connectivity, it's important offer both IPv4 and IPv6 connectivity for
clients, so they can pick what's best for them. And for many clients, IPv6 offers *lower* latency.

A bonus goal is avoiding the AWS public IPv4 address charges. These charges apply only to dedicated
public IPv4 addresses used exclusively by a single AWS customer, like EC2 instances and Load Balancers.

</div>

<div class="card">

# Ingress Services Overview

The following table lists common AWS services used for ingress and their capabilities regarding
IPv4/IPv6 support:

| Service | No IPv4 address charge | IPv6 Ingress Available | IPv6 to Origin/VPC |
|---------|:------------:|:------------:|:------------------:|
| CloudFront | ✅ | ✅ | ✅ |
| EC2 instances | ❌ | ✅ | ✅ |
| ECS (Fargate/EC2) | ❌ | ✅ | ✅ |
| Elastic Load Balancing (ALB/NLB) | ❌ | ✅ | ✅ |
| Elastic Beanstalk | ✅ | ✅ | ✅ |
| App Runner | ✅ | ✅ | ✅ |
| API Gateway | ✅ | ✅ | ✅ |
| Amplify Hosting | ✅ | ✅ | ❌ |
| AppSync | ✅ | ❌ | ❌ |
| Global Accelerator | ✅ | ✅ | ✅ |
| Lambda Function URLs | ✅ | ✅ | ✅ |
| S3 Website Hosting | ✅ | ❌ | n/a |

*Legend:*
- ✅ = Supported
- ❌ = Not supported

</div>

<div class="card">

# Service Details

## CloudFront

CloudFront supports both IPv4 and IPv6 for viewer requests as well as IPv6 origins. This makes it
perfect to provide both options to clients, while using IPv4 towards the origin, if necessary --
or to *only* use IPv6 towards the origin and save on IPv4 public address charges, for example with
an Application Load Balancer.

## Elastic Load Balancing

Application Load Balancers support IPv6 ingress. Optionally, ALBs even support *IPv6-only* mode,
allowing you to run ALBs without public IPv4 addresses.

## App Runner

App Runner supports both IPv4 and IPv6 for ingress traffic. App Runner also supports both IPv4 and
IPv6 for VPC-internal connectivity, making it a solid choice for IPv6-enabled applications.

Note that as of 2026-03, there's chatter about App Runner being sunset -- but no official word yet.

## Amplify Hosting

As AWS Amplify uses CloudFront under the hood, and always configures it with IPv6, Amplify works nicely.

## S3 Website Hosting

S3 Website Hosting does **not** support IPv6. The S3 website endpoints are IPv4-only. Use Amplify or
CloudFront in front of S3.

</div>

<div class="card">

# Recommendations

To avoid charges for public IPv4 addresses:

- For simple web applications, use **App Runner**: Easy setup with IPv6 support (but see note above)
- For serverless APIs, use **Lambda Function URLs**: Simple serverless APIs, with IPv6 support
- For all other HTTP-based applications, use **ALB in IPv6-only mode** (plus CloudFront to serve IPv4 clients)
- For everything else, consider **Global Accelerator** -- but this probably only makes sense if you're already using it anyway
- In general, when an HTTP-based service (AWS or otherwise) lacks support for IPv6 ingress, CloudFront is an easy fix (and
often a good idea anyway)

</div>

<div class="card">

# Original Blog Post

This page is based on this (old, outdated) blog post: [AWS: Ingress Traffic: Avoiding Public IPv4 Address Charges](https://tty.neveragain.de/2023/10/24/aws-ipv6-ingress.html)

</div>

Recent updates:

- *2026-03-16*: Initial
