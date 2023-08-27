#!/usr/bin/env python3

# intended for manual use; adjust filenames accordingly.

import json
import sys
import subprocess

import botocore
from Endpoints import ServiceEndpointsCollection

sec = ServiceEndpointsCollection(use_test_data = False)
sec.load_json_file("/tmp/endpoints-20230817.json")

all_endpoints_text = []
for sep in sec.endpoints:
    all_endpoints_text += [f"{sep.endpoint_default} (default)"] if sep.endpoint_default.hostname else []
    all_endpoints_text += [f"{sep.endpoint_dualstack} (dualstack)"] if sep.endpoint_dualstack.hostname else []

with open(f"output/endpoints.text", "w") as text_file:
    for ep in sorted(all_endpoints_text):
        print(f"{ep}", file = text_file) 
    