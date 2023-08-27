#!/usr/bin/env python3

import json
import sys
import subprocess
    
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
