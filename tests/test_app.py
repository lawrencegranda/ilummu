"""Test application factory and configuration for the Edify platform."""

# Standard Library imports
import os
import subprocess

# Local Application imports
from edify import create_app


def create_test_app():
    """Create Flask application instance with test configuration."""
    # Path to your env test script
    env_script = "env.test.sh"

    # Execute the script and capture the output using context manager
    with subprocess.Popen(
        ["bash", "-c", f"source {env_script} && env"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as process:
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print("Error activating environment:", stderr.decode())
            raise RuntimeError("Error.")

        # Set environment variables in the current Python environment
        for line in stdout.decode().splitlines():
            key, _, value = line.partition("=")
            os.environ[key] = value

    print("Environment variables set successfully.")

    # pylint: disable=import-outside-toplevel
    from edify.config import Config

    return create_app(Config)
