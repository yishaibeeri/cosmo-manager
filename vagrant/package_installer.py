from subprocess import CalledProcessError

import subprocess
import sys

__author__ = 'elip'

from retrying import retry
import timeout_decorator


class PackageInstaller:

    def __init__(self):
        # install fabric to run all other commands.
        self.install_fabric()


    @retry(stop='stop_after_attempt', stop_max_attempt_number=3, wait_fixed=3000)
    def install_fabric(self):
        return_code = subprocess.call(["sudo", "pip", "install", "fabric"])
        if return_code != 0:
            raise CalledProcessError(cmd="pip install fabric", returncode=1, output=sys.stderr)


    # Runs the command with a timeout of 10 minutes.
    # Since most command are downloads, we assume that if 10 minutes are not enough
    # then something is wrong. so we kill the process and let the retry decorator execute it again.
    @timeout_decorator.timeout(60 * 10)
    def run_with_timeout(self, command):
        self.run_fabric(command)

    @retry(stop='stop_after_attempt', stop_max_attempt_number=3, wait_fixed=3000)
    def run_with_retry_and_timeout(self, command):
        try:
            self.run_with_timeout(command)
        except SystemExit:  # lrun does not throw exception, but just exists the process
            raise CalledProcessError(cmd=command, returncode=1, output=sys.stderr)

    def run_fabric(self, command):
        from fabric.api import local as lrun
        print command
        lrun(command)

    def pip(self, package):
        self.run_with_retry_and_timeout("sudo pip install --timeout=120 {0}".format(package))

    def apt_get_update(self):
        self.run_with_retry_and_timeout("sudo apt-get -q update")

    def apt_get_install(self, package):
        self.run_with_retry_and_timeout("sudo apt-get install -y {0}".format(package))

    def add_apt(self, repo):
        self.run_with_retry_and_timeout("sudo add-apt-repository -y {0}".format(repo))

    def apt_key(self, key_file):
        self.run_with_retry_and_timeout("sudo apt-key add {0}".format(key_file))

    def wget(self, url, target_dir):
        self.run_with_retry_and_timeout("wget {0} -P {1}/".format(url, target_dir))