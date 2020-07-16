import os

import pytest

from test.test_utils import CONTAINER_TESTS_PREFIX
from test.test_utils.ec2 import execute_ec2_training_performance_test


MX_PERFORMANCE_TRAINING_GPU_CMD = os.path.join(CONTAINER_TESTS_PREFIX, "benchmark", "run_mxnet_training_performance_gpu")
MX_PERFORMANCE_TRAINING_CPU_CMD = os.path.join(CONTAINER_TESTS_PREFIX, "benchmark", "run_mxnet_training_performance_cpu")

MX_EC2_GPU_INSTANCE_TYPE = "p3.16xlarge"
MX_EC2_CPU_INSTANCE_TYPE = "c5.18xlarge"


@pytest.mark.integration("single node gpu training performance benchmark w/ imagenet dataset")
@pytest.mark.model("resnet50_v2")
@pytest.mark.parametrize("ec2_instance_type", [MX_EC2_GPU_INSTANCE_TYPE], indirect=True)
def test_performance_ec2_mxnet_training_gpu(mxnet_training, ec2_connection, gpu_only):
    execute_ec2_training_performance_test(ec2_connection, mxnet_training, MX_PERFORMANCE_TRAINING_GPU_CMD)


@pytest.mark.integration("single node cpu training performance benchmark w/ cifar10 dataset")
@pytest.mark.model("resnet18_v2")
@pytest.mark.parametrize("ec2_instance_type", [MX_EC2_CPU_INSTANCE_TYPE], indirect=True)
def test_performance_ec2_mxnet_training_cpu(mxnet_training, ec2_connection, cpu_only):
    execute_ec2_training_performance_test(ec2_connection, mxnet_training, MX_PERFORMANCE_TRAINING_CPU_CMD)
