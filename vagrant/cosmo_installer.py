import argparse
import os
from os.path import expanduser
from fabric.operations import local
from prerequisites_installer import PrerequisitesInstaller


__author__ = 'elip'

USER_HOME = expanduser('~')


class CosmoInstaller:

    """
    This class installs the cosmo jar into the machine,
    Accepts the working directory and the jar version.
    """

    def __init__(self, working_dir, cosmo_version):
        self.working_dir = working_dir
        self.cosmo_version = cosmo_version
        self.jar_name = "orchestrator-" + self.cosmo_version + "-all"

        PrerequisitesInstaller().install()

        from package_installer import PackageInstaller
        self.installer = PackageInstaller()

    def install_cosmo_from_s3(self):

        """
        Use this method when you want to install the official cosmo jar from
        the public maven repository.
        """

        get_cosmo = "https://s3.amazonaws.com/cosmo-snapshot-maven-repository/travisci/home/travis/" \
                    ".m2/repository/org/cloudifysource/cosmo/orchestrator/" + self.cosmo_version + "/" + self \
                    .jar_name + ".jar"

        self.installer.wget(get_cosmo, self.working_dir)

        self.installer.run_fabric("mv {0}/{1}.jar {0}/cosmo.jar".format(self.working_dir, self.jar_name))
        self.installer.run_fabric("cp {0} {1}".format("/vagrant/log4j.properties", self.working_dir)) 

        self.install_cosmo_common()

    def install_cosmo_common(self):
        run_script = """#!/bin/sh
if [ $# -gt 0 ] && [ "$1" = "undeploy" ]
then
        echo "Undeploying..."
        curdir=`pwd`
        for dir in /tmp/vagrant-vms/*/
        do
                if [ -d "$dir" ]; then
                        cd $dir
                        vagrant destroy -f > /dev/null 2>&1
                fi
        done
        cd $curdir
        rm -rf /tmp/vagrant-vms/*
        echo "done!"
else
        ARGS="$@"
        export VAGRANT_DEFAULT_PROVIDER=lxc
        java -Xms512m -Xmx1024m -XX:PermSize=128m -Dlog4j.configuration=file://{0}/log4j.properties -jar {0}/cosmo.jar $ARGS
fi 
""".format(self.working_dir)

        script_path = self.working_dir + "/cosmo.sh"
        cosmo_exec = open(script_path, "w")
        cosmo_exec.write(run_script)

        self.installer.run_fabric("chmod +x " + script_path)

        self.installer.run_fabric("echo \"alias cosmo='{0}/cosmo.sh'\" > {1}/.bash_aliases".format(self.working_dir,
                                                                                                   USER_HOME))

    def install_cosmo_from_local(self):

        """
        Use this method when you want to run cosmo on your local machine.
        It will compile the jar and copy it to the right place.
        """

        vagrant_dir = os.path.abspath(os.path.join(__file__, os.pardir))
        manager_dir = os.path.abspath(os.path.join(vagrant_dir, os.pardir))

        local("cd {0}/orchestrator && mvn clean package -Pall".format(manager_dir))

        # copy to working directory
        local("cp -r {0}/orchestrator/target/cosmo.jar {1}".format(
            manager_dir, self.working_dir))
        
        local("cp -r {0}/vagrant/log4j.properties {1}".format(
            manager_dir, self.working_dir))

        self.install_cosmo_common()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Installs the cosmo jar into the host'
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
    parser.add_argument(
        '--local',
        help='True if you are planning to run cosmo on your local machine',
        default=False
    )

    args = parser.parse_args()
    installer = CosmoInstaller(args.working_dir, args.cosmo_version)

    if args.local:
        installer.install_cosmo_from_local()
    else:
        installer.install_cosmo_from_s3()




