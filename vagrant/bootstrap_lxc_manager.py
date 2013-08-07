#/*******************************************************************************
# * Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
# *
# * Licensed under the Apache License, Version 2.0 (the "License");
# * you may not use this file except in compliance with the License.
# * You may obtain a copy of the License at
# *
# *       http://www.apache.org/licenses/LICENSE-2.0
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.
# *******************************************************************************/

import argparse
import os
from os.path import expanduser
import subprocess
import sys

__author__ = 'elip'

USER_HOME = expanduser('~')
JAVA_OPTS = "-Xms512m -Xmx1024m -XX:PermSize=128m"


class VagrantLxcBoot:

    """
    This class boots a cosmo management machine with all necessary components.
    The management machine itself is a virtual box backed vagrant host, and all subsequent agents
    are lxc backed vagrant guests.
    Accepts the working directory and the cosmo version.
    """
    def __init__(self, args):
        self.working_dir = args.working_dir
        self.cosmo_version = args.cosmo_version
        self.jar_name = "orchestrator-" + self.cosmo_version + "-all"

        # first thing, update api
        self.update_apt_registry()

        # install pip for subsequent calls.
        self.install_python_dev()
        self.install_python_pip()

        # install decorators for running with timeouts and retries
        self.install_timeout()
        self.install_retrying()

        # we can now import the installer, after installing the needed decorators.
        from package_installer import PackageInstaller
        self.installer = PackageInstaller()

    def install_python_dev(self):
        return_code = subprocess.call(["sudo", "apt-get", "-y", "install", "python-dev"])
        if return_code != 0:
            raise subprocess.CalledProcessError(cmd="apt-get install python-dev", returncode=1, output=sys.stderr)

    def install_python_pip(self):
        return_code = subprocess.call(["sudo", "apt-get", "-y", "install", "python-pip"])
        if return_code != 0:
            raise subprocess.CalledProcessError(cmd="apt-get install python-pip", returncode=1, output=sys.stderr)

    def install_retrying(self):
        return_code = subprocess.call(["sudo", "pip", "install", "retrying"])
        if return_code != 0:
            raise subprocess.CalledProcessError(cmd="pip install retrying", returncode=1, output=sys.stderr)

    def install_timeout(self):
        return_code = subprocess.call(["sudo", "pip", "install", "timeout-decorator"])
        if return_code != 0:
            raise subprocess.CalledProcessError(cmd="pip install timeout-decorator", returncode=1, output=sys.stderr)

    def update_apt_registry(self):
        return_code = subprocess.call(["sudo", "apt-get", "-y", "update"])
        if return_code != 0:
            raise subprocess.CalledProcessError(cmd="apt-get update", returncode=1, output=sys.stderr)

    def sudo(self, command):
            return "sudo {0}".format(command)

    def install_rabbitmq(self):
        self.installer.run_fabric(self.sudo(
            "sed -i '2i deb http://www.rabbitmq.com/debian/ testing main' /etc/apt/sources.list"
        ))

        self.installer.wget("http://www.rabbitmq.com/rabbitmq-signing-key-public.asc", self.working_dir)

        self.installer.apt_key("{0}/rabbitmq-signing-key-public.asc".format(self.working_dir))

        self.installer.apt_get_update()
        self.installer.apt_get_install("erlang-nox")
        self.installer.apt_get_install("-f")
        self.installer.apt_get_install("rabbitmq-server")
        self.installer.run_fabric(self.sudo("rabbitmq-plugins enable rabbitmq_management"))
        self.installer.run_fabric(self.sudo("rabbitmq-plugins enable rabbitmq_tracing"))
        self.installer.run_fabric(self.sudo("service rabbitmq-server restart"))
        self.installer.run_fabric(self.sudo("rabbitmqctl trace_on"))

    def install_lxc_docker(self):
        self.installer.apt_get_install("python-software-properties")
        self.installer.apt_get_update()
        self.installer.add_apt("ppa:dotcloud/lxc-docker")
        self.installer.apt_get_update()
        self.installer.apt_get_install("lxc-docker")

    def install_kernel(self):
        self.installer.add_apt("ppa:ubuntu-x-swat/r-lts-backport")
        self.installer.apt_get_update()
        self.installer.apt_get_install("linux-image-3.8.0-19-generic")

    def install_riemann(self):
        self.installer.wget("http://aphyr.com/riemann/riemann_0.2.2_all.deb", self.working_dir)
        self.installer.run_fabric(self.sudo("dpkg -i {0}/riemann_0.2.2_all.deb".format(self.working_dir)))

    def install_java(self):
        self.installer.apt_get_install("openjdk-7-jdk")

    def install_celery(self):
        self.installer.pip("billiard==2.7.3.28")
        self.installer.pip("celery==3.0.19")
        self.installer.pip("python-vagrant")
        self.installer.pip("bernhard")

    def install_vagrant(self):
        self.installer.wget(
            "http://files.vagrantup.com/packages/22b76517d6ccd4ef232a4b4ecbaa276aff8037b8/vagrant_1.2.6_x86_64.deb"
            , self.working_dir)
        self.installer.run_fabric(self.sudo("dpkg -i {0}/vagrant_1.2.6_x86_64.deb".format(self.working_dir)))
        self.install_vagrant_lxc()
        self.add_lxc_box("precise64", "http://dl.dropbox.com/u/13510779/lxc-precise-amd64-2013-07-12.box")

    def install_vagrant_lxc(self):
        self.installer.run_fabric("vagrant plugin install vagrant-lxc")

    def install_guest_additions(self):

        """
        Currently not used. provides some more functionality between the actual host and the virtual box vagrant guest.
        See http://www.virtualbox.org/manual/ch04.html
        """
        self.installer.apt_get_install("linux-headers-3.8.0-19-generic dkms")
        self.installer.run_fabric("echo 'Downloading VBox Guest Additions...'")
        self.installer.wget("-q http://dlc.sun.com.edgesuite.net/virtualbox/4.2.12/VBoxGuestAdditions_4.2.12.iso",
                            self.working_dir)

        guest_additions_script = """mount -o loop,ro /home/vagrant/VBoxGuestAdditions_4.2.12.iso /mnt
echo yes | /mnt/VBoxLinuxAdditions.run
umount /mnt
rm /root/guest_additions.sh
"""

        self.installer.run_fabric("echo -e '" + guest_additions_script + "' > /root/guest_additions.sh")
        self.installer.run_fabric("chmod 700 /root/guest_additions.sh")
        self.installer.run_fabric(
            "sed -i -E 's#^exit 0#[ -x /root/guest_additions.sh ] \\&\\& /root/guest_additions.sh#' /etc/rc.local"
        )
        self.installer.run_fabric("echo 'Installation of VBox Guest Additions is proceeding in the background.'")
        self.installer.run_fabric(
            "echo '\"vagrant reload\" can be used in about 2 minutes to activate the new guest additions.'"
        )

    def install_cosmo(self):

        run_script = """#!/bin/sh
ARGS=\"$@\"
export VAGRANT_DEFAULT_PROVIDER=lxc
java {0} -jar {1}/cosmo.jar $ARGS
""".format(JAVA_OPTS, self.working_dir)

        get_cosmo = "https://s3.amazonaws.com/cosmo-snapshot-maven-repository/travisci/home/travis/" \
                    ".m2/repository/org/cloudifysource/cosmo/orchestrator/" + self.cosmo_version + "/" + self\
            .jar_name + ".jar"

        self.installer.wget(get_cosmo, self.working_dir)

        self.installer.run_fabric("mv {0}/{1}.jar {0}/cosmo.jar".format(self.working_dir, self.jar_name))

        script_path = self.working_dir + "/cosmo.sh"
        cosmo_exec = open(script_path, "w")
        cosmo_exec.write(run_script)

        self.installer.run_fabric("chmod +x " + script_path)

        self.installer.run_fabric("echo \"alias cosmo='{0}/cosmo.sh'\" > {1}/.bash_aliases".format(self.working_dir, USER_HOME))

    def add_lxc_box(self, name, url):
        self.installer.run_with_retry_and_timeout(
            "vagrant box add {0} {1}".format(name, url)
        )

    def install_lxc(self):
        file_dir = os.path.abspath(os.path.join(__file__, os.pardir))
        self.installer.run_fabric(self.sudo("chmod +x {0}/travis_lxc_workaround.sh".format(file_dir)))
        self.installer.run_with_retry_and_timeout(self.sudo("{0}/travis_lxc_workaround.sh".format(file_dir)))

    def reboot(self):
        self.installer.run_fabric("shutdown -r +1")

    def bootstrap(self):
        # self.install_lxc()
        self.install_lxc_docker()
        self.install_kernel()
        self.install_rabbitmq()
        self.install_riemann()
        self.install_celery()
        self.install_vagrant()
        self.install_java()
        self.install_cosmo()
        print "Manager boot completed"

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Boots and installs all necessary cosmo management components'
    )
    parser.add_argument(
        '--working_dir',
        help='Working directory for all cosmo installation files',
        default="/home/vagrant/cosmo-work"
    )
    parser.add_argument(
        '--cosmo_version',
        help='Version of cosmo that will be used to deploy the dsl',
        default='0.1-SNAPSHOT'
    )

    vagrant_boot = VagrantLxcBoot(parser.parse_args())
    vagrant_boot.bootstrap()