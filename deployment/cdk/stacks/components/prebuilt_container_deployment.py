# MIT License
#
# Copyright (c) 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY

"""Construct to reference an existing ECR container"""

from aws_cdk import (
    Environment,
    aws_iam as iam,
    aws_ecr as ecr_repo,
    CfnOutput
)
from constructs import Construct
import os

class PrebuiltContainerDeployment(Construct):
    """Class for Prebuilt Container Deployment Construct"""
    def __init__(
            self,
            scope: Construct,
            id: str,
            ecr_arn: str,
            env: Environment,
            **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        try:
            # Validate input parameters
            if not ecr_arn:
                raise ValueError("ecr_arn is required")

            # Reference the existing repository
            self.repository = ecr_repo.Repository.from_repository_arn(
                self,
                "ImportedEcrRepo",
                ecr_arn
            )

            # Create deployment role with required permissions
            self.deployment_role = iam.Role(
                self,
                "ECRDeploymentRole",
                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name(
                        "service-role/AWSLambdaBasicExecutionRole"
                    )
                ]
            )

            # Add ECR permissions to access the existing image
            self.deployment_role.add_to_policy(
                iam.PolicyStatement(
                    actions=[
                        "ecr:GetAuthorizationToken",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:GetRepositoryPolicy",
                        "ecr:DescribeRepositories",
                        "ecr:ListImages",
                        "ecr:DescribeImages",
                        "ecr:BatchGetImage"
                    ],
                    resources=[ecr_arn]
                )
            )

            # Add outputs
            CfnOutput(
                self,
                "ECRRepositoryUri",
                value=self.repository.repository_uri,
                description="URI of the referenced ECR repository"
            )

        except Exception as e:
            print(f"Error in PrebuiltContainerDeployment construct: {e}")
            raise e

    def add_to_role_policy(self, statement: iam.PolicyStatement):
        """Add additional permissions to the deployment role"""
        if self.deployment_role:
            self.deployment_role.add_to_policy(statement)
