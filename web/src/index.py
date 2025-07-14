import psycopg
import json
import os
import re
import html
import boto3

DEFAULT_REGION_SELECTION = sorted([
    # default region selection
    "ap-northeast-1",
    "ap-southeast-1",
    "ca-central-1",
    "cn-north-1",
    "eu-central-1",
    "eu-west-1",
    "eusc-de-east-1",
    "us-east-1",
    "us-east-2",
    "us-gov-west-1",
])

dsql_client = boto3.client('dsql')
dsql_connection = None

def dsql_connect():
    dsql_token = dsql_client.generate_db_connect_auth_token(Hostname = os.environ.get('DSQL_ENDPOINT'))
    return psycopg.connect(
        host = os.environ.get('DSQL_ENDPOINT'),
        dbname = 'postgres',
        user = 'be_read',
        password = dsql_token,
        sslmode = 'require',
        sslnegotiation = "direct",
        row_factory = psycopg.rows.namedtuple_row,
        autocommit = True, # psycopg would leave idle transactions open even for read queries (and we don't write)
    )

def dsql_execute(query, params = None):
    global dsql_connection
    if dsql_connection is None:
        dsql_connection = dsql_connect()

    try:
        #with dsql_connection.transaction():
        return dsql_connection.execute(query, params, prepare = True)
    except psycopg.OperationalError as e:
        print(f"Database connection error: {e}")
        print(f"Attempting reconnect")
        dsql_connection.close()
        dsql_connection = dsql_connect()
        #with dsql_connection.transaction():
        return dsql_connection.execute(query, params, prepare = True)

all_regions_query = """
    SELECT region_name, partition_name, description
    FROM region
    ORDER BY region_name
"""
all_regions = dsql_execute(all_regions_query).fetchall()

def get_stats(event):
    stats_query = """
        SELECT
            COUNT(*) AS count_total,
            SUM(CASE WHEN endpoint_default_has_ipv6 THEN 1 ELSE 0 END) AS count_ipv6_default,
            SUM(CASE WHEN endpoint_dualstack_has_ipv6 AND NOT endpoint_default_has_ipv6 THEN 1 ELSE 0 END) AS count_ipv6_dualstack,
            SUM(CASE WHEN NOT endpoint_default_has_ipv6 AND NOT endpoint_dualstack_has_ipv6 THEN 1 ELSE 0 END) AS count_ipv4_only
        FROM endpoint
        WHERE endpoint_default_hostname IS NOT NULL
    """

    stats_row = dsql_execute(stats_query).fetchone()
    ipv6_default_p = int(stats_row.count_ipv6_default * 100 / stats_row.count_total)
    ipv6_dualstack_p = int(stats_row.count_ipv6_dualstack * 100 / stats_row.count_total)
    ipv4_only_p = int(stats_row.count_ipv4_only * 100 / stats_row.count_total)

    accept_header = event.get("headers", {}).get("accept", "")
    if "application/json" in accept_header:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "ipv6_default_percentage": ipv6_default_p,
                "ipv6_dualstack_percentage": ipv6_dualstack_p,
                "ipv4_only_percentage": ipv4_only_p,
            }),
        }

    body = f"""
        <div id="ipv6-color-stats" class="text-sm max-w-prose">
        <strong>The table is color-coded:</strong>
        <table class="">
            <tr>
            <td class="p-1 endpoint-ipv6">IPv6 by default</td>
            <td class="p-1 endpoint-ipv6 text-xl font-light">{ipv6_default_p}%</td>
            </tr>
            <tr>
            <td class="p-1 endpoint-ipv6-dualstack">IPv6 "dualstack"</td>
            <td class="p-1 endpoint-ipv6-dualstack text-xl font-light">{ipv6_dualstack_p}%</td>
            </tr>
            <tr>
            <td class="p-1 endpoint-ipv4">IPv4 only</td>
            <td class="p-1 endpoint-ipv4 text-xl font-light">{ipv4_only_p}%</td>
            </tr>
        </table>
    </div>
    """

    return body

def get_table_data(event, region_list_from_user, html_only = False):
    query = """
        SELECT *
        FROM endpoint
        WHERE region_name = ANY(%s)
        AND (endpoint_default_hostname IS NOT NULL OR endpoint_dualstack_hostname IS NOT NULL)
    """
    query_parameters = [region_list_from_user]

    if filter_service := event.get("queryStringParameters", {}).get("filter-service", "").strip().lower():
        query += " AND position(%s in service_name) > 0"
        query_parameters += [filter_service]

    filter_class = event.get("queryStringParameters", {}).get("filter-class", "ipv6").strip().lower()
    if filter_class == "ipv6":
        query += " AND endpoint_default_has_ipv6"
    elif filter_class == "ipv6-dualstack":
        query += " AND (endpoint_dualstack_has_ipv6 OR endpoint_default_has_ipv6)"

    endpoint_rows = dsql_execute(query, query_parameters).fetchall()

    endpoints = {}
    for row in endpoint_rows:
        endpoints[row.service_name] = endpoints.get(row.service_name, {})
        endpoints[row.service_name][row.region_name] = row

    region_headers_html = "\n".join(
        f'<th style="" class="data-region-{region_name} p-1 border-l border-gray-500 border-dotted">{region_name}</th>'
        for region_name in region_list_from_user
    )

    service_rows_html = ""
    for service_name in sorted(endpoints.keys()):
        service_rows_html += f"""
            <tr class="service-row data-service-{service_name} border-b border-gray-500 border-dotted">
                <th class="service-name pr-1">{service_name}</th>
        """

        for region_name in region_list_from_user:
            if region_name not in endpoints[service_name]:
                service_rows_html += f"""
                    <td class="border-l border-gray-500 border-dotted data-region-{region_name} data-service-{service_name} service-endpoints endpoint-nx">
                    </td>
                """
                continue

            endpoint_class = "endpoint-nx"
            if endpoints[service_name][region_name].endpoint_default_has_ipv6:
                endpoint_class = "endpoint-ipv6"
            elif endpoints[service_name][region_name].endpoint_dualstack_has_ipv6:
                endpoint_class = "endpoint-ipv6-dualstack"
            elif endpoints[service_name][region_name].endpoint_default_has_ipv4:
                endpoint_class = "endpoint-ipv4"

            endpoint_default_html = ""
            if endpoints[service_name][region_name].endpoint_default_hostname:
                protocols = []
                protocols += ["ipv4"] if endpoints[service_name][region_name].endpoint_default_has_ipv4 else []
                protocols += ["ipv6"] if endpoints[service_name][region_name].endpoint_default_has_ipv6 else []
                protocols_s = f"[{', '.join(protocols)}]"

                endpoint_default_html = f"""
                    <div class="has-tooltip">
                        default
                        <span class="tooltip rounded shadow-lg p-1 bg-gray-100 -mt-8">
                            {endpoints[service_name][region_name].endpoint_default_hostname} {protocols_s}
                        </span>
                    </div>
                """

            endpoint_dualstack_html = ""
            if endpoints[service_name][region_name].endpoint_dualstack_hostname:
                protocols = []
                protocols += ["ipv4"] if endpoints[service_name][region_name].endpoint_dualstack_has_ipv4 else []
                protocols += ["ipv6"] if endpoints[service_name][region_name].endpoint_dualstack_has_ipv6 else []
                protocols_s = f"[{', '.join(protocols)}]"

                endpoint_dualstack_html = f"""
                    <div class="has-tooltip">
                        dualstack
                        <span class="tooltip rounded shadow-lg p-1 bg-gray-100 -mt-8">
                            {endpoints[service_name][region_name].endpoint_dualstack_hostname} {protocols_s}
                        </span>
                    </div>
                """

            service_rows_html += f"""
                <td class="border-l border-gray-500 border-dotted data-region-{region_name} data-service-{service_name} service-endpoints {endpoint_class}">
                    {endpoint_default_html}
                    {endpoint_dualstack_html}
                </td>
            """

        service_rows_html += "</tr>\n"

    body = f"""
        <table id="table-data" class="text-center text-sm font-light flex-col">
            <thead class="border-b border-gray-500 border-dotted font-medium">
                <tr>
                    <th>Service</th>
                    {region_headers_html}
                </tr>
            </thead>
            <tbody class="flex-1">
                {service_rows_html}
            </tbody>
        </table>
    """

    if html_only:
        return body

    cookies = (
        [f'regions={",".join(region_list_from_user)}; Path=/; HttpOnly; SameSite=Strict']
        if len(region_list_from_user) > 0 and region_list_from_user != DEFAULT_REGION_SELECTION else []
    )

    return {
        "statusCode": 200,
        "body": body,
        "headers": {"Content-Type": "text/html"},
        "cookies": cookies,
    }

def get_region_selection_html(event, region_list_from_user):
    global all_regions

    body = "\n".join(
        f"""
            <label for="regions-{region.region_name}" class="flex items-center space-x-1 text-xs">
                <input
                    type="checkbox"
                    id="regions-{region.region_name}"
                    name="regions"
                    value="{region.region_name}"
                    class="form-checkbox"
                    {"checked" if region.region_name in region_list_from_user else ""}
                >
                    <span>{region.region_name} ({region.description})</span>
            </label>
        """
        for region in all_regions
    )

    return body

def get_changes_list_html(event):
    body = ""

    with open(".generated-endpoint-changes.text") as f:
        data_tags_open = False
        date_count = 0
        for line in f.readlines():
            if re.match(r'^\d', line):
                if data_tags_open:
                    body += '</ul>'
                    data_tags_open = False

                # new date
                date_count += 1
                if date_count > 30:
                    break

                body += f'<div id="changes-date-{line}" class="text-xs space-y-1">{line}</div>'
                body += f'<ul id="changes-data-{line}" class="text-xs">'
                data_tags_open = True

            else:
                line = re.sub(r'^(.)', r'\1 ', line) # add space
                body += f'<li><code>{html.escape(line)}</code></li>'

    body += '</ul>'

    return body

def get_main(event, region_list_from_user):
    body = f"""
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
                <meta property="og:image" content="https://awsipv6.s3.eu-central-1.amazonaws.com/og-image.png">
                <meta property="og:type" content="website">
                <link rel="stylesheet" href="uglyshit.css">
                <link rel="stylesheet" href="fonts.css">
                <script src="uglyshit.js"></script>
                <script src="htmx.min.js"></script>
            </head>

            <body>
            <div id="intro-and-stats" class="p-4">
                <div id="intro" class="grid md:grid-cols-2">
                    <div id="intro-text" class="space-y-2 text-sm max-w-prose">
                        <h2 class="text-xl font-bold">
                            AWS service endpoints by region and IPv6 support
                        </h2>
                        <p>
                            AWS has 300+ distinct service APIs and 30+ regions. Over 6,000 of those combinations
                            are in service.
                            The following table shows each service API, per region, by IPv6 support status.
                        </p>
                        <p class="font-light">
                            IPv6-support <strong>by default</strong> will "just work" (e.g. from an IPv6-only VPC).
                            A <strong>dualstack endpoint</strong> supports IPv6, but requires additional configuration.
                            See this <a href="https://tty.neveragain.de/2024/05/20/aws-ipv6-egress.html">blog post</a>
                            for details.
                        </p>
                        <p class="font-light">
                            <strong>Only IPv6-by-default services are shown by default.</strong>
                            Hover to see a endpoint addresses. Data is available as JSON <a href="endpoints.json">here</a>.
                        </p>
                    </div>
                    {get_stats(event)}
                </div>
            </div>

            <div id="everything" class="border-t flex">
                <div id="settings" class="p-4 w-64 flex-initial space-y-4 bg-gray-100 border-r-2">
                    <!--
                        the small hx-trigger delay for 'regions' is to avoid request flooding
                        due to the 'Select/Clear all' buttons (throttling doesn't seem to work reliably)
                    -->
                    <form
                        id="settings-form"
                        hx-get="awsipv6-endpoints"
                        hx-target="#table-data"
                        hx-trigger="
                            change delay:10ms from:input[name='regions'],
                            change from:input[name='filter-class'],
                            keyup delay:500ms from:input[name='filter-service']
                        "
                        hx-sync="this:replace"
                    >
                        <div class="pb-3">
                            <label for="filter-service"><strong>Filter services:</strong></label>
                            <input
                                type="text"
                                name="filter-service"
                                id="filter-service"
                                autofocus
                                pattern="[a-z0-9]*"
                                class="w-full px-1 border-1 bg-white rounded border-1"
                                onkeydown="if (event.key === 'Escape') event.target.value = '';"
                                onkeyup="removeEndpointClassFilter()"
                            >
                        </div>

                        <div class="pb-3">
                            <label><strong>Select endpoints:</strong></label>

                            <div class="text-sm">
                                <div>
                                    <input type="radio" name="filter-class" id="class-ipv6only" value="ipv6" checked="default">
                                    <label for="class-ipv6only">IPv6 (by default) only</label>
                                </div>

                                <div>
                                    <input type="radio" name="filter-class" id="class-ipv6dualstack" value="ipv6-dualstack">
                                    <label for="class-ipv6dualstack">IPv6 (default or dualstack)</label>
                                </div>

                                <div>
                                    <input type="radio" name="filter-class" id="class-all" value="all">
                                    <label for="class-all">All endpoints</label>
                                </div>
                            </div>
                        </div>

                        <div class="pb-3">
                            <label><strong>Select regions:</strong></label>
                            <div class="pb-2">
                                <input
                                    type="text"
                                    id="region-search"
                                    placeholder="Click to select & search"
                                    class="w-full px-1 border rounded bg-white"
                                    onkeydown="if (event.key === 'Escape') event.target.value = '';"
                                    onkeyup="filterRegions()"
                                    onfocus="document.getElementById('region-checkboxes').classList.remove('hidden')"
                                >
                            </div>
                            <div id="region-checkboxes" class="hidden">
                                <div class="pb-2 flex-row">
                                    <!--
                                        The "Select all" button isn't useful on Live, as it explodes the Lambda
                                        payload limit when selecting all endpoints. Hide it.
                                    -->
                                    <button
                                        type="button"
                                        class="rounded bg-white border-1 text-sm hidden"
                                        onclick="setAllRegionsChecked(true)"
                                    >
                                        <span class="mx-2">Select all</span>
                                    </button>
                                    <button
                                        type="button"
                                        class="rounded bg-white border-1 text-sm"
                                        onclick="setAllRegionsChecked(false)"
                                    >
                                        <span class="mx-2">Clear all</span>
                                    </button>
                                </div>
                                {get_region_selection_html(event, region_list_from_user = region_list_from_user)}
                                <div class="text-xs text-gray-500 mt-1">Check one or more regions from the list.</div>
                            </div>
                        </div>
                    </form>
                </div>
                <div id="main-content" class="p-2 text-xs">
                    {get_table_data(event, html_only = True, region_list_from_user = region_list_from_user)}
                </div>
            </div>

            <div id="changes" class="p-2 border-t space-y-2">
                <h4 class="text-xl">Recent changes</h4>
                <div id="changes-explain" class="text-sm">
                    Endpoints with a <code>+</code> have been added.<br>
                    Endpoints with a <code>-</code> have been removed.
                </div>
                {get_changes_list_html(event)}
            </div>

            <div id="outro" class="p-2 border-t space-y-4">
                <div id="details">
                    The details:
                    <ul class="list-disc pl-6 text-xs max-w-prose">

                        <li>This list is generated almost daily (Tue - Sat) from botocore's <code>get_available_services()</code> and <code>create_client()</code></li>
                        <li>This page is a new dynamic interface introduced in 2025-07; the  <a href="endpoints.html">old page</a> (a massive blob of HTML) is still available and being updated for a while longer</li>
                        <li>Selected regions will be remembered when this page is opened the next time (using a cookie)</li>
                        <li>The backend Lambda function will explode when selecting <i>all</i> services <i>and</i> too many regions, due to Lambda response size limits; this error isn't handled properly yet</li>
                        <li>IPv4 and IPv6 support is determined by DNS only (i.e. if an endpoint returns any AAAA records, it is considered IPv6-enabled)</li>
                        <li>AWS partitions that are marked as <code>_UNSUPPORTED_DUALSTACK_PARTITIONS</code> have been excluded; same for partitions that seemingly should have been flagged non-dualstack but weren't (<code>aws-iso-e</code>, <code>aws-iso-f</code>)</li>
                        <li>Service APIs that require additional parameters have been excluded (currently only <code>cloudfront-keyvaluestore</code> and <code>s3control</code>)</li>
                        <li>Regions that are not available for a service are not checked, according to botocore's <code>get_available_services()</code> (which seems to be wrong sometimes)</li>
                        <li>Non-regionalized services (that have only one partition-wide endpoint, i.e. IAM or Route53) are not properly supported yet</li>
                        <li>Percentages in the table at the top are based on the count of service-region endpoints that are actually available; that's more than 6.000 endpoints,
                                btw, while the total number of service/region combinations is more than 9.000</li>
                        <li>Fun fact: In about 2/3 of regions, there isn't just <code>s3.$region.amazonaws.com</code>, but also a version with dash, <code>s3-$region.amazonaws.com</code>,
                                and that also works. Reasons unknown.</li>
                        <li>The China regions' DNS resolution has been unreliable for years, at least from both AWS eu-central-1 and Github runners, so their
                                entries might occasionally "flicker" in the data; this affects about a handful of endpoints per week or so. All entries
                                with <code>amazonwebservices.com.cn</code> or <code>amazonaws.com.cn</code> names are therefore excluded when generating the
                                list of recent changes.</li>
                    </ul>
                </div>
                <div id="footer">
                    <p>
                        Contact: <a href="https://twitter.com/apparentorder">@apparentorder</a> or
                        <a href="mailto:apparentorder@neveragain.de">e-mail</a>.
                    </p>
                    <p>
                        Sources are available on <a href="https://github.com/apparentorder/awsipv6">on Github</a>.
                    </p>
                </div>
            </div>
            </body>
        </html>
    """

    return {
        "statusCode": 200,
        "body": body,
        "headers": {"Content-Type": "text/html"},
    }

def handler(event: dict, context) -> dict:
    region_list = DEFAULT_REGION_SELECTION

    if qsp := event.get("queryStringParameters"):
        print(f"queryStringParameters: {json.dumps(qsp)}")

        # If there were QSP but no regions, make sure to use an empty list instead
        # of the cookie's value. That's why QSP take precedence over cookies.
        region_list_qsp = qsp.get("regions", "")
        region_list = sorted(region_list_qsp.split(",") if region_list_qsp else [])
        print(f"Regions selected from QS: {region_list}")

    elif all_cookies := event.get("cookies"):
        for cookie in all_cookies:
            name, _, value = cookie.partition("=")
            if name == "regions":
                region_list = sorted(value.split(",") if value else [])
                print(f"Regions selected from cookie: {region_list}")
                break

    path = event["requestContext"]["http"]["path"]
    print(f"Request for path: {path}")

    if path.endswith("/awsipv6-endpoints"):
        return get_table_data(event, html_only = False, region_list_from_user = region_list)

    if path.endswith("/awsipv6-main"):
        return get_main(event, region_list_from_user = region_list)

    return {
        "statusCode": 404,
        "body": "Unknown path",
    }