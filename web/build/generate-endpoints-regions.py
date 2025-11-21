#!/usr/bin/env python3

import os
import re
import sqlite3

epdb = sqlite3.connect("web/zola/static/endpoints.sqlite")
epdb.row_factory = sqlite3.Row

cur = epdb.execute("""
    SELECT
        r.partition_name,
        r.region_name as region_name,
        r.description as region_description,
        sum(endpoint_default_has_ipv6) as ipv6_default_count,
        sum(case when endpoint_dualstack_has_ipv6 and not endpoint_default_has_ipv6 then 1 else 0 end) as ipv6_dualstack_count,
        sum(case when endpoint_default_has_ipv4 and not endpoint_default_has_ipv6 and not endpoint_dualstack_has_ipv6 then 1 else 0 end) as ipv4_count
    FROM endpoint e
    LEFT JOIN region r ON e.region_name = r.region_name
    GROUP BY r.partition_name, r.region_name, region_description
    ORDER BY
        region_name
""")

count_all = epdb.execute("SELECT COUNT(DISTINCT service_name) FROM ENDPOINT").fetchone()[0];

html = f'''
    <!-- file: {os.path.basename(__file__)} -->
    <table class="progress-table font-light">
        <thead>
            <tr class="text-left">
                <th>Region</th>
                <th>IPv6 support per service &mdash; by default / opt-in / ipv4-only</th>
            </tr>
        </thead>

        <tbody>
'''

for row in cur.fetchall():
    region_description = row['region_description']
    if match := re.match(r'.*\((.*)\)', region_description):
        region_description = match.group(1)

    region_name = f'{row['region_name']} ({region_description})'

    percentages = {}
    for cat in ['ipv6_default', 'ipv6_dualstack', 'ipv4']:
        percentages[cat] = row[f'{cat}_count'] * 100 / count_all

    # percentages["nx"] = 100 - sum(percentages.values())

    html += f'''
        <tr class="progress-table-row">
            <td>{region_name}</td>
            <td class="progress-table-cell">
                <div class="progress-bar">
                    <div class="progress-bar-segment endpoint-ipv6" style="width: {percentages['ipv6_default']:.1f}%" title="service count ipv6-default: {row['ipv6_default_count']} ({percentages['ipv6_default']:.1f}%)"></div>
                    <div class="progress-bar-segment endpoint-ipv6-dualstack" style="width: {percentages['ipv6_dualstack']:.1f}%" title="service count ipv6-opt-in: {row['ipv6_dualstack_count']} ({percentages['ipv6_dualstack']:.1f}%)"></div>
                    <div class="progress-bar-segment endpoint-ipv4" style="width: {percentages['ipv4']:.1f}%" title="service count ipv4-only: {row['ipv4_count']} ({percentages['ipv4']:.1f}%)"></div>
                </div>
            </td>
        </tr>
    '''

html += '</table>\n'

open("web/zola/generated/endpoints-regions.html", 'w').write(html)
