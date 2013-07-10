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

"""
A celery tasks for installing and starting diamond monitoring (+ includes 1 monitor)
"""

import urllib2
import os
from os import path
from cosmo.celery import celery

@celery.task
def install(diamond_config, __cloudify_id, **kwargs):

    # install dependencies
    install_dependencies()

    config_paths = ConfigPaths(diamond_config)

    make_directories(config_paths)

    create_main_config(config_paths, diamond_config, cloudify_id)

    # TODO extract to different task in some new interface
    collector_properties = diamond_config['collector_properties']
    install_collector(collector_properties, config_paths)

    workaround_temp_diamond_bug(diamond_config)


@celery.task
def start(diamond_config, __cloudify_id, **kwargs):
    config_paths = ConfigPaths(diamond_config)
    command = 'nohup diamond -c {0}'.format(config_paths.main_config_path)
    os.system(command)


class ConfigPaths(object):

    def __init__(self, diamond_config):
        self.root_dir = path.join(diamond_config['workdir'], 'diamond')
        self.collectors_dir = path.join(self.root_dir, 'collectors')
        self.collectors_config_dir = path.join(self.root_dir, 'collectors_config')
        self.logs_dir = path.join(self.root_dir, 'logs')
        self.main_config_path = path.join(self.root_dir, 'diamond.conf')
        self.diamond_pid_path = path.join(self.root_dir, 'diamond.pid')
        self.diamond_log_path = path.join(self.logs_dir, 'diamond.log')

def install_dependencies():
    os.system("sudo pip install diamond")
    # for riemann handler
    os.system("sudo pip install bernhard")


def make_directories(config_paths):
    os.makedirs(config_paths.root_dir)
    os.mkdir(config_paths.collectors_dir)
    os.mkdir(config_paths.collectors_config_dir)
    os.mkdir(config_paths.logs_dir)


def create_main_config(config_paths, diamond_config, cloudify_id):
    # load template diamond configuration (only possible after 'pip install diamond')
    from configobj import ConfigObj
    config_template = ConfigObj('/etc/diamond/diamond.conf.example')

    # locate where the handlers code is
    import diamond.handler
    diamond_handlers = path.dirname(diamond.handler.__file__)

    # modify template configuration for our needs
    config_template['server']['handlers'] = 'diamond.handler.riemann.RiemannHandler'
    config_template['server']['user'] = diamond_config['user']
    config_template['server']['group'] = diamond_config['group']
    config_template['server']['pid_file'] = config_paths.diamond_pid_path
    config_template['server']['collectors_path'] = config_paths.collectors_dir
    config_template['server']['collectors_config_path'] = config_paths.collectors_config_dir
    config_template['server']['collectors_reload_interval'] = diamond_config['collectors_reload_interval']
    config_template['server']['handlers_path'] = diamond_handlers
    config_template['logger_root']['level'] = 'DEBUG'
    config_template['handler_rotated_file']['level'] = 'DEBUG'
    config_template['handler_rotated_file']['args'] = ["('{0}'".format(config_paths.diamond_log_path),
                                                       'midnight', '1', '7)']
    riemann_handler = 'RiemannHandler'
    config_template['handlers'][riemann_handler] = {}
    config_template['handlers'][riemann_handler]['host'] = diamond_config['riemann_host']
    config_template['handlers'][riemann_handler]['port'] = diamond_config['riemann_port']
    config_template['handlers'][riemann_handler]['transport'] = diamond_config['riemann_transport']
    with open(config_paths.main_config_path, 'w') as f:
        config_template.write(f)


def install_collector(properties, config_paths):

    short_name = properties['meta']['short_name']
    name = properties['meta']['name']
    url = properties['meta']['url']

    # download plugin (single file) to collectors directory
    response = urllib2.urlopen(url)
    collector_dir = path.join(config_paths.collectors_dir, short_name)
    os.mkdir(collector_dir)
    collector_path = path.join(collector_dir, '{0}.py'.format(short_name))
    with open(collector_path, 'w') as f:
        f.write(response.read())

    # create and write collector config
    collector_config = ConfigObj()
    collector_config['enabled'] = 'True'
    if properties.has_key['config']:
        for key, value in properties['config'].items():
            collector_config[key] = value

    collector_config_path = path.join(config_paths.collectors_config_dir,
                                      '{0}.conf'.format(name))
    with open(collector_config_path, 'w') as f:
        collector_config.write(f)


def workaround_temp_diamond_bug(diamond_config):
    from diamond import server
    server_py_path = path.join(path.dirname(server.__file__), 'server.py')
    temp_path = '{0}/temp.py'.format(diamond_config['workdir'])
    os.system("sudo sed s/handername/handlername/ {0} > {1}".format(server_py_path, temp_path))
    os.system("sudo cp {0} {1}".format(temp_path, server_py_path))
