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
A celery tasks for installing and starting diamond monitoring
"""

import os
from os import path
from cosmo.celery import celery, get_cosmo_properties
from configobj import ConfigObj


@celery.task
def install(diamond_config, **kwargs):
    config_paths = ConfigPaths(diamond_config)
    make_directories(config_paths)
    create_main_config(config_paths, diamond_config)
    # install_collectors(config_paths, diamond_config)


@celery.task
def start(diamond_config, **kwargs):
    config_paths = ConfigPaths(diamond_config)
    command = 'nohup diamond -c {0}'.format(config_paths.main_config_path)
    os.system(command)


@celery.task
def stop(diamond_config, **kwargs):
    config_paths = ConfigPaths(diamond_config)
    if not path.exists(config_paths.diamond_pid_path):
        return
    with open(config_paths.diamond_pid_path, 'r') as f:
        os.system("kill {0}".format(f.read()))


@celery.task
def restart(diamond_config, **kwargs):
    stop(diamond_config)
    config_paths = ConfigPaths(diamond_config)
    create_main_config(config_paths, diamond_config)
    # install_collectors(config_paths, diamond_config)
    start(diamond_config)


class ConfigPaths(object):

    def __init__(self, diamond_config):
        self.root_dir = path.join(diamond_config['workdir'], 'diamond')
        self.collectors_dir = path.join(self.root_dir, 'collectors')
        self.collectors_config_dir = path.join(self.root_dir, 'collectors_config')
        self.logs_dir = path.join(self.root_dir, 'logs')
        self.main_config_path = path.join(self.root_dir, 'diamond.conf')
        self.diamond_pid_path = path.join(self.root_dir, 'diamond.pid')
        self.diamond_log_path = path.join(self.logs_dir, 'diamond.log')


def make_directories(config_paths):
    os.makedirs(config_paths.root_dir)
    os.mkdir(config_paths.collectors_dir)
    os.mkdir(config_paths.collectors_config_dir)
    os.mkdir(config_paths.logs_dir)


def create_main_config(config_paths, diamond_config):
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
    config_template['handler_rotated_file']['args'] = ["('{0}'".format(config_paths.diamond_log_path), "'midnight'", '1', '7)']
    riemann_handler = 'RiemannHandler'
    config_template['handlers'][riemann_handler] = {}
    config_template['handlers'][riemann_handler]['host'] = get_cosmo_properties()['management_ip']
    with open(config_paths.main_config_path, 'w') as f:
        config_template.write(f)


# def install_collectors(config_paths, diamond_config):
#     if 'collectors' in diamond_config.keys():
#         for short_name, collector_properties in diamond_config['collectors'].items():
#             install_collector(short_name, collector_properties, config_paths)
#
#
# def install_collector(short_name, properties, config_paths):
#
#     name = properties['meta']['name']
#     url = properties['meta']['url']
#
#     # download plugin (single file) to collectors directory
#     response = urllib2.urlopen(url)
#     collector_dir = path.join(config_paths.collectors_dir, short_name)
#     os.mkdir(collector_dir)
#     collector_path = path.join(collector_dir, '{0}.py'.format(short_name))
#     with open(collector_path, 'w') as f:
#         f.write(response.read())
#
#     # create and write collector config
#     collector_config = ConfigObj()
#     collector_config['enabled'] = 'True'
#     if 'config' in properties.keys():
#         for key, value in properties['config'].items():
#             collector_config[key] = value
#
#     collector_config_path = path.join(config_paths.collectors_config_dir,
#                                       '{0}.conf'.format(name))
#     with open(collector_config_path, 'w') as f:
#         collector_config.write(f)
