+++
title = "Introduction"
+++

# AWS Services IPv6 Support Information

Welcome, adventurer!

**This page is work in progress. Maybe in a few weeks?**

This site is an information hub for all things IPv6 on Amazon Web Services (AWS).

It assumes familiarity with IPv6 basics and focuses on AWS-specific details. For an introduction to
IPv6 networking, please see FIXME.

You will find information on [ingress](@/ingress.md) traffic — that is, for incoming requests
from clients. Around 50% of clients globally have IPv6 connectivity, with more than 75% in some advanced countries.
In many countries, IPv6 actually reduces latency for the end user by 10 milliseconds or more!
For detailed data, see
[Google's IPv6 statistics](https://www.google.com/intl/en/ipv6/statistics.html#tab=per-country-ipv6-adoption).

There is also information on [egress](@/egress.md) traffic — implementing IPv6 connectivity
for resources in AWS VPCs, so they can connect to the outside world using IPv6, including other AWS services.
One key advantage is that IPv6 egress does not require NAT, so there is no Managed NAT Gateway tax on this traffic.

Closely related to egress is some information on [programming the AWS SDKs](@/sdk-programming.md).
Contrary to what you'd expect, making custom AWS programs like Lambda functions use IPv6 to call other
AWS services doesn't "just work" in most cases, but requires careful consideration and configuration opt-in,
which is pretty unique behavior in this world.

... separate 'p' on IPv4 address tax ...
