import os

import pytest

from test.test_utils import CONTAINER_TESTS_PREFIX, LOGGER, is_tf2, is_tf1
from test.test_utils.ec2 import get_ec2_instance_type


SMDEBUG_SCRIPT = os.path.join(CONTAINER_TESTS_PREFIX, "testSmdebug")


SMDEBUG_EC2_GPU_INSTANCE_TYPE = get_ec2_instance_type(default="p2.8xlarge", processor="gpu")
SMDEBUG_EC2_CPU_INSTANCE_TYPE = get_ec2_instance_type(default="m4.16xlarge", processor="cpu")


@pytest.mark.integration("smdebug")
@pytest.mark.model("mnist")
@pytest.mark.parametrize("ec2_instance_type", SMDEBUG_EC2_GPU_INSTANCE_TYPE, indirect=True)
@pytest.mark.flaky(reruns=0)
def test_smdebug_gpu(training, ec2_connection, region, ec2_instance_type, gpu_only, py3_only):
    #if is_tf1(training):
        #pytest.skip("Currently skipping for TF1 until the issue is fixed")
    run_smdebug_test(training, ec2_connection, region, ec2_instance_type,
                     docker_executable="nvidia-docker", container_name="smdebug-gpu")


@pytest.mark.flaky(reruns=0)
@pytest.mark.integration("smdebug")
@pytest.mark.model("mnist")
@pytest.mark.parametrize("ec2_instance_type", SMDEBUG_EC2_CPU_INSTANCE_TYPE, indirect=True)
def test_smdebug_cpu(training, ec2_connection, region, ec2_instance_type, cpu_only, py3_only):
    # TODO: Remove this once test timeout has been debugged (failures especially on m4.16xlarge)
    #if is_tf1(training):
        #pytest.skip("Currently skipping for TF1 until the issue is fixed")
    run_smdebug_test(training, ec2_connection, region, ec2_instance_type)


def run_smdebug_test(
    image_uri,
    ec2_connection,
    region,
    ec2_instance_type,
    docker_executable="docker",
    container_name="smdebug",
    test_script=SMDEBUG_SCRIPT,
):
    large_shm_instance_types = ("p2.8xlarge", "m4.16xlarge")
    shm_setting = ' --shm-size="1g" ' if ec2_instance_type in large_shm_instance_types else " "
    framework = get_framework_from_image_uri(image_uri)
    container_test_local_dir = os.path.join("$HOME", "container_tests")
    ec2_connection.run(f"$(aws ecr get-login --no-include-email --region {region})", hide=True)

    try:
        ec2_connection.run(
            f"{docker_executable} run --name {container_name} -v "
            f"{container_test_local_dir}:{os.path.join(os.sep, 'test')}{shm_setting}{image_uri} "
            f"/bin/bash -c '{test_script} {framework}'",
            hide=True,
            timeout=3000
        )
    except Exception:
        debug_output = ec2_connection.run(f"docker logs {container_name}")
        LOGGER.error(f"Caught exception while trying to run test via fabric. Output: {debug_output.stdout}")
        raise


def get_framework_from_image_uri(image_uri):
    frameworks = ("tensorflow", "mxnet", "pytorch")
    for framework in frameworks:
        if framework in image_uri:
            if framework == "tensorflow" and is_tf2(image_uri):
                return "tensorflow2"
            return framework
    raise RuntimeError(f"Could not find any framework {frameworks} in {image_uri}")
