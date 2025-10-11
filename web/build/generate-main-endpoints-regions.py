#!/usr/bin/env python3

import sys
import os
import sqlite3

use_test_data = not "--live" in sys.argv

epdb = sqlite3.connect("output/endpoints.sqlite")
epdb.row_factory = sqlite3.Row

html = ''

# Calculate service categories from database
service_categories = {'fully_ipv6': 0, 'dual_only': 0, 'ipv4_only': 0, 'mixed': 0}

cur = epdb.execute("SELECT DISTINCT service_name FROM endpoint")
services = [row['service_name'] for row in cur.fetchall()]
html = '''
    AWS has 300+ distinct service APIs and 30+ regions. Over 6,000 of
    those combinations are in service. The following table shows each
    service API, per region, by IPv6 support status.

    IPv6-support by default will "just work" (e.g. from an IPv6-only
    VPC). A dualstack endpoint supports IPv6, but requires additional
    configuration. See this blog post for details.

    Only IPv6-by-default services are shown by default. Hover to see a
    endpoint addresses. Data is available as JSON here.
'''

with open("output/endpoints-regions-main.html", 'w') as f:
    f.write(html)
