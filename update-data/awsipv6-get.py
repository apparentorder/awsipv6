import json
import os
import psycopg
import subprocess
import sys

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
import boto3
from Endpoints import ServiceEndpointsCollection

# check for dummy tag to make sure we haven't accidentally imported the
# system-provided botocore
assert("awsipv6-git" in botocore.__version__)

# ----------------------------------------------------------------------
# collect / generate data

sec = ServiceEndpointsCollection(use_test_data = use_test_data)

for service_name in sorted(sec.all_services):
    print(f'* {service_name} ...')

    for region_name, region_data in sec.all_regions.items():
        partition_name = region_data['partition']

        sec.add(service_name, partition_name, region_name)

# ----------------------------------------------------------------------
# write database output

dsql_client = boto3.client('dsql')
dsql_token = dsql_client.generate_db_connect_admin_auth_token(Hostname = os.environ.get('DSQL_ENDPOINT'))
conn = psycopg.connect(
    host = os.environ.get('DSQL_ENDPOINT'),
    dbname = 'postgres',
    user = 'admin',
    password = dsql_token,
    sslmode = 'require',
)

with conn.cursor() as cur:
    insert_sql = """
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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (service_name, partition_name, region_name)
        DO UPDATE SET
            endpoint_default_hostname = EXCLUDED.endpoint_default_hostname,
            endpoint_default_has_ipv4 = EXCLUDED.endpoint_default_has_ipv4,
            endpoint_default_has_ipv6 = EXCLUDED.endpoint_default_has_ipv6,
            endpoint_dualstack_hostname = EXCLUDED.endpoint_dualstack_hostname,
            endpoint_dualstack_has_ipv4 = EXCLUDED.endpoint_dualstack_has_ipv4,
            endpoint_dualstack_has_ipv6 = EXCLUDED.endpoint_dualstack_has_ipv6;
    """

    insert_region_sql = """
        INSERT INTO region (
            region_name,
            partition_name,
            description
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (region_name, partition_name)
        DO UPDATE SET description = EXCLUDED.description;
    """

    for region_name, region_data in sec.all_regions.items():
        # Process all records by region so that each COMMIT covers a few hundred records,
        # aligning nicely with DSQL's row limit.
        partition_name = region_data['partition']

        cur.execute(insert_region_sql, (
            region_name,
            partition_name,
            region_data['description'],
        ))

        for sep in filter(lambda ep: ep.region_name == region_name, sec.endpoints):
                cur.execute(insert_sql, (
                    sep.service_name,
                    sep.partition_name,
                    sep.region_name,
                    sep.endpoint_default.hostname,
                    sep.endpoint_default.has_ipv4,
                    sep.endpoint_default.has_ipv6,
                    sep.endpoint_dualstack.hostname,
                    sep.endpoint_dualstack.has_ipv4,
                    sep.endpoint_dualstack.has_ipv6,
                ))

        conn.commit()

# ----------------------------------------------------------------------
# write json output

with open(f"output/endpoints.json", "w") as json_file:
    json.dump(sec.data(), json_file, indent = 4)

# ----------------------------------------------------------------------
# write text output

all_endpoints_text = []
for sep in sec.endpoints:
    all_endpoints_text += [f"{sep.endpoint_default} (default)"] if sep.endpoint_default.hostname else []
    all_endpoints_text += [f"{sep.endpoint_dualstack} (dualstack)"] if sep.endpoint_dualstack.hostname else []

with open(f"output/endpoints.text", "w") as text_file:
    for ep in sorted(all_endpoints_text):
        print(f"{ep}", file = text_file)
