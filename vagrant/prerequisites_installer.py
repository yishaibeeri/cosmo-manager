import subprocess
import sys

__author__ = 'elip'


class PrerequisitesInstaller:

    def install(self):
        self._update_apt_registry()
        self._install_python_dev()
        self._install_python_pip()
        self._install_retrying()
        self._install_timeout()

    def _install_python_dev(self):
        return_code = subprocess.call(["sudo", "apt-get", "-y", "install", "python-dev"])
        if return_code != 0:
            raise subprocess.CalledProcessError(cmd="apt-get install python-dev", returncode=1, output=sys.stderr)

    def _install_python_pip(self):
        return_code = subprocess.call(["sudo", "apt-get", "-y", "install", "python-pip"])
        if return_code != 0:
            raise subprocess.CalledProcessError(cmd="apt-get install python-pip", returncode=1, output=sys.stderr)

    def _install_retrying(self):
        return_code = subprocess.call(["sudo", "pip", "install", "retrying"])
        if return_code != 0:
            raise subprocess.CalledProcessError(cmd="pip install retrying", returncode=1, output=sys.stderr)

    def _install_timeout(self):
        return_code = subprocess.call(["sudo", "pip", "install", "timeout-decorator"])
        if return_code != 0:
            raise subprocess.CalledProcessError(cmd="pip install timeout-decorator", returncode=1, output=sys.stderr)

    def _update_apt_registry(self):
        return_code = subprocess.call(["sudo", "apt-get", "-y", "update"])
        if return_code != 0:
            raise subprocess.CalledProcessError(cmd="apt-get update", returncode=1, output=sys.stderr)


if __name__ == '__main__':

    """
    These are needed to the cosmo installer and the bootstrap process.
    """

    installer = PrerequisitesInstaller()
    installer.install()