#!/usr/bin/env python3

from botocore.regions import EndpointResolver
import urllib
import botocore.session
import botocore.exceptions
import json
import socket

class ServiceEndpointsCollection:
    def __init__(self, use_test_data = False):
        self.botocore_session = botocore.session.get_session()
        self.botocore_endpoint_resolver = self.botocore_session.get_component('endpoint_resolver')
        self.botocore_endpoint_data = self.botocore_endpoint_resolver._endpoint_data

        self.endpoints = []
        self.service_lookup = {}

        if use_test_data:
            self._use_test_data()
            return

        self.all_regions = {}

        # some services require additional parameters that are not known to us.
        # no option but to blacklist those services
        self.service_blacklist = {
            "cloudfront-keyvaluestore": "KVS ARN must be provided to use this service",
            "s3control": "ParamValidationError: Parameter validation failed: AccountId is required but not set",
        }

        self.all_services = set(self.botocore_session.get_available_services()) - set(self.service_blacklist.keys())

        # XXX: 2024-05-30: for some(?) "iso" regions, for all(?) services name -- including those that usually *do* have a dualstack
        # endpoint --, botocore throws an exception:
        #
        #     botocore.exceptions.EndpointVariantError: Unable to construct a modeled endpoint with the following variant(s) ['dualstack']:
        #
        # Regions observed so far: eu-isoe-west-1 (2024-05-30), us-isof-east-1, us-isof-south-1, eusc-de-east-1 (all 2025-07-13).
        #
        # We will assume that these partitions do not support dualstack at all and should have been flagged accordingly.
        # Exception: EU Sovereign Cloud (eusc), which will be an additional public commercial partition and deserves visibility.
        #
        # Revisit this in due time.
        #
        self.botocore_endpoint_resolver._UNSUPPORTED_DUALSTACK_PARTITIONS += ["aws-iso-e", "aws-iso-f"]

        for partition_data in self.botocore_endpoint_data['partitions']:
            if partition_data['partition'] in self.botocore_endpoint_resolver._UNSUPPORTED_DUALSTACK_PARTITIONS:
                continue

            for region_key, region_data in partition_data['regions'].items():
                self.all_regions[region_key] = region_data
                self.all_regions[region_key]['partition'] = partition_data['partition']

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
            "cn-north-1": {
                "description": "cnn1",
                "partition": "aws-cn",
            },
        }

        self.all_services = [
            'apigateway',
            'sts',
            'ec2',
            'iam',
            'secretsmanager',
         ]

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
            botocore_session = self.botocore_session
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
    def __init__(self, service_name, partition_name, region_name, botocore_session, loaded = False):
        self.partition = partition_name
        self.service_name = service_name
        self.partition_name = partition_name
        self.region_name = region_name
        self.botocore_session = botocore_session
        self.endpoint_default = None
        self.endpoint_dualstack = None
        self.deprecated = False
        self.config_default = botocore.config.Config(defaults_mode = 'standard')
        self.config_dualstack = botocore.config.Config(defaults_mode = 'standard', use_dualstack_endpoint = True)

        if loaded:
            return

        # XXX: unfortunately, get_available_regions() works correctly for most services,
        #      but fails for some services (e.g. for 'bedrock' or 'eks-auth' it returns
        #      an empty list)  --  https://github.com/boto/botocore/issues/3028
        #      we therefore only use it when it actually returns something.
        service_regions = self.botocore_session.get_available_regions(service_name, partition_name)

        if len(service_regions) > 0 and region_name not in service_regions:
            self.endpoint_default = Endpoint(None)
            self.endpoint_dualstack = Endpoint(None)
            return

        hostname_default = self._resolve_service_endpoint(service_name, region_name, config = self.config_default)
        hostname_dualstack = self._resolve_service_endpoint(service_name, region_name, config = self.config_dualstack)

        self.endpoint_default = Endpoint(hostname_default)

        if hostname_dualstack != hostname_default:
            self.endpoint_dualstack = Endpoint(hostname_dualstack)
        else:
            # for services that use the same endpoint for "dualstack", or don't
            # support any separate dualstack endpoint at all, don't list the
            # dualstack endpoint separately.
            self.endpoint_dualstack = Endpoint(None)

    def _resolve_service_endpoint(self, service_name, region_name, config = None):
        try:
            aws_client = self.botocore_session.create_client(
                service_name,
                region_name = region_name,
                config = config,
            )

        except botocore.exceptions.EndpointVariantError as e:
            print(f"WARNING:  Resolving {service_name} in {region_name}: {e}")
            return None

        # proper usage of botocore's newer EndpointRulesetResolver infrastructure
        # is tied to a single operation (an OperationModel); for our purposes, it
        # doesn't matter which operation we pick, we just need to pick one.
        some_operation_name = list(aws_client._service_model._service_description['operations'].keys())[0]
        operation_model = aws_client._service_model.operation_model(some_operation_name)

        # the rest of this is based on botocore/client.py, BaseClient._make_api_call()
        request_context = {
            'client_region': aws_client.meta.region_name,
            'client_config': aws_client.meta.config,
            'has_streaming_input': operation_model.has_streaming_input,
            'auth_type': operation_model.auth_type,
        }

        try:
            result = aws_client._resolve_endpoint_ruleset(
                operation_model,
                {}, # api_params (we don't need those)
                request_context = request_context
            )

            return urllib.parse.urlparse(result[0]).netloc

        except Exception as e:
            print(f"ERROR:  Resolving for service {service_name} in region {region_name}: {e}")
            return None

    @staticmethod
    def from_data(data):
        sep = ServiceEndpoints(
            service_name = data['service'],
            partition_name = data['partition'],
            region_name = data['region'],
            botocore_session = None,
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
