#!/usr/bin/env python3

import os
from constructs import Construct

import aws_cdk as cdk
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as cloudfront_origins
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_certificatemanager as acm

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
            default_root_object = "intro/index.html",
            default_behavior = cloudfront.BehaviorOptions(
                origin = s3_origin,
                viewer_protocol_policy = cloudfront.ViewerProtocolPolicy.ALLOW_ALL,
                # It seems necessary to pass the headers to the origin so that Cloudfront actually does compression.
                origin_request_policy = cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                cache_policy = cf_cache_policy,
                function_associations = [cloudfront.FunctionAssociation(
                    function = cf_index_function,
                    event_type = cloudfront.FunctionEventType.VIEWER_REQUEST,
                )],
            ),
            additional_behaviors = {
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

app = cdk.App()

cert_stack = Awsipv6CertStack(app, "Awsipv6CertStack", env = cdk.Environment(region = "us-east-1"))

Awsipv6CdnStack(app, f"Awsipv6CdnStack",
    env = cdk.Environment(region = REGION),
    cf_certificate = cert_stack.cert,
    cross_region_references = True,
)

app.synth()
