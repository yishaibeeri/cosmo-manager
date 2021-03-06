########
# Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

__author__ = "idanmo"

from setuptools import setup


PLUGIN_INSTALLER_VERSION = '0.3'
PLUGIN_INSTALLER_BRANCH = 'develop'
PLUGIN_INSTALLER = "https://github.com/CloudifySource/" \
                   "cosmo-plugin-plugin-installer/tarball/{" \
                   "0}#egg=cosmo-plugin-plugin-installer-{1}" \
    .format(PLUGIN_INSTALLER_BRANCH, PLUGIN_INSTALLER_VERSION)


COSMO_MANAGER_REST_CLIENT_VERSION = '0.3'
COSMO_MANAGER_REST_CLIENT_BRANCH = 'develop'
COSMO_MANAGER_REST_CLIENT = "https://github.com/CloudifySource/" \
                            "cosmo-manager-rest-client/tarball/{" \
                            "0}#egg=cosmo-manager-rest-client-{1}" \
    .format(COSMO_MANAGER_REST_CLIENT_BRANCH,
            COSMO_MANAGER_REST_CLIENT_VERSION)

COSMO_CELERY_VERSION = '0.3'
COSMO_CELERY_BRANCH = 'develop'
COSMO_CELERY = "https://github.com/CloudifySource/" \
               "cosmo-celery-common/tarball/{" \
               "0}#egg=cosmo-celery-common-{1}" \
    .format(COSMO_CELERY_BRANCH,
            COSMO_CELERY_VERSION)

setup(
    name='cloudify-workflows',
    version='0.3',
    author='Idan Moyal',
    author_email='idan@gigaspaces.com',
    packages=['plugins'],
    license='LICENSE',
    description='Cloudify workflow python tests',
    zip_safe=False,
    install_requires=[
        "cosmo-celery-common",
        "pika==0.9.13",
        "cosmo-plugin-plugin-installer",
        "cosmo-manager-rest-client",
        "bernhard==0.1.0"
    ],
    test_requires=[
        "nose"
    ],
    dependency_links=[COSMO_CELERY,
                      PLUGIN_INSTALLER,
                      COSMO_MANAGER_REST_CLIENT]
)
