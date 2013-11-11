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

import shortuuid

from ..command import Command, ListerCommand


class Route(Command):
    """\
    Set up a route for incoming requests.

    To route all domains done to a specific domain to a service:

      gilliam-cli route api.domain.tld/{rest:.*?} api.service/{rest}

    For example, to route everything under `/v1/` to the v1 service in
    the api formation:

      gillial-cli route /v1/{rest:.*?} v1.api.service/{rest}

    To route authentication requests:

      gilliam-cli route /login/{provider} auth.service/{provider}
    """

    def get_parser(self, prog_name):
        parser = Command.get_parser(self, prog_name)
        parser.add_argument(
            '-d', '--delete',
            action="store_true"
            )
        parser.add_argument(
            'route',
            nargs='?'
            )
        parser.add_argument(
            'target',
            nargs='?'
            )
        return parser

    def _parse_route(self, route):
        domain, path = route.split('/', 1)
        domain = domain if domain else None
        path = '/{0}'.format(path)
        return domain, path

    def _delete(self, router, options):
        router.delete(options.route)

    def _create(self, router, options):
        if not options.target:
            sys.exit("must specify route target")

        # Always assume that we're dealing with HTTP.
        if not options.target.startswith('http://'):
            options.target = 'http://' + options.target

        domain, path = self._parse_route(options.route)
        route = router.create(shortuuid.uuid(), domain, path, options.target)
        self.app.stdout.write('route {0}\n'.format(route['name']))

    def take_action(self, options):
        router = self.app.config.router()
        if options.delete:
            self._delete(router, options)
        else:
            self._create(router, options)


class Routes(ListerCommand):
    """list existing routes"""
    FIELDS = ('name', 'domain', 'path', 'target')

    def take_action(self, options):
        def it(router, fields):
            for route in router.routes():
                yield [route.get(f) for f in fields]
        return self.FIELDS, it(self.app.config.router(), self.FIELDS)
