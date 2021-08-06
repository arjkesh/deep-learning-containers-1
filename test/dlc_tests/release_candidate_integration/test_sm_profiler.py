import os
import json
import yaml

import pytest

from invoke.context import Context

from test.test_utils import (
    is_mainline_context,
    get_container_name,
    get_framework_and_version_from_tag,
    get_processor_from_image_uri,
    is_tf_version,
    LOGGER,
)


@pytest.mark.integration("smprofiler")
@pytest.mark.model("N/A")
# @pytest.mark.skipif(not is_mainline_context(), reason="Mainline only test")
def test_sm_profiler_pt(pytorch_training):
    processor = get_processor_from_image_uri(pytorch_training)
    if processor not in ("cpu", "gpu"):
        pytest.skip(f"Processor {processor} not supported. Skipping test.")

    ctx = Context()

    profiler_tests_dir = os.path.join(
        os.getenv("CODEBUILD_SRC_DIR"), get_container_name("smprof", pytorch_training), "smprofiler_tests"
    )
    ctx.run(f"mkdir -p {profiler_tests_dir}", hide=True)

    # Download sagemaker-tests zip
    sm_tests_zip = "sagemaker-tests.zip"
    ctx.run(
        f"aws s3 cp {os.getenv('SMPROFILER_TESTS_BUCKET')}/{sm_tests_zip} {profiler_tests_dir}/{sm_tests_zip}",
        hide=True,
    )

    # PT test setup requirements
    with ctx.prefix(f"cd {profiler_tests_dir}"):
        ctx.run(f"unzip {sm_tests_zip}", hide=True)
        with ctx.prefix("cd sagemaker-tests/tests/scripts/pytorch_scripts"):
            ctx.run("mkdir -p data", hide=True)
            ctx.run(
                "aws s3 cp s3://smdebug-testing/datasets/cifar-10-python.tar.gz data/cifar-10-batches-py.tar.gz",
                hide=True,
            )
            ctx.run("aws s3 cp s3://smdebug-testing/datasets/MNIST_pytorch.tar.gz data/MNIST_pytorch.tar.gz", hide=True)
            with ctx.prefix("cd data"):
                ctx.run("tar -zxf MNIST_pytorch.tar.gz", hide=True)
                ctx.run("tar -zxf cifar-10-batches-py.tar.gz", hide=True)

    run_sm_profiler_tests(pytorch_training, profiler_tests_dir, "test_profiler_pytorch.py", processor)


@pytest.mark.integration("smprofiler")
@pytest.mark.model("N/A")
# @pytest.mark.skipif(not is_mainline_context(), reason="Mainline only test")
def test_sm_profiler_tf(tensorflow_training):
    if is_tf_version("1", tensorflow_training):
        pytest.skip("Skipping test on TF1, since there are no smprofiler config files for TF1")
    processor = get_processor_from_image_uri(tensorflow_training)
    if processor not in ("cpu", "gpu"):
        pytest.skip(f"Processor {processor} not supported. Skipping test.")

    ctx = Context()

    profiler_tests_dir = os.path.join(
        os.getenv("CODEBUILD_SRC_DIR"), get_container_name("smprof", tensorflow_training), "smprofiler_tests"
    )
    ctx.run(f"mkdir -p {profiler_tests_dir}", hide=True)

    # Download sagemaker-tests zip
    sm_tests_zip = "sagemaker-tests.zip"
    ctx.run(f"aws s3 cp s3://smprofiler-test-artifacts/{sm_tests_zip} {profiler_tests_dir}/{sm_tests_zip}", hide=True)
    ctx.run(f"cd {profiler_tests_dir} && unzip {sm_tests_zip}", hide=True)

    # Install tf datasets
    ctx.run(
        f"echo 'tensorflow-datasets==4.0.1' >> {profiler_tests_dir}/sagemaker-tests/tests/scripts/tf_scripts/requirements.txt",
        hide=True,
    )

    run_sm_profiler_tests(tensorflow_training, profiler_tests_dir, "test_profiler_tensorflow.py", processor)


class SMProfilerRCTestFailure(Exception):
    pass


def run_sm_profiler_tests(image, profiler_tests_dir, test_file, processor):
    """
    Testrunner to execute SM profiler tests from DLC repo
    """
    ctx = Context()
    ctx.run(
        f"pip install -r https://raw.githubusercontent.com/awslabs/sagemaker-debugger/master/config/profiler/requirements.txt && pip install pytest==5.3.5",
        hide=True,
        warn=True,
    )

    # Collect env variables for tests
    framework, version = get_framework_and_version_from_tag(image)

    # TODO: remove when SMDebug adds a 1.9.0 pytorch specfile
    if framework == "pytorch" and version == "1.9.0":
        version = "1.8.0"
    spec_file = f"buildspec_profiler_sagemaker_{framework}_{version.replace('.', '_')}_integration_tests.yml"

    # Get buildspec file from GitHub
    # Note: SMDebug seems to update these in master, not necessarily in feature branches, hence using master branch
    ctx.run(
        f"wget https://raw.githubusercontent.com/awslabs/sagemaker-debugger/master/config/profiler/{spec_file}",
        hide=True,
    )
    with open(spec_file, "r") as sf:
        yml_envs = yaml.safe_load(sf)
        spec_file_envs = yml_envs.get("env", {}).get("variables")

    # Command to set all necessary environment variables
    export_cmd = " && ".join(f"export {key}={val}" for key, val in spec_file_envs.items())
    export_cmd = f"{export_cmd} && export ENV_CPU_TRAIN_IMAGE=test && export ENV_GPU_TRAIN_IMAGE=test && export ENV_{processor.upper()}_TRAIN_IMAGE={image}"

    test_results_outfile = os.path.join(os.getcwd(), f"{get_container_name('smprof', image)}.txt")
    with ctx.prefix(f"cd {profiler_tests_dir}"):
        with ctx.prefix(f"cd sagemaker-tests && {export_cmd}"):
            try:
                ctx.run(
                    f"pip install smdebug && pytest --json-report --json-report-file={test_results_outfile} -n=auto -v -s -W=ignore tests/{test_file}::test_{processor}_jobs",
                    hide=True,
                )
                with open(test_results_outfile) as outfile:
                    result_data = json.load(outfile)
                    LOGGER.info(f"Tests passed on {image}; Results:\n{json.dumps(result_data, indent=4)}")
            except Exception as e:
                if os.path.exists(test_results_outfile):
                    with open(test_results_outfile) as outfile:
                        result_data = json.load(outfile)
                    raise SMProfilerRCTestFailure(
                        f"Failed SM Profiler tests. Results:\n{json.dumps(result_data, indent=4)}"
                    ) from e
                raise
