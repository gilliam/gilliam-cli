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

import logging
import yaml
import sys

from ..build import ImageBuilder
from ..command import Command
from ..manifest import ProjectManifest
from ..scheduler import Scheduler
from .. import util


class _CommonEnvCommand(Command):
    """Base class for the `set` and `unset` commands."""

    log = logging.getLogger(__name__)

    requires = {'formation': True}

    def get_parser(self, prog_name):
        parser = Command.get_parser(self, prog_name)
        parser.add_argument(
            'var',
            nargs='+',
            help="environment variable"
            )
        parser.add_argument(
            '-r', '--release',
            default=None,
            help="base release other than latest"
            )
        parser.add_argument(
            '--author',
            default=None,
            help="author of the release"
            )
        parser.add_argument(
            '-m', '--message',
            help="description of the release"
            )
        parser.add_argument(
            '--rate'
            )
        parser.add_argument(
            '-a', '--apply',
            help="apply changes by migrating to new release"
            )
        return parser

    def _split_var(self, var):
        """Try to split a variable definition (`var=value`) into variable
        name and value.

        :returns: The name and value.
        :rtype: tuple(str, str).

        :raises: `ValueError` if the given value does not adhere to
            the format.
        """
        try:
            name, value = var.split('=', 1)
        except ValueError:
            raise ValueError("{0}: invalid env var def format".format(var))
        return name, value

    def _split_scope(self, name):
        """Try to split given string into *scope* and variable name.
        The format is `[[SCOPE]:]NAME`.

        :returns: scope and variable name.  Scope may be `None` if not
            specified.
        """
        try:
            scope, name = name.split(':', 1)
        except ValueError:
            return None, name
        else:
            return scope, name

    def take_action(self, options):
        """Perform command.

        .. note:

           If the specified release cannot be found or if there's no
           releases at all in the formation, this command will barf.
        """
        rate = util.parse_rate(options.rate)
        formation = Scheduler(self.app.config.scheduler()).formation(
            self.app.config.formation)
        release = (formation.find_release(options.release) if options.release
                   else formation.last_release)
        if not release:
            sys.exit("no release")

        self.update_env(formation, release, options.var)

        name = formation.release(
            options.author or release.get('author'),
            options.message or release.get('message'),
            release['services'],
            merge_env=False)
        self.app.stdout.write("release {0}\n".format(name))

        if options.apply:
            self.log.debug("start migrating to {0}".format(name))
            formation.migrate(name, rate)

    def update_env(self, formation, release, vars):
        """Update environment according to semantics of command.

        This should be implemented by subclass.
        """
        raise NotImplementedError("update_env")


class Set(_CommonEnvCommand):
    """set environment variable in new release"""

    def update_env(self, formation, release, vars):
        for var in vars:
            name, value = self._split_var(var)
            scope, name = self._split_scope(name)
            if not scope:
                self._set_globally(release, name, value)
            else:
                self._set_specific(release, scope, name, value)

    def _set_globally(self, release, var, value):
        for service in release['services'].itervalues():
            service.get('env', {}).update({var: value})

    def _set_specific(self, release, name, var, value):
        service = release['services'].get(name, {})
        service.get('env', {}).update({var: value})


class Unset(_CommonEnvCommand):
    """unset environment variable in new release"""

    def update_env(self, formation, release, vars):
        for var in vars:
            scope, name = self._split_scope(var)
            if not scope:
                self._unset_globally(release, name)
            else:
                self._unset_specific(release, scope, name)

    def _unset_globally(self, release, var):
        for service in release['services'].itervalues():
            service.get('env', {}).pop(var, None)

    def _unset_specific(self, release, name, var):
        service = release['services'].get(name, {})
        service.get('env', {}).pop(var, None)


class Show(Command):
    """show environment for release"""

    requires = {'formation': True}

    def get_parser(self, prog_name):
        parser = Command.get_parser(self, prog_name)
        parser.add_argument(
            "service",
            nargs='?',
            help="specific service to show variables for"
            )
        parser.add_argument(
            '-r', '--release',
            default=None,
            help="release other than latest"
            )
        return parser

    def take_action(self, options):
        formation = Scheduler(self.app.config.scheduler()).formation(
            self.app.config.formation)
        release = (formation.find_release(options.release) if options.release
                   else formation.last_release)
        if not release:
            sys.exit("no release")

        if options.service:
            output = release['services'].get(options.service, {}).get('env', {})
        else:
            output = {}
            for name, defn in release['services'].items():
                output[name] = defn.get('env', {})
            output = {name: env for (name, env) in output.items() if env}
        if output:
            yaml.safe_dump(output, self.app.stdout, default_flow_style=False)
