#!/usr/bin/env python3

import os
from constructs import Construct

import aws_cdk as cdk
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as cloudfront_origins
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_iam as iam
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_logs as logs
from aws_cdk import aws_dsql as dsql
from aws_cdk import aws_lambda as awslambda

REGION = "eu-west-1"

class Awsipv6CertStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.cert = acm.Certificate(self, f"Awsipv6Certificate",
            domain_name = "awsipv6.neveragain.de",
            validation = acm.CertificateValidation.from_dns(), # manual
        )

class Awsipv6CdnStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, cf_certificate, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cf_cache_policy = cloudfront.CachePolicy(self, f"Awsipv6CachePolicy",
            cache_policy_name = f"Awsipv6CachePolicy",
            default_ttl = cdk.Duration.hours(6),
            min_ttl = cdk.Duration.seconds(60),
            max_ttl = cdk.Duration.hours(24),
            enable_accept_encoding_brotli = True,
            enable_accept_encoding_gzip = True,
            query_string_behavior = cloudfront.CacheQueryStringBehavior.all(),
            cookie_behavior = cloudfront.CacheCookieBehavior.allow_list("regions")
        )

        s3_origin = cloudfront_origins.S3BucketOrigin.with_bucket_defaults(
            origin_id = "awsipv6-bucket",
            bucket = s3.Bucket.from_bucket_attributes(self, f"Awsipv6Bucket",
                bucket_name = "awsipv6",
                bucket_regional_domain_name = "awsipv6.s3.eu-central-1.amazonaws.com",
            ),
        )

        cf_index_function = cloudfront.Function(self, f"Awsipv6IndexFunction",
            runtime = cloudfront.FunctionRuntime.JS_2_0,
            code = cloudfront.FunctionCode.from_inline("""
                function handler(event) {
                    if (event.request.uri.endsWith('/') && event.request.uri !== '/')
                        event.request.uri += 'index.html';

                    return event.request;
                }
            """),
        )

        cf_distribution = cloudfront.Distribution(self, f"Awsipv6Distribution",
            comment = "Awsipv6",
            domain_names = ["awsipv6.neveragain.de"],
            certificate = cf_certificate,
            enable_ipv6 = True,
            # default_root_object = "awsipv6-main",
            http_version = cloudfront.HttpVersion.HTTP2_AND_3,
            default_root_object = "awsipv6-main",
            default_behavior = cloudfront.BehaviorOptions(
                origin = s3_origin,
                viewer_protocol_policy = cloudfront.ViewerProtocolPolicy.ALLOW_ALL,
                # It seems necessary to pass the headers to the origin so that Cloudfront actually does compression.
                origin_request_policy = cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                cache_policy = cf_cache_policy,
            ),
            additional_behaviors = {
                "/awsipv6-*": cloudfront.BehaviorOptions(
                    origin = cloudfront_origins.FunctionUrlOrigin.with_origin_access_control(
                        live_stack.backend_function_url,
                        origin_id = "awsipv6-lambda-live",
                    ),
                    viewer_protocol_policy = cloudfront.ViewerProtocolPolicy.ALLOW_ALL,
                    cache_policy = cf_cache_policy,
                    allowed_methods = cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                    origin_request_policy = cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                    response_headers_policy = cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS_WITH_PREFLIGHT,
                ),
                "/beta/awsipv6-*": cloudfront.BehaviorOptions(
                    origin = cloudfront_origins.FunctionUrlOrigin.with_origin_access_control(
                        beta_stack.backend_function_url,
                        origin_id = "awsipv6-lambda-beta",
                    ),
                    viewer_protocol_policy = cloudfront.ViewerProtocolPolicy.ALLOW_ALL,
                    cache_policy = cloudfront.CachePolicy.CACHING_DISABLED, # differs from live
                    allowed_methods = cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                    origin_request_policy = cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                    response_headers_policy = cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS_WITH_PREFLIGHT,
                ),
                "/beta/*": cloudfront.BehaviorOptions(
                    origin = s3_origin,
                    viewer_protocol_policy = cloudfront.ViewerProtocolPolicy.ALLOW_ALL,
                    origin_request_policy = cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                    cache_policy = cloudfront.CachePolicy.CACHING_DISABLED,
                    function_associations = [cloudfront.FunctionAssociation(
                        function = cf_index_function,
                        event_type = cloudfront.FunctionEventType.VIEWER_REQUEST,
                    )],
                ),
            },
        )

        cdk.Tags.of(cf_distribution).add("Name", "Awsipv6")

class Awsipv6Stack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        """
        create role be_read login;
        aws iam grant be_read to 'arn:aws:iam::329261680777:role/Awsipv6Stack-Awsipv6BackendServiceRole9C6C370D-VRoQ71oeneEx';
        create table endpoint (
            service_name text not null,
            partition_name text not null,
            region_name text not null,
            endpoint_default_hostname text,
            endpoint_default_has_ipv4 bool,
            endpoint_default_has_ipv6 bool,
            endpoint_dualstack_hostname text,
            endpoint_dualstack_has_ipv4 bool,
            endpoint_dualstack_has_ipv6 bool,
            primary key (service_name, partition_name, region_name)
        );
        create table region (
            region_name text not null,
            partition_name text not null,
            description text not null,
            primary key (region_name, partition_name)
        );
        grant select on endpoint, region to be_read;

        The "update-data" scripts use a DSQL "admin" token, so do not need to be known
        to the database via AWS IAM GRANT. The deployment role (awsipv6-github) does
        need IAM permissions for DSQL accordingly.
        """
        dsql_cluster = dsql.CfnCluster(self, f"Awsipv6DsqlCluster",
            deletion_protection_enabled = False,
        )
        cdk.Tags.of(dsql_cluster).add("Name", "Awsipv6")
        dsql_endpoint = f"{dsql_cluster.attr_identifier}.dsql.{REGION}.on.aws"

        """
        pip install \
            --platform manylinux2014_aarch64 \
            --python-version 3.13 \
            --target python-dependencies/python \
            --only-binary=:all: \
            psycopg-binary
        """
        dependencies = awslambda.LayerVersion(self, f"Awsipv6Dependencies",
            code = awslambda.Code.from_asset(os.path.join(os.path.dirname(__file__), ".pydep")),
            compatible_runtimes = [awslambda.Runtime.PYTHON_3_13],
        )

        backend = awslambda.Function(self, f"Awsipv6Backend",
            runtime = awslambda.Runtime.PYTHON_3_13,
            function_name = f"Awsipv6Backend",
            handler = "index.handler",
            code = awslambda.Code.from_asset(os.path.join(os.path.dirname(__file__), "web/src")),
            layers = [dependencies],
            architecture = awslambda.Architecture.ARM_64,
            memory_size = 1769,
            timeout = cdk.Duration.seconds(15),
            log_group = logs.LogGroup(self, f"Awsipv6BackendLogGroup",
                log_group_name = f"/aws/lambda/Awsipv6Backend",
                removal_policy = cdk.RemovalPolicy.DESTROY,
                retention = logs.RetentionDays.ONE_MONTH,
            ),
            environment = {
                "DSQL_ENDPOINT": dsql_endpoint,
            },
        )

        backend.role.attach_inline_policy(iam.Policy(self, f"Awsipv6BackendPolicy", statements = [
            iam.PolicyStatement(
                actions = ["dsql:DbConnect"],
                resources = [dsql_cluster.attr_resource_arn],
            ),
        ]))

        self.backend_function_url = backend.add_function_url(auth_type = awslambda.FunctionUrlAuthType.AWS_IAM)

        """
        aws cloudformation describe-stacks --stack-name Awsipv6Stack \
        | jq -j '.Stacks[].Outputs[] | select(.OutputKey == "BackendLambdaRoleArn") | .OutputValue'
        """
        cdk.CfnOutput(self, "BackendLambdaRoleArn", value = backend.role.role_arn)
        cdk.CfnOutput(self, "DsqlClusterEndpoint", value = dsql_endpoint)

class Awsipv6BetaStack(cdk.Stack):
    # This duplicates a lot (usually: all) of the Live stack's code, but this seemed more
    # reasonable than hacking around each time only the Beta version should be modified.

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        dsql_cluster = dsql.CfnCluster(self, f"Awsipv6BetaDsqlCluster",
            deletion_protection_enabled = False,
        )
        cdk.Tags.of(dsql_cluster).add("Name", "Awsipv6Beta")
        dsql_endpoint = f"{dsql_cluster.attr_identifier}.dsql.{REGION}.on.aws"

        dependencies = awslambda.LayerVersion(self, f"Awsipv6BetaDependencies",
            code = awslambda.Code.from_asset(os.path.join(os.path.dirname(__file__), ".pydep")),
            compatible_runtimes = [awslambda.Runtime.PYTHON_3_13],
        )

        backend = awslambda.Function(self, f"Awsipv6BetaBackend",
            runtime = awslambda.Runtime.PYTHON_3_13,
            function_name = f"Awsipv6BetaBackend",
            handler = "index.handler",
            code = awslambda.Code.from_asset(os.path.join(os.path.dirname(__file__), "web/src")),
            layers = [dependencies],
            architecture = awslambda.Architecture.ARM_64,
            memory_size = 1769,
            timeout = cdk.Duration.seconds(15),
            log_group = logs.LogGroup(self, f"Awsipv6BetaBackendLogGroup",
                log_group_name = f"/aws/lambda/Awsipv6BetaBackend",
                removal_policy = cdk.RemovalPolicy.DESTROY,
                retention = logs.RetentionDays.ONE_MONTH,
            ),
            environment = {
                "DSQL_ENDPOINT": dsql_endpoint,
            },
        )

        backend.role.attach_inline_policy(iam.Policy(self, f"Awsipv6BetaBackendPolicy", statements = [
            iam.PolicyStatement(
                actions = ["dsql:DbConnect"],
                resources = [dsql_cluster.attr_resource_arn],
            ),
        ]))

        self.backend_function_url = backend.add_function_url(auth_type = awslambda.FunctionUrlAuthType.AWS_IAM)

        cdk.CfnOutput(self, "BackendLambdaRoleArn", value = backend.role.role_arn)
        cdk.CfnOutput(self, "DsqlClusterEndpoint", value = dsql_endpoint)

app = cdk.App()

live_stack = Awsipv6Stack(app, f"Awsipv6Stack", env = cdk.Environment(region = REGION))
beta_stack = Awsipv6BetaStack(app, f"Awsipv6BetaStack", env = cdk.Environment(region = REGION))

cert_stack = Awsipv6CertStack(app, "Awsipv6CertStack", env = cdk.Environment(region = "us-east-1"))

Awsipv6CdnStack(app, f"Awsipv6CdnStack",
    env = cdk.Environment(region = REGION),
    cf_certificate = cert_stack.cert,
    cross_region_references = True,
)

app.synth()
