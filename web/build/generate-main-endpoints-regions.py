#!/usr/bin/env python3

import re
import sqlite3

epdb = sqlite3.connect("output/endpoints.sqlite")
epdb.row_factory = sqlite3.Row

cur = epdb.execute("""
    SELECT
        region_name,
        (select description from region r where r.region_name = endpoint.region_name) as region_description,
        sum(endpoint_default_has_ipv6) as ipv6_default_count,
        sum(case when endpoint_dualstack_has_ipv6 and not endpoint_default_has_ipv6 then 1 else 0 end) as ipv6_dualstack_count,
        sum(case when endpoint_default_has_ipv4 and not endpoint_default_has_ipv6 and not endpoint_dualstack_has_ipv6 then 1 else 0 end) as ipv4_count,
        sum(case when endpoint_default_has_ipv4 or endpoint_dualstack_has_ipv4 then 1 else 0 end) as count_all
    FROM endpoint
    GROUP BY region_name
    HAVING count_all > 0
    ORDER BY
        (ipv6_default_count*5 + ipv6_dualstack_count*3 - ipv4_count*10)*100/count_all DESC
        -- ipv4_count*100/count_all ASC,
        -- ipv6_default_count*100/count_all DESC
""")

    # ORDER BY (sum(endpoint_default_has_ipv6) * 100.0 / sum(case when endpoint_default_has_ipv4 then 1 else 0 end)) DESC,
    #          (sum(case when endpoint_dualstack_has_ipv6 and not endpoint_default_has_ipv6 then 1 else 0 end) * 100.0 / sum(case when endpoint_default_has_ipv4 then 1 else 0 end)) DESC
html = f'<table class="progress-table">'

for row in cur.fetchall():
    region_description = row['region_description']
    if match := re.match(r'.*\((.*)\)', region_description):
        region_description = match.group(1)

    region_name = f'{row['region_name']} ({region_description})'

    percentages = {}
    for cat in ['ipv6_default', 'ipv6_dualstack', 'ipv4']:
        percentages[cat] = row[f'{cat}_count'] * 100 / row['count_all']

    html += f'''
        <tr>
            <td>{region_name}</td>
            <td>
                <div class="progress-bar">
                    <div class="progress-bar-segment endpoint-ipv6" style="width: {percentages['ipv6_default']:.1f}%" title="service count: {row['ipv6_default_count']} ({percentages['ipv6_default']:.1f}%)"></div>
                    <div class="progress-bar-segment endpoint-ipv6-dualstack" style="width: {percentages['ipv6_dualstack']:.1f}%" title="service count: {row['ipv6_dualstack_count']} ({percentages['ipv6_dualstack']:.1f}%)"></div>
                    <div class="progress-bar-segment endpoint-ipv4" style="width: {percentages['ipv4']:.1f}%" title="service count: {row['ipv4_count']} ({percentages['ipv4']:.1f}%)"></div>
                </div>
            </td>
        </tr>
    '''

html += '</table>\n'

open("output/endpoints-regions-main.html", 'w').write(html)
