#!/usr/bin/env python3
# should read "php" ...

import json
import sys
import re
import html

if len(sys.argv) < 2:
    raise Exception("need botocore repo directory")
    
botocore_repo = sys.argv[1]

use_test_data = True
base_url = "https://awsipv6.s3.eu-central-1.amazonaws.com/beta"

if len(sys.argv) == 3 and sys.argv[2] == "--live":
    use_test_data = False
    base_url = "https://awsipv6.neveragain.de"

sys.path.insert(0, f"{botocore_repo}")

import botocore
from Endpoints import ServiceEndpointsCollection

# check for dummy tag to make sure we haven't accidentally imported the
# system-provided botocore
assert("awsipv6-git" in botocore.__version__)

# ----------------------------------------------------------------------

REGIONS_DISPLAY_DEFAULT = [
        # top regions, by services count,
        # according to https://www.aws-services.info/regions.html
        "us-east-1",
        "us-east-2",
        #"us-west-2",
        "eu-west-1",
        #"eu-west-2",
        "eu-central-1",
        "ap-southeast-1",
        #"ap-southeast-2",
        "ap-northeast-1",
        #"ap-northeast-2",
        "ca-central-1",
        "cn-north-1",
        "us-gov-west-1",
]

# ----------------------------------------------------------------------
# load service data
sec = ServiceEndpointsCollection(use_test_data = use_test_data)
sec.load_json_file("output/endpoints.json")
stats = sec.stats()

# ----------------------------------------------------------------------
# pass 3: output

print('''<!doctype html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta charset="UTF-8">
<meta name="twitter:card" content="summary_large_image" />
<meta property="og:title" content="AWS service endpoints by region and IPv6 support">
<meta name="description" content="A map to quickly identify which AWS services in your region support IPv6 by default and which require using a special dualstack endpoint">
<meta property="og:description" content="A map to quickly identify which AWS services in your region support IPv6 by default and which require using a special dualstack endpoint">
''')
print(f'<meta property="og:image" content="{base_url}/og-image.png">')
print('''
<meta property="og:type" content="website">
<link rel="stylesheet" href="uglyshit.css">
<link rel="stylesheet" href="fonts.css">
<title>AWS service endpoints by region and IPv6 support</title>
<script src="uglyshit.js"></script>
</head>

<body>
''')

print('<div id="intro-and-stats" class="p-4">')

print('<div id="intro" class="grid md:grid-cols-2">')

print('<div id="intro-text" class="space-y-2 text-sm max-w-prose">')
print('<h2 class="text-xl font-bold">')
print('AWS service endpoints by region and IPv6 support')
print('</h2>')

print('<p>')
print('AWS has 300+ distinct service APIs and 30+ regions. Over 6,000 of those combinations')
print('are in service.')
print('The following table shows each service API, per region, by IPv6 support status.')
print('</p>')
print('<p class="font-light">')
print('IPv6-support <strong>by default</strong> will "just work" (e.g. from an IPv6-only VPC).')
print('A <strong>dualstack endpoint</strong> supports IPv6, but requires additional configuration.')
print('See this <a href="https://tty.neveragain.de/2024/05/20/aws-ipv6-egress.html">blog post</a>')
print('for details.')
print('</p>')

print('<p class="font-light">')
print('<strong>IPv4-only services are hidden by default.</strong>')
print('Hover to see a endpoint addresses. Data is available as JSON <a href="endpoints.json">here</a>.')
print('</p>')

print('</div>') # intro-text

print('<div id="ipv6-color-stats" class="text-sm max-w-prose">')
print('<strong>The table is color-coded:</strong>')
print('<table class="">')
print(f'<tr>')
stats_str = f"{int(stats['count_ipv6_default']*100/stats['count_enabled'])}%"
print(f'<td class="p-1 endpoint-ipv6">IPv6 by default</td>')
print(f'<td class="p-1 endpoint-ipv6 text-xl font-light">{stats_str}</td>')
print(f'</tr>')
print(f'<tr>')
stats_str = f"{int(stats['count_ipv6_dualstack']*100/stats['count_enabled'])}%"
print(f'<td class="p-1 endpoint-ipv6-dualstack">IPv6 "dualstack"</td>')
print(f'<td class="p-1 endpoint-ipv6-dualstack text-xl font-light">{stats_str}</td>')
print(f'</tr>')
print(f'<tr>')
stats_str = f"{int(stats['count_ipv4_only']*100/stats['count_enabled'])}%"
print(f'<td class="p-1 endpoint-ipv4">IPv4 only</td>')
print(f'<td class="p-1 endpoint-ipv4 text-xl font-light">{stats_str}</td>')
print(f'</tr>')
print('</table>') # grid
print('</div>') # ipv6-color-stats

print('</div>') # intro
#print('<div id="stats" class="p-5 float-right">')
#print('<div class="card">123</div>')
#print('</div>') # stats
print('</div>') # intro-and-stats

print('<div id="everything" class="border-t flex">')

print('<div id="settings" class="p-4 w-64 flex-initial space-y-4 bg-gray-100 border-r-2">')
if True: # settings
    print('<strong>Filter services:</strong>')
    print('<div id="filter-services">')
    print('<input type="search" autofocus class="box-border w-full border-2 rounded" id="search-service" pattern="[a-z0-9]*" oninput="updateSearch(this)">')
    print('</div>') # filter-services
    
    #print('<hr>')    
    
    print(f'<div class="select-v4only"><label><strong><input id="toggle-v4only" type="checkbox" checked onchange="toggleV4Only(this)"> Hide IPv4-only services</strong></label></div>')
    
    #print('<hr>')
    
    #print('<div id="region-selection-dropdown">')
    #print('<p>')
    #print('<span class="anchor" onclick="toggleRegionDropdown(this)">&gt;&gt; <strong>Click here to select regions</strong></span>')
    #print('</p>')
    #print('<div id="region-selection-items" style="display:none">')
    print('<div id="region-selection-items">')
    print('<strong>Select regions:</strong>')
    for region_key in sorted(sec.all_regions.keys()):
        partition_name = sec.all_regions[region_key]['partition']
        region_description = sec.all_regions[region_key]['description']
        region_description = re.sub(r'.*\((.*)\).*', '\\1', region_description)
        checked = "checked" if region_key in REGIONS_DISPLAY_DEFAULT else ""
        print(f'<div class="region-selection text-xs"><label>')
        #print(f'<div>')
        print(f'<input type="checkbox" {checked} onchange="toggleRegion(this, \'{partition_name}-{region_key}\')">')
        print(f'{region_key}')
        #print(f'</div>')
        #print(f'<div>')
        print(f'({region_description})')
        #print(f'</div>')
        print(f'</label></div>')
        
    print('</div>')
    #print('</div>') # region-selection-items
    #print('</div>') # region-selection-dropdown
    #print('</p>')

    
print('</div>') # settings/sidebar


print('<div id="main-content" class="p-2 flex-auto text-xs">')
print('''
<div class="flex flex-col">
  <div class="">
    <div class="">
      <div class="">
        <table class="text-center text-sm font-light">

''')
#<div class="flex flex-col">
#  <div class="overflow-x-auto sm:-mx-6 lg:-mx-8">
#    <div class="inline-block py-2 sm:px-6 lg:px-8">
#      <div class="overflow-hidden">
#        <table class="text-center text-sm font-light">
        
print('<thead class="border-b font-medium dark:border-neutral-500">')
print('<tr>')
print("<th>Service</th>")
for region_key in sorted(sec.all_regions.keys()):
    partition_name = sec.all_regions[region_key]['partition']
    display = "display:none" if region_key not in REGIONS_DISPLAY_DEFAULT else ""
    print(f'<th style="{display}" class="data-region-{partition_name}-{region_key} p-1 border-r">{region_key}</th>')
print("</tr>")
print('</thead>')
print('<tbody>')

for service_name in sorted(sec.all_services):
    # pass 1: check if the service makes us sad
    has_any_ipv6 = False

    for region_key in sorted(sec.all_regions.keys()):
        partition_name = sec.all_regions[region_key]['partition']
        s = sec.service_lookup[f"{partition_name}:{service_name}:{region_key}"]
        if s.endpoint_default.has_ipv6 or s.endpoint_dualstack.has_ipv6:
            has_any_ipv6 = True

    v4only = " service-ipv4-only" if not has_any_ipv6 else ""
    v4only_hide = "display:none" if not has_any_ipv6 else ""

    print(f'<tr style="{v4only_hide}" class="service-row data-service-{service_name}{v4only} border-b dark:border-neutral-500">')
    print(f'<th class="service-name">{service_name}</th>')


    for region_key in sorted(sec.all_regions.keys()):
        partition_name = sec.all_regions[region_key]['partition']
        s = sec.service_lookup[f"{partition_name}:{service_name}:{region_key}"]

        s_out = ""
        if str(s.endpoint_default):
            s_out += f'<div class="has-tooltip">default'
            s_out += f'<span class="tooltip rounded shadow-lg p-1 bg-gray-100 -mt-8">{s.endpoint_default}</span>'
            s_out += f'</div>'
        if str(s.endpoint_dualstack):
            s_out += f'<div class="has-tooltip">dualstack'
            s_out += f'<span class="tooltip rounded shadow-lg p-1 bg-gray-100 -mt-8">{s.endpoint_dualstack}</span>'
            s_out += f'</div>'

        classes  = [f"data-region-{partition_name}-{region_key}"]
        classes += [f"data-service-{service_name}"]
        classes += [f"service-endpoints"]

        if not s.endpoint_default.hostname and not s.endpoint_dualstack.hostname:
            classes += ["endpoint-nx"]
        else:
            if s.endpoint_default.has_ipv6:
                classes += ["endpoint-ipv6"]
            elif s.endpoint_dualstack.has_ipv6:
                classes += ["endpoint-ipv6-dualstack"]
            else:
                classes += ["endpoint-ipv4"]

        display = "display:none" if region_key not in REGIONS_DISPLAY_DEFAULT else ""
        print(f'<td style="{display}" class="border-r {" ".join(classes)}"> {s_out} </td>')

    print("</tr>")

print('</tbody>')
print("</table>")
print("</div>")
print("</div>")
print("</div>")
print("</div>")
print('</div>') # main-content
print('</div>') # everything

print('<div id="changes" class="p-2 border-t space-y-2">')
print('<h4 class="text-xl">Recent changes</h4>')

print('<div id="changes-explain" class="text-sm">')
print('Endpoints with a <code>+</code> have been added.<br>')
print('Endpoints with a <code>-</code> have been removed.')
print('</div>')

with open("output/changes") as f:
    data_tags_open = False
    for line in f.readlines():
        if re.match(r'^\d', line):
            if data_tags_open:
                print('</ul>')
                data_tags_open = False
                
            # new date
            print(f'<div id="changes-date" class="text-sm space-y-1">{line}</div>')
            print(f'<ul id="changes-data" class="text-xs">')
            data_tags_open = True
            
        else:
            line = re.sub(r'^(.)', r'\1 ', line) # add space
            print(f'<li><code>{html.escape(line)}</code></li>')
            
    print('</ul>')

print('</div>')

print('<div id="outro" class="p-2 border-t space-y-4">')
print('''
<div id="details">
The details:
<ul class="list-disc pl-6 text-xs max-w-prose">
  <li>This list is generated almost daily (Tue - Sat) from botocore's <code>get_available_services()</code> and <code>create_client()</code></li>
  <li>IPv4 and IPv6 support is determined by DNS only (i.e. if an endpoint returns any AAAA records, it is considered IPv6-enabled)</li>
  <li>AWS partitions that are marked as <code>_UNSUPPORTED_DUALSTACK_PARTITIONS</code> have been excluded.</li>
  <li>Service APIs that require additional parameters have been excluded (currently only <code>cloudfront-keyvaluestore</code> and <code>s3control</code>)</li>
  <li>Regions that are not available for a service are not checked, according to botocore's <code>get_available_services()</code> (which seems to be wrong sometimes)</li>
  <li>Non-regionalized services (that have only one partition-wide endpoint, i.e. IAM or Route53) are not properly supported yet</li>
  <li>Selection "Hide IPv4-only" may display services that are IPv6-enabled only in regions that are not currently selected</li>
  <li>Percentages in the table at the top are based on the count of service-region endpoints that are actually available; that's more than 6.000 endpoints,
      btw, while the total number of service/region combinations is more than 9.000</li>
  <li>Fun fact: In about 2/3 of regions, there isn't just <code>s3.$region.amazonaws.com</code>, but also a version with dash, <code>s3-$region.amazonaws.com</code>,
      and that also works. Reasons unknown.</li>
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
''')

print("</body>")
print("</html>")
