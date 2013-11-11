# Copyright 2013 Johan Rydberg.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

from ..build import ImageBuilder
from ..command import Command
from ..manifest import ProjectManifest
from ..scheduler import Scheduler
from .. import util


class _ServicesBuilder(object):
    """Builds a set of services for a release from a project
    definition.
    """

    def __init__(self, config, service_manager):
        self.config = config
        self.service_manager = service_manager

    def build(self, defn, push_image=True):
        """Build services from a project definition (contents of the
        `gilliam.yml` file).

        :param defn: The project definition.
        :type defn: dict.

        :returns: The services.
        :rtype: dict.
        """
        services = {}

        if 'auxiliary' in defn:
            self._build_auxiliary(defn['auxiliary'], services)

        if 'processes' in defn:
            self._build_processes(
                self.config.project_dir, defn['processes'], services,
                push_image
                )

        return services

    def _build_processes(self, dir, processes, services, push_image):
        """Build services for processes.  Store the result in `services`.

        :param processes: The processes defined by the project.
        :type processes: dict(str:dict).

        :param services: The services where the services should be stored.
        :type services: dict.
        """
        image = ImageBuilder(self.config).build(dir, push_image=push_image)
        for name, defn in processes.items():
            services[name] = {
                'image': image, 'command': defn['script'],
                'ports': defn.get('ports', []),
                'env': defn.get('env', {})}

    def _build_auxiliary(self, aux, services):
        """Build services from axualiary services in the project
        definition.

        :param aux: Auxiliary services.
        :type aux: dict(str:dict).

        :param services: The services where the services should be stored.
        :type services: dict(str:dict).
        """
        for name, defn in aux.items():
            service_type = defn.get('type')
            if service_type:
                try:
                    service_ext = self.service_manager[service_type]
                except KeyError:
                    sys.exit("{0}: {1}: no such service".format(
                        name, service_type))
            else:
                for ext in iter(self.service_manager):
                    if ext.obj.detect(name, defn):
                        service_ext = ext
                        break
                else:
                    sys.exit("{0}: cannot detect service".format(name))
            service_obj = service_ext.obj
            services[name] = service_obj.build(name, defn)


class Deploy(Command):
    """Build a new release and migrate to it."""

    requires = {'formation': True, 'project_dir': True}

    def get_parser(self, prog_name):
        parser = Command.get_parser(self, prog_name)
        parser.add_argument(
            '--author',
            default=None
            )
        parser.add_argument(
            '-m', '--message',
            help="description of the release"
            )
        parser.add_argument(
            '--rate',
            help="migration rate"
            )
        parser.add_argument(
            '--no-push',
            dest='push_image',
            default=True,
            action='store_false',
            help="do not push built image to registry"
            )
        return parser

    def take_action(self, options):
        rate = util.parse_rate(options.rate)
        defn = ProjectManifest.load(self.app.config.project_dir)

        formation = Scheduler(self.app.config.scheduler()).formation(
            self.app.config.formation)

        services = _ServicesBuilder(
            self.app.config, self.app.service_manager).build(
                defn, push_image=options.push_image)
        name = formation.release(
            options.author,
            options.message,
            services,
            merge_env=True
            )
        self.app.stdout.write('release {0}\n'.format(name))
        formation.migrate(name, rate)
