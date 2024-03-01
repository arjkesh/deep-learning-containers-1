import pytest

import test.test_utils as test_utils

from test.dlc_tests.ec2.pytorch.training import common_cases
from test.dlc_tests.ec2 import smclarify_cases


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("all PT 2.2 tests")
@pytest.mark.model("N/A")
@pytest.mark.team("conda")
@pytest.mark.parametrize("ec2_instance_type", common_cases.PT_EC2_GPU_INSTANCE_TYPE, indirect=True)
def test_pytorch_2_2_gpu(
    pytorch_training___2__2, ec2_connection, region, gpu_only, ec2_instance_type
):
    pytorch_training = pytorch_training___2__2
    if test_utils.is_image_incompatible_with_instance_type(pytorch_training, ec2_instance_type):
        pytest.skip(
            f"Image {pytorch_training} is incompatible with instance type {ec2_instance_type}"
        )

    test_cases = [
        (common_cases.pytorch_standalone, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_train_mnist, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_linear_regression_gpu, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_gloo, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_gloo_inductor_gpu, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_nccl, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_nccl_inductor, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_mpi, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_mpi_inductor_gpu, (pytorch_training, ec2_connection)),
        (common_cases.nvapex, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_amp, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_amp_inductor, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_training_torchaudio, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_training_torchdata, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_cudnn_match_gpu, (pytorch_training, ec2_connection, region)),
    ]

    if "sagemaker" in pytorch_training:
        test_cases += [
            (smclarify_cases.smclarify_metrics_gpu, (pytorch_training, ec2_connection)),
        ]

    test_utils.execute_serial_test_cases(test_cases, test_description="PT 2.2 GPU")


@pytest.mark.usefixtures("sagemaker")
@pytest.mark.integration("pytorch_sanity_test")
@pytest.mark.model("N/A")
@pytest.mark.team("conda")
@pytest.mark.parametrize("ec2_instance_type", common_cases.PT_EC2_CPU_INSTANCE_TYPE, indirect=True)
def test_pytorch_standalone_cpu(pytorch_training___2__2, ec2_connection, cpu_only):
    pytorch_training = pytorch_training___2__2
    test_cases = [
        (common_cases.pytorch_standalone, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_train_mnist, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_linear_regression_cpu, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_gloo, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_mpi, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_training_torchaudio, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_training_torchdata, (pytorch_training, ec2_connection)),
        (common_cases.pytorch_telemetry_cpu, (pytorch_training, ec2_connection)),
    ]

    if "sagemaker" in pytorch_training:
        test_cases += [
            (smclarify_cases.smclarify_metrics_cpu, (pytorch_training, ec2_connection)),
        ]

    test_utils.execute_serial_test_cases(test_cases, test_description="PT 2.2 CPU")
