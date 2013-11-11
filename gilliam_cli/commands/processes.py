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

from ..command import ListerCommand, Command
from ..scheduler import Scheduler
from ..util import parse_rate, parse_scale
from ..port_spec import merge_port_specs


class ProcessStatus(ListerCommand):
    """Display running instances."""

    requires = {'formation': True}

    FIELDS = ('name', 'release', 'state', 'status', 'reason', 'assigned_to', 'image', 'command')

    def take_action(self, options):
        def it(scheduler):
            for instance in scheduler.instances(self.app.config.formation):
                yield [instance.get(f) for f in self.FIELDS]

        return self.FIELDS, it(self.app.config.scheduler())


class Scale(Command):
    """Scale processes of services."""

    requires = {'formation': True}

    def get_parser(self, prog_name):
        parser = Command.get_parser(self, prog_name)
        parser.add_argument(
            '-r', '--release',
            help="Release to scale"
            )
        parser.add_argument(
            "scale",
            nargs='+'
            )
        parser.add_argument(
            '--rate',
            dest='rate',
            help="rate to create or destroy instances"
            )
        return parser

    def take_action(self, options):
        scales = dict(parse_scale(scale) for scale in options.scale)
        rate = parse_rate(options.rate)
        formation = Scheduler(self.app.config.scheduler()).formation(
            self.app.config.formation)

        if not options.release:
            last_release = formation.last_release
            options.release = (last_release['name']
                               if last_release else None)

        if not options.release:
            sys.exit("can't find a release to scale")

        formation.scale(options.release, scales, rate)


class Spawn(Command):
    """Launch a new process instance."""

    requires = {'formation': True}

    def get_parser(self, prog_name):
        parser = Command.get_parser(self, prog_name)
        parser.add_argument(
            'service',
            help='service template'
            )
        parser.add_argument(
            '-r', '--release',
            metavar="NAME",
            help="release"
            )
        parser.add_argument(
            '--assigned-to',
            metavar="NAME",
            dest="assigned_to",
            help="assign instance to executor"
            )
        parser.add_argument(
            '-p', '--port',
            action='append',
            dest="ports",
            default=[],
            help="port mapping"
            )
        parser.add_argument(
            '--require',
            action='append',
            default=[],
            dest="requirements"
            )
        parser.add_argument(
            '--rank',
            default=None
            )

        return parser

    def _find_service(self, release, name):
        service = release['services'].get(name)
        if service is None:
            sys.exit("%s: no such service" % (name,))
        return (service['image'], service['command'],
                service.get('env', {}),
                service.get('ports', []))

    def take_action(self, options):
        scheduler = self.app.config.scheduler()
        formation = Scheduler(scheduler).formation(
            self.app.config.formation)
        release = (formation.find_release(options.release)
                   if options.release else formation.last_release)

        if release is None:
            sys.exit("no release in formation")

        image, command, env, ports = self._find_service(
            release, options.service)
        ports = merge_port_specs(ports, options.ports)

        inst = scheduler.spawn(
            self.app.config.formation,
            options.service,
            release['name'],
            image, command, env, ports,
            options.assigned_to,
            options.requirements, options.rank
            )
        self.app.stdout.write('{0}\n'.format(inst['name']))
