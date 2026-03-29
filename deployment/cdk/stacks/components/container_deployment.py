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

"""Main construct to build and push the container resources to ECR"""

from aws_cdk import (
    Environment,
    aws_iam as iam,
    aws_ecr_assets as ecr_assets,
    CfnOutput
)
import cdk_ecr_deployment
from constructs import Construct
import os

from stacks.components.ecr import Ecr

class ContainerDeployment(Construct):
    """Class for Container Deployment Construct"""
    def __init__(
            self,
            scope: Construct,
            id: str,
            config_data: dict,
            build_args: dict,
            dockerfile_path: str,
            env: Environment,
            ecr: Ecr,
            **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        try:
            # Validate input parameters
            if not dockerfile_path or not os.path.exists(dockerfile_path):
                raise ValueError(f"Invalid dockerfile path: {dockerfile_path}")
            if not os.path.exists(os.path.join(dockerfile_path, "Dockerfile")):
                raise ValueError(f"Dockerfile not found in {dockerfile_path}")

            # Create deployment role with required permissions
            deployment_role = iam.Role(
                self,
                "ECRDeploymentRole",
                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name(
                        "service-role/AWSLambdaBasicExecutionRole"
                    )
                ]
            )

            # Add ECR permissions
            deployment_role.add_to_policy(
                iam.PolicyStatement(
                    actions=[
                        "ecr:GetAuthorizationToken",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:GetRepositoryPolicy",
                        "ecr:DescribeRepositories",
                        "ecr:ListImages",
                        "ecr:DescribeImages",
                        "ecr:BatchGetImage",
                        "ecr:InitiateLayerUpload",
                        "ecr:UploadLayerPart",
                        "ecr:CompleteLayerUpload",
                        "ecr:PutImage"
                    ],
                    resources=[ecr.repository.repository_arn]
                )
            )

            # Build and assign the docker image for ECR
            self.asset = ecr_assets.DockerImageAsset(
                self,
                "DockerImage",
                directory=dockerfile_path,
                build_args=build_args,
                platform=ecr_assets.Platform.LINUX_AMD64,
                #cache_disabled=True
            )

            # Copy image from cdk docker image asset to ECR
            self.deployment = cdk_ecr_deployment.ECRDeployment(
                self,
                "DeployDockerImage",
                src=cdk_ecr_deployment.DockerImageName(self.asset.image_uri),
                dest=cdk_ecr_deployment.DockerImageName(
                    ecr.repository.repository_uri
                ),
                role=deployment_role,
                memory_limit=512,
            )

            # Add dependencies
            if hasattr(self.asset, "node"):
                self.deployment.node.add_dependency(self.asset)

            # Add outputs
            CfnOutput(
                self,
                "DockerImageUri",
                value=self.asset.image_uri,
                description="URI of the built Docker image"
            )

            CfnOutput(
                self,
                "ECRRepositoryUri",
                value=ecr.repository.repository_uri,
                description="URI of the ECR repository"
            )

        except Exception as e:
            print(f"Error in ContainerDeployment construct: {e}")
            raise e

    @property
    def image_uri(self) -> str:
        """Return the URI of the deployed Docker image"""
        return self.asset.image_uri if hasattr(self, 'asset') else None

    @property
    def deployment_role(self) -> iam.Role:
        """Return the deployment role"""
        return self.deployment.role if hasattr(self, 'deployment') else None

    def add_to_role_policy(self, statement: iam.PolicyStatement):
        """Add additional permissions to the deployment role"""
        if self.deployment_role:
            self.deployment_role.add_to_policy(statement)
