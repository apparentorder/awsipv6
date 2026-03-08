import json
import os
import sys
import time
import pathlib

# ----------------------------------------------------------------------
# take care of importing botocore from a git clone

if len(sys.argv) < 2:
    raise Exception("need botocore repo directory")

botocore_repo = sys.argv[1]

use_test_data = True
if len(sys.argv) == 3 and sys.argv[2] == "--live":
    use_test_data = False

sys.path.insert(0, f"{botocore_repo}")

import botocore
import sqlite3
from Endpoints import collect_endpoints, get_all_regions, get_botocore_session

# check for dummy tag to make sure we haven't accidentally imported the
# system-provided botocore
assert("awsipv6-git" in botocore.__version__)

# ----------------------------------------------------------------------
# collect / generate data

print(f"Gathering endpoint data ...")

botocore_session = get_botocore_session()
all_regions = get_all_regions(botocore_session, use_test_data=use_test_data)

# Collect all endpoints into a list
endpoints = []
last_service = None
for ep in collect_endpoints(botocore_session, use_test_data=use_test_data):
    service_name = ep['service']
    if service_name != last_service:
        print(f'* {service_name} ...')
        last_service = service_name
    endpoints.append(ep)

print()

# ----------------------------------------------------------------------
# write json output

print(f"Writing output to web/zola/static/endpoints.json ...")

with open(f"web/zola/static/endpoints.json", "w") as json_file:
    json.dump(endpoints, json_file, indent = 4)

print()

# ----------------------------------------------------------------------
# write text output

print(f"Writing output to web/zola/static/endpoints.text ...")

all_endpoints_text = []
for ep in endpoints:
    ep_default = ep['endpoint_default']
    ep_dualstack = ep['endpoint_dualstack']

    hostname_default = ep_default.get('hostname')
    hostname_dualstack = ep_dualstack.get('hostname')

    if hostname_default:
        tags = []
        if ep_default.get('has_ipv4'):
            tags.append('ipv4')
        if ep_default.get('has_ipv6'):
            tags.append('ipv6')
        tags_str = " [" + ", ".join(tags) + "]" if tags else ""
        all_endpoints_text.append(f"{hostname_default}{tags_str} (default)")

    if hostname_dualstack and hostname_dualstack != hostname_default:
        tags = []
        if ep_dualstack.get('has_ipv4'):
            tags.append('ipv4')
        if ep_dualstack.get('has_ipv6'):
            tags.append('ipv6')
        tags_str = " [" + ", ".join(tags) + "]" if tags else ""
        all_endpoints_text.append(f"{hostname_dualstack}{tags_str} (dualstack)")

with open(f"web/zola/static/endpoints.text", "w") as text_file:
    for ep in sorted(all_endpoints_text):
        print(f"{ep}", file = text_file)

# ----------------------------------------------------------------------
# write sqlite output

sqlite_path = "web/zola/static/endpoints.sqlite"
pathlib.Path(sqlite_path).unlink(missing_ok=True)
print(f"Writing output to {sqlite_path} ...")

with sqlite3.connect(sqlite_path) as conn_sqlite:
    cur_sqlite = conn_sqlite.cursor()
    cur_sqlite.execute("""
        CREATE TABLE IF NOT EXISTS region (
            region_name TEXT,
            partition_name TEXT,
            description TEXT,
            PRIMARY KEY (region_name, partition_name)
        )
        WITHOUT ROWID
    """)

    cur_sqlite.execute("""
        CREATE TABLE IF NOT EXISTS endpoint (
            service_name TEXT,
            region_name TEXT,
            partition_name TEXT,
            endpoint_default_hostname TEXT,
            endpoint_default_has_ipv4 INTEGER,
            endpoint_default_has_ipv6 INTEGER,
            endpoint_dualstack_hostname TEXT,
            endpoint_dualstack_has_ipv4 INTEGER,
            endpoint_dualstack_has_ipv6 INTEGER,
            PRIMARY KEY (service_name, region_name, partition_name)
        )
        WITHOUT ROWID
    """)

    for region_name, region_data in all_regions.items():
        cur_sqlite.execute("""
            INSERT INTO region (region_name, partition_name, description)
            VALUES (?, ?, ?)
            ON CONFLICT(region_name, partition_name) DO UPDATE SET description=excluded.description
        """, (
            region_name,
            region_data['partition'],
            region_data['description'],
        ))

    for ep in endpoints:
        ep_default = ep['endpoint_default']
        ep_dualstack = ep['endpoint_dualstack']

        cur_sqlite.execute("""
            INSERT INTO endpoint (
                service_name,
                partition_name,
                region_name,
                endpoint_default_hostname,
                endpoint_default_has_ipv4,
                endpoint_default_has_ipv6,
                endpoint_dualstack_hostname,
                endpoint_dualstack_has_ipv4,
                endpoint_dualstack_has_ipv6
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(service_name, partition_name, region_name) DO UPDATE SET
                endpoint_default_hostname=excluded.endpoint_default_hostname,
                endpoint_default_has_ipv4=excluded.endpoint_default_has_ipv4,
                endpoint_default_has_ipv6=excluded.endpoint_default_has_ipv6,
                endpoint_dualstack_hostname=excluded.endpoint_dualstack_hostname,
                endpoint_dualstack_has_ipv4=excluded.endpoint_dualstack_has_ipv4,
                endpoint_dualstack_has_ipv6=excluded.endpoint_dualstack_has_ipv6
        """, (
            ep['service'],
            ep['partition'],
            ep['region'],
            ep_default.get('hostname'),
            int(ep_default.get('has_ipv4', False)),
            int(ep_default.get('has_ipv6', False)),
            ep_dualstack.get('hostname'),
            int(ep_dualstack.get('has_ipv4', False)),
            int(ep_dualstack.get('has_ipv6', False)),
        ))

print()

print(f"Done.")
