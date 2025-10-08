#!/usr/bin/env python3

import sys
import os

# Add the update-data directory to the path to import Endpoints
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'update-data'))

from Endpoints import ServiceEndpointsCollection

use_test_data = not "--live" in sys.argv
sec = ServiceEndpointsCollection(use_test_data=use_test_data)
sec.load_json_file(sys.argv[1])

html = '''
        <!doctype html>
        <html lang="en">
            <head>
                <title>AWS service endpoints by region and IPv6 support</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta charset="UTF-8">
                <meta name="twitter:card" content="summary_large_image">
                <meta property="og:title" content="AWS service endpoints by region and IPv6 support">
                <meta name="description" content="A map to quickly identify which AWS services in your region support IPv6 by default and which require using a special dualstack endpoint">
                <meta property="og:description" content="A map to quickly identify which AWS services in your region support IPv6 by default and which require using a special dualstack endpoint">
                <meta property="og:image" content="https://awsipv6.neveragain.de/og-image.png">
                <meta property="og:type" content="website">
                <link rel="stylesheet" href="uglyshit.css">
                <link rel="stylesheet" href="fonts.css">
                <script src="uglyshit.js"></script>
                <script src="htmx.min.js"></script>
            </head>
'''

# Calculate counts per service
service_counts = {}
for ep in sec.endpoints:
    for i in range(60):
        service = f"{ep.service_name}{i}"
        if service not in service_counts:
            service_counts[service] = {'ipv6_default': 0, 'ipv6_dualstack': 0, 'ipv4_only': 0, 'nx': 0}

        if not ep.endpoint_default.hostname and not ep.endpoint_dualstack.hostname:
            service_counts[service]['nx'] += 1 + i
        elif ep.endpoint_default.has_ipv6:
            service_counts[service]['ipv6_default'] += 1 + i
        elif ep.endpoint_dualstack.has_ipv6:
            service_counts[service]['ipv6_dualstack'] += 1 + i
        else:
            service_counts[service]['ipv4_only'] += 1 + i

# Sort services by IPv6 default (desc), dualstack (desc), IPv4 only (desc), then name (asc)
def sort_key(service):
    counts = service_counts[service]
    return (-counts['ipv6_default'], -counts['ipv6_dualstack'], -counts['ipv4_only'], service)

html += '<main>\n'
html += '<ul class="bubble-list">\n'
for service in sorted(service_counts.keys(), key=sort_key):
    counts = service_counts[service]
    total = counts['ipv6_default'] + counts['ipv6_dualstack'] + counts['ipv4_only'] + counts['nx']

    if total == 0:
        continue

    ipv6_default_pct = (counts['ipv6_default'] / total) * 100
    ipv6_dualstack_pct = (counts['ipv6_dualstack'] / total) * 100
    ipv4_only_pct = (counts['ipv4_only'] / total) * 100
    nx_pct = (counts['nx'] / total) * 100

    # Calculate dynamic width based on service name length
    base_width = 60
    char_width = 8  # approximate pixels per character
    dynamic_width = max(base_width, len(service) * char_width + 20)  # +20 for padding

    html += f'''
        <li class="bubble-item">
            <div class="bubble-container" style="width: {dynamic_width}px">
                <div class="bubble-segment endpoint-ipv6" style="width: {ipv6_default_pct:.1f}%"></div>
                <div class="bubble-segment endpoint-ipv6-dualstack" style="width: {ipv6_dualstack_pct:.1f}%"></div>
                <div class="bubble-segment endpoint-ipv4" style="width: {ipv4_only_pct:.1f}%"></div>
                <div class="bubble-segment endpoint-nx" style="width: {nx_pct:.1f}%"></div>
                <span class="bubble-label">{service}</span>
            </div>
        </li>
    '''

html += '</ul>\n'
html += '</main>'

with open("output/endpoints-overview.html", 'w') as f:
    f.write(html)
