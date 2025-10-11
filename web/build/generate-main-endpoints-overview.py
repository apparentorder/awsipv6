import sqlite3

epdb = sqlite3.connect("output/endpoints.sqlite")
epdb.row_factory = sqlite3.Row

cur = epdb.execute("""
    WITH s AS (
        SELECT
            service_name,
            sum(endpoint_default_has_ipv6) as ipv6_default_count,
            sum(endpoint_dualstack_has_ipv6) as ipv6_dualstack_count,
            sum(endpoint_default_has_ipv4) as count_active
        FROM endpoint
        WHERE partition_name = 'aws'
        GROUP BY service_name
    )

    SELECT
        service_name,
        CASE
            WHEN ipv6_default_count > 0 AND ipv6_default_count = count_active THEN 'all_ipv6_default'
            WHEN ipv6_dualstack_count > 0 AND ipv6_dualstack_count = count_active THEN 'all_ipv6_dualstack'
            WHEN ipv6_default_count = 0 AND ipv6_dualstack_count = 0 THEN 'all_ipv4_only'
            ELSE 'mixed'
        END AS category
    FROM s
    WHERE count_active > 0
""")

service_categories = {'all_ipv6_default': 0, 'all_ipv6_dualstack': 0, 'mixed': 0, 'all_ipv4_only': 0}
total_services = 0

for row in cur.fetchall():
    total_services += 1
    service_categories[row['category']] += 1

# Build pie chart. Note: The angles are given as percentages, not degrees.
colors = {
    'all_ipv6_default': 'var(--color-endpoint-ipv6)',
    'all_ipv6_dualstack': 'var(--color-endpoint-ipv6-dualstack)',
    'mixed': 'var(--color-endpoint-mixed)',
    'all_ipv4_only': 'var(--color-endpoint-ipv4)',
}
parts = []
angles = {}
current_angle = 0
cat_count_str = {}
for cat in ['all_ipv6_default', 'all_ipv6_dualstack', 'mixed', 'all_ipv4_only']:
    cat_percent = (service_categories[cat] / total_services) * 100
    parts.append(f'{colors[cat]} {current_angle:.1f}% {current_angle + cat_percent:.1f}%')

    cat_count_str[cat] = f'{service_categories[cat]} service{"" if service_categories[cat] == 1 else "s"} ({cat_percent:.0f}%)'

    current_angle += cat_percent

pie_conic_gradient_str = ", ".join(parts)

# -----

html = f'''
    <div class="flex flex-col md:flex-row gap-4">
        <div class="max-w-prose">
            <p class="text-lg">
                This summary chart shows how many AWS services support IPv6 client applications
                on their public API endpoints, categorized by the mode of IPv6 support and by
                consistency across AWS regions.
            </p>

            <p class="text-sm">
                More detailed data on endpoints is available on the other pages.
            </p>

            <p class="text-sm">
                Additionally, there are resources for IPv6-enabled AWS architectures, like IPv6
                support for IPv6 ingress and egress traffic of key AWS services and other design
                considerations.
            </p>
        </div>

        <div class="pie-chart-container">
            <div class="pie-chart" style="background: conic-gradient({pie_conic_gradient_str});"></div>
        </div>
        <div class="pie-legend">
            <div class="pie-legend-item">
                <span class="pie-legend-color endpoint-ipv6"></span>
                IPv6 by default: {cat_count_str["all_ipv6_default"]}
            </div>
            <div class="pie-legend-item">
                <span class="pie-legend-color endpoint-ipv6-dualstack"></span>
                IPv6 with SDK opt-in: {cat_count_str["all_ipv6_dualstack"]}
            </div>
            <div class="pie-legend-item">
                <span class="pie-legend-color endpoint-mixed"></span>
                Inconsistent across regions: {cat_count_str["mixed"]}
            </div>
            <div class="pie-legend-item">
                <span class="pie-legend-color endpoint-ipv4"></span>
                IPv4 only: {cat_count_str["all_ipv4_only"]}
            </div>
            <div class="text-xs text-gray-400 max-w-prose">
                Services total: {total_services}. Data for AWS commercial regions only, as
                the China / GovCloud / EU Sovereign Cloud partitions have severe differences.
            </div>
        </div>
    </div>
'''

open("output/endpoints-overview-main.html", 'w').write(html)
