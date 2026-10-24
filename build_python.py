#!/usr/bin/env python3

import os
import re
import sys
import argparse
import subprocess
import tempfile
import getpass
import requests


# https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input/3041990#3041990
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Builds specified Python version from sources and installs it to /usr/local/bin"
    )
    parser.add_argument("python_version", help="Python version to build (3.8,3.9,etc)")
    parser.add_argument(
        "-b", "--batch-mode", action="store_true", default=False, help="Batch mode (disables all prompts)"
    )
    options = parser.parse_args()
    if not re.fullmatch(r"3\.\d+", options.python_version):
        sys.exit(f"ERROR: invalid Python version '{options.python_version}' (expected 3.x)")

    return options


def get_system_python_version():
    return subprocess.check_output(
        ["/usr/bin/python3", "-c", "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')"],
        text=True,
    ).strip()


def get_latest_release(python_version):
    python_releases = requests.get("https://endoflife.date/api/python.json").json()
    release_info = next((x for x in python_releases if x["cycle"] == python_version), None)
    if not release_info:
        sys.exit(f"Can't find release info for Python version {python_version}")
    return release_info["latest"]


def install_packages(options):
    package_list = (
        "build-essential",
        "tk-dev",
        "libncurses5-dev",
        "libncursesw5-dev",
        "libreadline-dev",
        "libdb5.3-dev",
        "libgdbm-dev",
        "libsqlite3-dev",
        "libssl-dev",
        "libbz2-dev",
        "libexpat1-dev",
        "liblzma-dev",
        "zlib1g-dev",
        "libffi-dev",
    )

    print("Checking installed packages")
    apt_packages_to_install = []
    for apt_package in package_list:
        if (
            subprocess.run(  # pylint: disable=subprocess-run-check
                ["/usr/bin/dpkg-query", "-s", apt_package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        ).returncode != 0:
            apt_packages_to_install += [apt_package]

    if len(apt_packages_to_install) != 0:
        print(f"The following apt packages need to be installed: {apt_packages_to_install}")
        print("Updating apt package list")
        sudo_cmd = ["/usr/bin/sudo"]
        if options.batch_mode:
            sudo_cmd += ["-n"]
        sudo_cmd += ["--", "sh", "-c"]
        if options.batch_mode:
            apt_cmd = ["DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get -qq update"]
        else:
            apt_cmd = ["/usr/bin/apt-get update"]
        print(sudo_cmd + apt_cmd)
        subprocess.check_call(sudo_cmd + apt_cmd)

        print("Installing packages")
        # Convert to space-separated list
        apt_packages_to_install = " ".join(apt_packages_to_install)
        if options.batch_mode:
            apt_cmd = [
                (
                    "DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get -y -qq "
                    f"install {apt_packages_to_install}"
                )
            ]
        else:
            apt_cmd = [f"/usr/bin/apt-get -y -qq install {apt_packages_to_install}"]
        print(sudo_cmd + apt_cmd)
        subprocess.check_call(sudo_cmd + apt_cmd)


def build_python(options, release):
    download_url = f"https://www.python.org/ftp/python/{release}/Python-{release}.tgz"
    archive_name = f"Python-{release}.tgz"
    extracted_dir = f"Python-{release}"

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Downloading {download_url}")
        subprocess.check_call(["/usr/bin/curl", download_url, "--output", archive_name], cwd=temp_dir)
        print(f"Extracting {archive_name}")
        subprocess.check_call(["tar", "xzf", archive_name], cwd=temp_dir)
        build_dir = os.path.join(temp_dir, extracted_dir)
        print(f"Build directory: {build_dir}")
        build_env = os.environ.copy()
        if "/usr/bin" not in build_env["PATH"]:
            build_env["PATH"] += os.pathsep + "/usr/bin"
        subprocess.check_call(["./configure", "--enable-optimizations"], cwd=build_dir, env=build_env)
        # We used to call sudo_cmd + ["make", "altinstall", "-j", str(len(os.sched_getaffinity(0)))]
        # But Python 3.11 introduced a bug when 'altinstall -j' returns 2 even when
        # there is no error: https://github.com/python/cpython/issues/101295
        # Dividing in two separate calls for now to address this

        # Use all available CPU cores
        # https://stackoverflow.com/questions/1006289/how-to-find-out-the-number-of-cpus-using-python/55423170#55423170
        subprocess.check_call(
            ["make", "-j", str(len(os.sched_getaffinity(0)))], cwd=build_dir, env=build_env
        )
        print(f"\nRunning altinstall of {extracted_dir}")
        sudo_cmd = ["/usr/bin/sudo"]
        if options.batch_mode:
            sudo_cmd += ["-n"]

        # altinstall does not hide system Python binaries, just installs new
        # version alongside the system one
        subprocess.check_call(sudo_cmd + ["make", "altinstall"], cwd=build_dir, env=build_env)

        # Running make as root causes some files in the build directory to be
        # created with root as an owner. Changing the owner to current user
        # so that TemporaryDirectory cleanup code would not fail
        subprocess.check_call(
            sudo_cmd + ["chown", "-R", getpass.getuser(), build_dir],
        )


def main():
    options = parse_arguments()

    system_version = get_system_python_version()
    if system_version == options.python_version:
        sys.exit(f"ERROR: system Python is already version {system_version}")

    python_path = f"/usr/local/bin/python{options.python_version}"
    if os.path.isfile(python_path):
        print(f"{python_path} is already installed")
        sys.exit(0)

    release = get_latest_release(options.python_version)

    if not options.batch_mode:
        # Reopen /dev/tty when running script from a pipeline
        if not sys.stdin.isatty():
            sys.stdin = open("/dev/tty")
        print(
            f"This script will:\n"
            f" - Install build dependencies (apt)\n"
            f" - Download Python {release} sources, build them\n"
            f" - Install to {python_path}"
        )
        if not query_yes_no("Continue?"):
            sys.exit("Cancelled by user")

    install_packages(options)
    build_python(options, release)
    print(f"Python {release} has been installed to {python_path}")


if __name__ == "__main__":
    main()
