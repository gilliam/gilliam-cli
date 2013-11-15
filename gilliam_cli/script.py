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
import os
import sys

from cliff.app import App
from cliff.commandmanager import CommandManager
from stevedore.extension import ExtensionManager

from .config import Config, StageConfig, FormationConfig, AuthConfig
from . import util


class GilliamApp(App):
    """Gilliam command-line client."""

    log = logging.getLogger(__name__)

    def __init__(self, command_manager, service_manager):
        super(GilliamApp, self).__init__(
            description='gilliam X', version='0.1',
            command_manager=command_manager)
        self.service_manager = service_manager

    def initialize_app(self, argv):
        """Initialize app before command is run."""

        # we do not require anything for the help command to run.
        if argv and argv[0] == 'help':
            return

        project_dir = self.options.project_dir or util.find_rootdir()

        form_config = (
            FormationConfig.make(project_dir) if project_dir else
            None)

        env_stage = os.getenv('GILLIAM_STAGE')
        self.options.stage = (
            self.options.stage if self.options.stage else
            form_config.stage if form_config else
            env_stage if env_stage else
            None)
        self.options.formation = (
            self.options.formation if self.options.formation else
            form_config.formation if form_config else
            None)

        try:
            stage_config = (
                StageConfig.make(self.options.stage) if self.options.stage else
                StageConfig.default())
        except EnvironmentError as err:
            stage_config = None

        auth_path = os.path.expanduser('~/.gilliam/auth')
        auth_config = AuthConfig.make(auth_path)

        self.config = Config(
            project_dir, stage_config, form_config, auth_config,
            self.options.stage, self.options.formation)

    def configure_logging(self):
        super(GilliamApp, self).configure_logging()
        # need to quiet some chatty parts of our deps.
        requests_logger = logging.getLogger(
            'requests.packages.urllib3.connectionpool')
        requests_logger.setLevel(logging.WARNING)

    def build_option_parser(self, description, version,
                            argparse_kwargs=None):
        """Return an argparse option parser for this application."""
        parser = super(GilliamApp, self).build_option_parser(
            description, version, argparse_kwargs=argparse_kwargs)

        parser.add_argument(
            '--stage',
            metavar='NAME',
            dest='stage',
            help="Stage ...")

        parser.add_argument(
            '-F', '--formation',
            metavar='NAME',
            dest='formation',
            help='Formation the subcommand applies to')

        parser.add_argument(
            '--project-dir',
            metavar="PATH",
            dest="project_dir",
            help="root directory of your project")

        return parser

    def prepare_to_run_command(self, cmd):
        """Perform any preliminary work needed to run a command.

        :see: :method:`cliff.app.App.prepare_to_run`.
        """
        requires = getattr(cmd, 'requires', {})
        if requires.get('formation'):
            if not self.config.formation:
                sys.exit("no formation; specify using -f")
        if requires.get('project_dir'):
            if not self.config.project_dir:
                sys.exit("no project dir; specify using --project-dir")
        if requires.get('stage'):
            if not self.config.stage_config:
                sys.exit("no stage")


def main(argv=sys.argv[1:]):
    myapp = GilliamApp(CommandManager('gilliam.commands'),
                       ExtensionManager('gilliam.services',
                                        invoke_on_load=True))
    return myapp.run(argv)
