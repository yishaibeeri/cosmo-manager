# coding=utf-8

"""
Publishes state of current registered tasks

#### Dependencies

 * celery

"""

import diamond.collector
from celery import Celery

class CeleryRegisteredTasksCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(CeleryRegisteredTasksCollector, self).get_default_config_help()
        config_help.update({
            'broker_url' : 'the broker url'
        })
        return config_help

    def get_default_config(self):
        config = super(CeleryRegisteredTasksCollector, self).get_default_config()
        config.update({
            'enabled': 'True',
            'broker_url': 'amqp://'
        })
        return config

    def __init__(self, config, handlers):
        super(CeleryRegisteredTasksCollector, self).__init__(config, handlers)
        self.broker_url = self.config['broker_url']

    def collect(self):
        with Celery(broker=self.broker_url, backend=self.broker_url) as c:
            tasks = c.control.inspect.registered(c.control.inspect())

        plugins = self._extract_registered_plugins(tasks)
        for plugin in plugins:
            self.publish_gauge(plugin, 1)

    def _extract_registered_plugins(self, tasks):
        if not tasks:
            return []
            
        plugins = set()
        for node, node_tasks in tasks.items():
            for task in node_tasks:
                plugin_name_split = task.split('.')[:-1]
                if not plugin_name_split[0] == 'cosmo':
                    continue
                if not plugin_name_split[-1] == 'tasks':
                    continue
                plugin_name = '.'.join(plugin_name_split[1:-1])
                full_plugin_name = '{0}@{1}'.format(node, plugin_name)
                plugins.add(full_plugin_name)
        return list(plugins)
