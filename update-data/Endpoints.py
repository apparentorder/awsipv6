#!/usr/bin/env python3
"""
AWS IPv6 Endpoint Data Collection

This module provides functions to collect AWS service endpoint data,
including IPv4/IPv6 support detection via DNS resolution.

Functions:
- get_available_services: Get list of available AWS services
- get_all_regions: Get all AWS regions with partition info
- resolve_endpoint: Resolve hostname and detect IPv4/IPv6 support
- get_service_hostname: Get service endpoint hostname via botocore
- collect_endpoints: Generator that yields endpoint data dicts
- calculate_stats: Calculate statistics from endpoint list
"""

from botocore.regions import EndpointResolver
import urllib
import botocore.session
import botocore.exceptions
import json
import socket


# Service blacklist - services that require additional parameters
SERVICE_BLACKLIST = {
    "cloudfront-keyvaluestore": "KVS ARN must be provided to use this service",
    "s3control": "ParamValidationError: Parameter validation failed: AccountId is required but not set",
}

# Unsupported dualstack partitions
UNSUPPORTED_DUALSTACK_PARTITIONS = ["aws-iso-e", "aws-iso-f"]


# =============================================================================
# Test Data
# =============================================================================

TEST_REGIONS = {
    "eu-central-1": {
        "description": "euc1",
        "partition": "aws",
    },
    "us-east-2": {
        "description": "use2",
        "partition": "aws",
    },
    "us-west-1": {
        "description": "usw1",
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
    "ap-southeast-2": {
        "description": "apse2",
        "partition": "aws",
    },
    "ca-central-1": {
        "description": "cac1",
        "partition": "aws",
    },
    "us-east-1": {
        "description": "use1",
        "partition": "aws",
    },
    "us-gov-west-1": {
        "description": "us-gov-w1",
        "partition": "aws-us-gov",
    },
}

TEST_SERVICES = [
    'apigateway',
    'sts',
    'ec2',
    'iam',
    'secretsmanager',
]


# =============================================================================
# Core Functions
# =============================================================================

def get_botocore_session():
    """Create and return a botocore session."""
    return botocore.session.get_session()


def get_available_services(botocore_session, use_test_data=False):
    """
    Get set of available AWS services.

    Args:
        botocore_session: Botocore session object
        use_test_data: If True, return test services instead

    Returns:
        Set of service names
    """
    if use_test_data:
        return set(TEST_SERVICES)

    return set(botocore_session.get_available_services()) - set(SERVICE_BLACKLIST.keys())


def get_all_regions(botocore_session, use_test_data=False):
    """
    Get all AWS regions with partition information.

    Args:
        botocore_session: Botocore session object
        use_test_data: If True, return test regions instead

    Returns:
        Dict mapping region_name -> {description, partition}
    """
    if use_test_data:
        return dict(TEST_REGIONS)

    botocore_endpoint_resolver = botocore_session.get_component('endpoint_resolver')
    botocore_endpoint_data = botocore_endpoint_resolver._endpoint_data

    # Add unsupported partitions to botocore's list
    botocore_endpoint_resolver._UNSUPPORTED_DUALSTACK_PARTITIONS += UNSUPPORTED_DUALSTACK_PARTITIONS

    all_regions = {}
    for partition_data in botocore_endpoint_data['partitions']:
        if partition_data['partition'] in UNSUPPORTED_DUALSTACK_PARTITIONS:
            continue

        for region_key, region_data in partition_data['regions'].items():
            all_regions[region_key] = region_data
            all_regions[region_key]['partition'] = partition_data['partition']

    return all_regions


def resolve_endpoint(hostname):
    """
    Resolve hostname and detect IPv4/IPv6 support via DNS.

    Args:
        hostname: The hostname to resolve

    Returns:
        dict: {hostname, has_ipv4, has_ipv6}
    """
    result = {
        "hostname": hostname,
        "has_ipv4": False,
        "has_ipv6": False,
    }

    if hostname is None:
        return result

    try:
        for (family, _socktype, _proto, _canon_name, _addr) in socket.getaddrinfo(hostname, 443):
            result["has_ipv4"] |= (family == socket.AddressFamily.AF_INET)
            result["has_ipv6"] |= (family == socket.AddressFamily.AF_INET6)
    except socket.gaierror:
        # Name not known, probably
        pass

    # If neither IP version resolved, clear hostname
    if not result["has_ipv4"] and not result["has_ipv6"]:
        result["hostname"] = None

    return result


def get_service_hostname(service_name, region_name, botocore_session, use_dualstack=False):
    """
    Get service endpoint hostname using botocore.

    Args:
        service_name: AWS service name (e.g., 'ec2')
        region_name: AWS region (e.g., 'us-east-1')
        botocore_session: Botocore session object
        use_dualstack: If True, use dualstack endpoint

    Returns:
        Hostname string or None if not available
    """
    config = botocore.config.Config(
        defaults_mode='standard',
        use_dualstack_endpoint=use_dualstack
    )

    try:
        aws_client = botocore_session.create_client(
            service_name,
            region_name=region_name,
            config=config,
        )
    except botocore.exceptions.EndpointVariantError as e:
        print(f"WARNING:  Resolving {service_name} in {region_name}: {e}")
        return None

    # Get any operation to resolve the endpoint
    some_operation_name = list(aws_client._service_model._service_description['operations'].keys())[0]
    operation_model = aws_client._service_model.operation_model(some_operation_name)

    request_context = {
        'client_region': aws_client.meta.region_name,
        'client_config': aws_client.meta.config,
        'has_streaming_input': operation_model.has_streaming_input,
        'auth_type': operation_model.auth_type,
    }

    try:
        result = aws_client._resolve_endpoint_ruleset(
            operation_model,
            {},  # api_params (we don't need those)
            request_context=request_context
        )
        return urllib.parse.urlparse(result[0]).netloc
    except Exception as e:
        print(f"ERROR:  Resolving for service {service_name} in {region_name}: {e}")
        return None


def collect_endpoints(botocore_session, use_test_data=False):
    """
    Generator that yields endpoint data for all services in all regions.

    Args:
        botocore_session: Botocore session object
        use_test_data: If True, use test data instead of live AWS data

    Yields:
        dict with endpoint data:
        {
            'service': str,
            'partition': str,
            'region': str,
            'endpoint_default': {hostname, has_ipv4, has_ipv6},
            'endpoint_dualstack': {hostname, has_ipv4, has_ipv6},
        }
    """
    all_services = get_available_services(botocore_session, use_test_data)
    all_regions = get_all_regions(botocore_session, use_test_data)

    # Add unsupported partitions to botocore's list (needed for each new session)
    botocore_endpoint_resolver = botocore_session.get_component('endpoint_resolver')
    for partition in UNSUPPORTED_DUALSTACK_PARTITIONS:
        if partition not in botocore_endpoint_resolver._UNSUPPORTED_DUALSTACK_PARTITIONS:
            botocore_endpoint_resolver._UNSUPPORTED_DUALSTACK_PARTITIONS.append(partition)

    for service_name in sorted(all_services):
        for region_name, region_data in all_regions.items():
            partition_name = region_data['partition']

            # Check if service is available in this region
            service_regions = botocore_session.get_available_regions(service_name, partition_name)

            if len(service_regions) > 0 and region_name not in service_regions:
                # Service not available in this region
                endpoint_default = resolve_endpoint(None)
                endpoint_dualstack = resolve_endpoint(None)
            else:
                # Get default endpoint
                hostname_default = get_service_hostname(
                    service_name, region_name, botocore_session, use_dualstack=False
                )
                endpoint_default = resolve_endpoint(hostname_default)

                # Get dualstack endpoint (if different)
                hostname_dualstack = get_service_hostname(
                    service_name, region_name, botocore_session, use_dualstack=True
                )

                if hostname_dualstack != hostname_default:
                    endpoint_dualstack = resolve_endpoint(hostname_dualstack)
                else:
                    # Same as default or not supported
                    endpoint_dualstack = resolve_endpoint(None)

            yield {
                'service': service_name,
                'partition': partition_name,
                'region': region_name,
                'endpoint_default': endpoint_default,
                'endpoint_dualstack': endpoint_dualstack,
            }


def calculate_stats(endpoints):
    """
    Calculate statistics from endpoint list.

    Args:
        endpoints: List of endpoint dicts

    Returns:
        dict with statistics:
        {
            'count_total': int,
            'count_enabled': int,
            'count_ipv6_default': int,
            'count_ipv6_dualstack': int,
            'count_ipv4_only': int,
            'count_nx': int,
        }
    """
    se_count = 0
    se_count_ipv6_default = 0
    se_count_ipv6_dualstack = 0
    se_count_ipv4_only = 0
    se_count_nx = 0

    for ep in endpoints:
        ep_default = ep.get('endpoint_default', {})
        ep_dualstack = ep.get('endpoint_dualstack', {})

        hostname_default = ep_default.get('hostname')
        hostname_dualstack = ep_dualstack.get('hostname')

        has_ipv6_default = ep_default.get('has_ipv6', False)
        has_ipv6_dualstack = ep_dualstack.get('has_ipv6', False)

        if not hostname_default and not hostname_dualstack:
            se_count_nx += 1
        elif has_ipv6_default:
            se_count += 1
            se_count_ipv6_default += 1
        elif has_ipv6_dualstack:
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


def load_endpoints_from_json(json_file):
    """
    Load endpoints from JSON file.

    Args:
        json_file: Path to JSON file

    Returns:
        List of endpoint dicts
    """
    with open(json_file, "r") as f:
        return json.load(f)


# =============================================================================
__all__ = [
    'get_available_services',
    'get_all_regions',
    'resolve_endpoint',
    'get_service_hostname',
    'collect_endpoints',
    'calculate_stats',
    'load_endpoints_from_json',
]

