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

import os
import yaml
import sys

from ..command import Command, ListerCommand
from ..scheduler import Scheduler


class Releases(ListerCommand):
    """show releases in formation"""

    requires = {'formation': True}

    FIELDS = ('name', 'author', 'message')

    requires = {'formation': True}

    def take_action(self, options):
        """Handle the command."""
        def it(scheduler):
            for instance in scheduler.releases(self.app.config.formation):
                yield [instance.get(f) for f in self.FIELDS]

        return self.FIELDS, it(self.app.config.scheduler())


class DumpRelease(Command):
    """dump a release"""

    requires = {'formation': True}

    def get_parser(self, prog_name):
        parser = Command.get_parser(self, prog_name)
        parser.add_argument(
            '-r', '--release',
            help="release name"
            )
        return parser

    def take_action(self, options):
        formation = Scheduler(self.app.config.scheduler()).formation(
            self.app.config.formation)
        release = (formation.find_release(options.release) if options.release
                   else formation.last_release)
        yaml.safe_dump(release, self.app.stdout, default_flow_style=False)
