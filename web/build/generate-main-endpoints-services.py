#!/usr/bin/env python3

import re
import sqlite3

epdb = sqlite3.connect("output/endpoints.sqlite")
epdb.row_factory = sqlite3.Row

region_count = epdb.execute("SELECT count(*) AS c FROM region").fetchone()["c"]

cur = epdb.execute("""
    SELECT
        service_name,
        sum(endpoint_default_has_ipv6) as ipv6_default_count,
        sum(case when endpoint_dualstack_has_ipv6 and not endpoint_default_has_ipv6 then 1 else 0 end) as ipv6_dualstack_count,
        sum(case when endpoint_default_has_ipv4 and not endpoint_default_has_ipv6 and not endpoint_dualstack_has_ipv6 then 1 else 0 end) as ipv4_count,
        sum(case when endpoint_default_has_ipv4 or endpoint_dualstack_has_ipv4 then 1 else 0 end) as count_active
    FROM endpoint
    GROUP BY service_name
    HAVING count_active
    ORDER BY
        (ipv6_default_count*15 + ipv6_dualstack_count*3 - ipv4_count*7)*100/count_active DESC,
        service_name
""")

html = f'<table class="progress-table">'

for row in cur.fetchall():
    percentages = {}
    for cat in ['ipv6_default', 'ipv6_dualstack', 'ipv4']:
        percentages[cat] = row[f'{cat}_count'] * 100 / region_count

    html += f'''
        <tr class="progress-table-row">
            <td>{row['service_name']}</td>
            <td>
                <div class="progress-bar">
                    <div class="progress-bar-segment endpoint-ipv6" style="width: {percentages['ipv6_default']:.1f}%" title="region count: {row['ipv6_default_count']} ({percentages['ipv6_default']:.1f}%)"></div>
                    <div class="progress-bar-segment endpoint-ipv6-dualstack" style="width: {percentages['ipv6_dualstack']:.1f}%" title="region count: {row['ipv6_dualstack_count']} ({percentages['ipv6_dualstack']:.1f}%)"></div>
                    <div class="progress-bar-segment endpoint-ipv4" style="width: {percentages['ipv4']:.1f}%" title="region count: {row['ipv4_count']} ({percentages['ipv4']:.1f}%)"></div>
                </div>
            </td>
        </tr>
    '''

    service_regions = epdb.execute("""
        SELECT *
        FROM endpoint
        WHERE service_name = ?
        ORDER BY region_name
    """, (row['service_name'],)).fetchall()

    region_class = {}
    for region in service_regions:
        match region:
            case r if r['endpoint_default_has_ipv6']:
                region_class[region['region_name']] = "endpoint-ipv6"
            case r if r['endpoint_dualstack_has_ipv6']:
                region_class[region['region_name']] = "endpoint-ipv6-dualstack"
            case r if r['endpoint_default_has_ipv4'] or r['endpoint_dualstack_has_ipv4']:
                region_class[region['region_name']] = "endpoint-ipv4"
            case _:
                region_class[region['region_name']] = "endpoint-nx"

    html_tooltip = f'''
        <div class="font-semibold">{row['service_name']}</div>

        <div class="flex visible lg:hidden text-xs"> <!-- compact region list for small screens -->
    '''

    for region in service_regions:
        html_tooltip += f'<span class="border p-1 text-nowrap border-gray-500 rounded-sm {region_class[region["region_name"]]}">{region["region_name"]}</span>\n'

    html_tooltip += '''
        </div>

        <div class="hidden lg:block"> <!-- full detail region list for large screens -->
            <table class="text-xs/3 whitespace-nowrap">
                <tr>
                    <th>Region</th>
                    <th>Default endpoint</th>
                    <th>Dual-stack endpoint</th>
                </tr>
    '''

    for region in service_regions:
        class_def = ""
        match region:
            case r if r['endpoint_default_has_ipv6']:
                class_def = "endpoint-ipv6"
            case r if r['endpoint_default_has_ipv4']:
                class_def = "endpoint-ipv4"

        class_ds = ""
        match region:
            case r if r['endpoint_dualstack_has_ipv6']:
                class_ds = "endpoint-ipv6-dualstack"
            case r if r['endpoint_dualstack_has_ipv4']:
                class_ds = "endpoint-ipv4"

        html_tooltip += f'''
        <tr>
            <th>{region['region_name']}</th>
            <td class="endpoint-nx"><code class="{class_def}">{region['endpoint_default_hostname'] or ""}</code></td>
            <td class="endpoint-nx"><code class="{class_ds}">{region['endpoint_dualstack_hostname'] or ""}</code></td>
        </tr>
        '''

    html_tooltip += '</table></div>'

    open(f"output/endpoints-services-tooltip-{row['service_name']}.html", 'w').write(html_tooltip)

html += '</table>\n'

open("output/endpoints-services-main.html", 'w').write(html)
