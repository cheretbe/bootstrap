#!/usr/bin/env python3

import os
import sys
import argparse
import subprocess
import tempfile
import getpass

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
        description="Wrapper script for Python virtual environments creation"
    )
    parser.add_argument(
        "venv_name",
        help="Virtual environments (relative to ~/.cache/venv/, not full path)"
    )
    parser.add_argument(
        "-r", "--requirement", default=None,
        help="Install additional pip packages from the given requirements file"
    )
    parser.add_argument(
        "-b", "--batch-mode", action="store_true", default=False,
        help="Batch mode (disables all prompts)"
    )
    parser.add_argument(
        "-p", "--python", choices=["system", "3.8", "3.9"], default="system",
        help="Python version to use (default: system)"
    )
    options = parser.parse_args()
    if os.path.sep in options.venv_name:
        sys.exit("ERROR: virtual environment name should be a directory name, not full path")

    return options

def install_packages(options):
    if options.python == "system":
        package_list = ("python3-venv", "python3-dev")
    else:
        package_list = (
            "build-essential", "tk-dev", "libncurses5-dev", "libncursesw5-dev",
            "libreadline-dev", "libdb5.3-dev", "libgdbm-dev", "libsqlite3-dev",
            "libssl-dev", "libbz2-dev", "libexpat1-dev", "liblzma-dev",
            "zlib1g-dev", "libffi-dev"
        )

    print("Checking installed packages")
    apt_packages_to_install = []
    for apt_package in package_list:
        if (subprocess.run( #pylint: disable=subprocess-run-check
                ["/usr/bin/dpkg-query", "-s", apt_package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
        )).returncode != 0:
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

def build_python(options):
    if options.python == "3.9":
        download_url = "https://www.python.org/ftp/python/3.9.5/Python-3.9.5.tgz"
        archive_name = "Python-3.9.5.tgz"
        extracted_dir = "Python-3.9.5"
        python_path = "/usr/local/bin/python3.9"
    elif options.python == "3.8":
        download_url = "https://www.python.org/ftp/python/3.8.10/Python-3.8.10.tgz"
        archive_name = "Python-3.8.10.tgz"
        extracted_dir = "Python-3.8.10"
        python_path = "/usr/local/bin/python3.8"
    else:
        sys.exit(f"Unsupported Python version: {options.python}")

    if not os.path.isfile(python_path):
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Downloading {download_url}")
            subprocess.check_call(
                ["/usr/bin/curl", download_url, "--output", archive_name],
                cwd=temp_dir
            )
            print(f"Extracting {archive_name}")
            subprocess.check_call(["tar", "xzf", archive_name], cwd=temp_dir)
            # subprocess.check_call(["ls", "-lha"], cwd=temp_dir)
            build_dir = os.path.join(temp_dir, extracted_dir)
            build_env = os.environ.copy()
            if "/usr/bin" not in build_env["PATH"]:
                build_env["PATH"] += os.pathsep + "/usr/bin"
            subprocess.check_call(
                ["./configure", "--enable-optimizations"],
                cwd=build_dir, env=build_env
            )
            # altinstall does not hide system Python binaries, just installs new
            # version alongside the system one
            print(f"\nRunning altinstall of {extracted_dir}")
            sudo_cmd = ["/usr/bin/sudo"]
            if options.batch_mode:
                sudo_cmd += ["-n"]
            subprocess.check_call(
                sudo_cmd + ["make", "altinstall"],
                cwd=build_dir, env=build_env
            )
            # Running make as root causes some files in the build directory to be
            # created with root as an owner. Changing the owner to current user
            # so that TemporaryDirectory cleanup code would not fail
            subprocess.check_call(
                sudo_cmd + ["chown", "-R", getpass.getuser(), build_dir],
            )
    return python_path


def main():
    options = parse_arguments()

    venv_path = os.path.expanduser(f"~/.cache/venv/{options.venv_name}")
    if os.path.isdir(venv_path):
        sys.exit(0)

    if not options.batch_mode:
        # Reopen /dev/tty when running script from a pipeline
        if not sys.stdin.isatty():
            sys.stdin = open("/dev/tty")
        print("A Python 3 virtual environment needs to be created for this script to run")
        if not query_yes_no(f"Would you like to setup venv '{venv_path}' now?"):
            sys.exit("Cancelled by user")
    print(f"Creating venv '{venv_path}'")

    install_packages(options)
    # sys.exit(0)

    if options.python == "system":
        python_path = "/usr/bin/python3"
    else:
        python_path = build_python(options)

    print([python_path, "-m", "venv", venv_path])
    subprocess.check_call([python_path, "-m", "venv", venv_path])
    pip_cmd = (
        f". {venv_path}/bin/activate &&\n"
        "pip3 install --disable-pip-version-check wheel &&\n"
        "pip3 install --upgrade pip &&\n"
    )
    if options.requirement is not None:
        pip_cmd += f"pip3 install -r {options.requirement} &&\n"
    pip_cmd += "deactivate"
    pip_env = os.environ.copy()
    if "/usr/bin" not in pip_env["PATH"].split(os.pathsep):
        pip_env["PATH"] += f"{os.pathsep}/usr/bin"
    print(pip_cmd)
    subprocess.check_call(pip_cmd, shell=True, env=pip_env)


if __name__ == "__main__":
    main()
