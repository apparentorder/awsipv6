#!/usr/bin/env python3

from botocore.regions import EndpointResolver
import botocore.session
import json
import socket
import sys

class ServiceEndpointsCollection:
    def __init__(self, use_test_data = False):
        self._botocore_session = botocore.session.get_session()
        self.botocore_endpoint_resolver = self._botocore_session.get_component('endpoint_resolver')
        self.botocore_endpoint_data = self.botocore_endpoint_resolver._endpoint_data

        self.endpoints = []
        self.service_lookup = {}

        if use_test_data:
            self._use_test_data()
            return

        self.all_regions = {}
        self.all_services = set()

        for partition_data in self.botocore_endpoint_data['partitions']:
            if partition_data['partition'] in self.botocore_endpoint_resolver._UNSUPPORTED_DUALSTACK_PARTITIONS:
                continue

            for region_key, region_data in partition_data['regions'].items():
                self.all_regions[region_key] = region_data
                self.all_regions[region_key]['partition'] = partition_data['partition']

            for service_name, _ in partition_data['services'].items():
                self.all_services.add(service_name)

    def _use_test_data(self):
        self.all_regions = {
            "eu-central-1": {
                "description": "euc1",
                "partition": "aws",
            },
            "us-east-2": {
                "description": "use2",
                "partition": "aws",
            },
            "eu-west-1": {
                "description": "euw1",
                "partition": "aws",
            },
            "il-central-1": {
                "description": "ilc1",
                "partition": "aws",
            },
        }

        self.all_services = set(["elasticbeanstalk", "firehose", "secretsmanager", "ec2", "iam", "amplify",
            "rds",
            "health"])

    def stats(self):
        # note: SEPs that are not present (service not supported in a region) do not count.
        se_count = 0
        se_count_ipv6_default = 0
        se_count_ipv6_dualstack = 0
        se_count_ipv4_only = 0
        se_count_nx = 0
        
        for sep in self.endpoints:
            if not sep.endpoint_default.hostname and not sep.endpoint_dualstack.hostname:
                se_count_nx += 1
            elif sep.endpoint_default.has_ipv6:
                se_count += 1
                se_count_ipv6_default += 1
            elif sep.endpoint_dualstack.has_ipv6:
                se_count += 1
                se_count_ipv6_dualstack += 1
            else:
                se_count += 1
                se_count_ipv4_only += 1
                
        return {
            "count_total": se_count + se_count_nx,
            "count_enabled": se_count,
            "count_ipv6_default": se_count_ipv6_default,
            "count_ipv6_dualstack": se_count_ipv6_dualstack,
            "count_ipv4_only": se_count_ipv4_only,
            "count_nx": se_count_nx,
        }
        
    def add(self, service_name, partition_name, region_name):
        sep = ServiceEndpoints(
            service_name = service_name,
            partition_name = partition_name,
            region_name = region_name,
            endpoint_resolver = self.botocore_endpoint_resolver
        )

        self.endpoints += [sep]
        self.service_lookup[f'{sep.partition_name}:{sep.service_name}:{sep.region_name}'] = sep

    def data(self):
        return list(map(lambda sep: sep.data(), self.endpoints))

    def load_json_file(self, json_file):
        with open(json_file, "r") as f:
            json_data = json.load(f)

        for sep_data in json_data:
            sep = ServiceEndpoints.from_data(sep_data)
            self.endpoints += [sep]
            self.service_lookup[f'{sep.partition_name}:{sep.service_name}:{sep.region_name}'] = sep

class Endpoint:
    def __init__(self, hostname, loaded = False):
        self.hostname = hostname
        self.has_ipv4 = False
        self.has_ipv6 = False

        if loaded:
            return

        if hostname is None:
            return

        self.resolve()

        if not self.has_ipv4 and not self.has_ipv6:
            self.hostname = None

    @staticmethod
    def from_data(data):
        ep = Endpoint(data['hostname'], loaded = True)
        ep.has_ipv4 = data['has_ipv4']
        ep.has_ipv6 = data['has_ipv6']

        return ep

    def data(self):
        r = {
            "hostname": self.hostname,
            "has_ipv4": self.has_ipv4,
            "has_ipv6": self.has_ipv6,
        }

        return r

    def __str__(self):
        if self.hostname is None:
            return ""

        tags = []
        tags_str = ""

        tags += ["ipv4"] if self.has_ipv4 else []
        tags += ["ipv6"] if self.has_ipv6 else []

        if len(tags) > 0:
            tags_str = " [" + ", ".join(tags) + "]"

        return f"{self.hostname}{tags_str}"

    def resolve(self):
        self.has_ipv4 = False
        self.has_ipv6 = False

        #print(f"RESOLVE: {hostname}")
        try:
            for (family, _socktype, _proto, _canon_name, _addr) in socket.getaddrinfo(self.hostname, 443):
                #print(f"{hostname} {addr[0]}")
                self.has_ipv4 |= (family == socket.AddressFamily.AF_INET)
                self.has_ipv6 |= (family == socket.AddressFamily.AF_INET6)
        except socket.gaierror:
            # name not known, probably.
            pass

class ServiceEndpoints:
    def __init__(self, service_name, partition_name, region_name, endpoint_resolver, loaded = False):
        self.partition = partition_name
        self.service_name = service_name
        self.partition_name = partition_name
        self.region_name = region_name
        self.endpoint_default = None
        self.endpoint_dualstack = None
        self.deprecated = False

        if loaded:
            return

        aws_endpoint_default = endpoint_resolver.construct_endpoint(
            service_name,
            region_name,
            partition_name,
            use_dualstack_endpoint = False
        )

        if aws_endpoint_default.get('deprecated'):
            # we're not handling those endpoints
            self.deprecated = True
            self.endpoint_default = Endpoint(None)
            self.endpoint_dualstack = Endpoint(None)
            return

        self.endpoint_default = Endpoint(aws_endpoint_default.get('hostname'))

        try:
            aws_endpoint_dualstack = endpoint_resolver.construct_endpoint(
                service_name,
                region_name,
                partition_name,
                use_dualstack_endpoint = True
            )

            self.endpoint_dualstack = Endpoint(aws_endpoint_dualstack.get('hostname'))

        except botocore.exceptions.EndpointVariantError:
            pass

    @staticmethod
    def from_data(data):
        sep = ServiceEndpoints(
            service_name = data['service'],
            partition_name = data['partition'],
            region_name = data['region'],
            endpoint_resolver = None,
            loaded = True
        )

        sep.endpoint_default = Endpoint.from_data(data['endpoint_default'])
        sep.endpoint_dualstack = Endpoint.from_data(data['endpoint_dualstack'])

        return sep

    def data(self):
        r = {
            "service": self.service_name,
            "partition": self.partition_name,
            "region": self.region_name,
            "endpoint_default": self.endpoint_default.data(),
            "endpoint_dualstack": self.endpoint_dualstack.data(),
        }

        return r
