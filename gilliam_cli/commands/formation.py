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

from urllib import urlopen
import yaml

from ..config import FormationConfig
from ..command import Command


# Name of the initial release.
_INITIAL_RELEASE_NAME = '1'


class Launch(Command):
    """Launch a new formation from an existing release manifest."""

    def get_parser(self, prog_name):
        parser = Command.get_parser(self, prog_name)
        parser.add_argument(
            'formation',
            help="name of the formation to create"
            )
        parser.add_argument(
            'release',
            help="release manifest"
            )
        return parser

    def take_action(self, options):
        release = self._read_release(options.release)
        scheduler = self.app.config.scheduler()
        formation = scheduler.create_formation(options.formation)
        scheduler.create_release(
                options.formation, _INITIAL_RELEASE_NAME,
                release.get('author', 'unknown'),
                release.get('message', ''),
                release.get('services', {}))

    def _read_release(self, fn):
        """Read release manifest and return it as a python C{dict}."""
        if fn.startswith("http://") or fn.startswith("https://"):
            with urlopen(fn) as fp:
                return yaml.load(fp)
        elif fn == '-':
            return yaml.load(self.app.stdin)
        else:
            with open(fn) as fp:
                return yaml.load(fp)


class Create(Command):
    """Create a new formation."""

    requires = {'project_dir': True}

    def get_parser(self, prog_name):
        parser = Command.get_parser(self, prog_name)
        parser.add_argument(
            'formation',
            help="name of the formation to create"
            )
        return parser

    def take_action(self, options):
        scheduler = self.app.config.scheduler()
        formation = scheduler.create_formation(options.formation)

        form_config = FormationConfig.make(self.app.config.project_dir)
        form_config.formation = formation['name']

        if self.app.options.stage:
            form_config.stage = self.app.options.stage
