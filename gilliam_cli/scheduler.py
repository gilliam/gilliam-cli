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

"""High-level interface for the scheduler."""

import getpass
import time

from gilliam.errors import ConflictError


def _merge_service_env(base, services):
    """Given two sets of service environments, copy environment
    variables from `base` to `services`.
    """
    result = services.copy()
    for name, defn in result.items():
        env = defn.get('env', {})
        val = base.get(name, {}).get('env', {})
        env.update({k: v for (k, v) in val if k not in env})
    return result


class Formation(object):

    def __init__(self, client, formation):
        self.client = client
        self.formation = formation

    def _name_release(self, current):
        return str(int(current['name']) + 1 if current is not None else 1)

    @property
    def last_release(self):
        releases = list(self.client.releases(self.formation))
        if not releases:
            return None
        releases.sort(key=lambda release: int(release['name']))
        return releases[-1]

    def find_release(self, name):
        for release in self.client.releases(self.formation):
            if release['name'] == name:
                return release
        return None

    def release(self, author, message, services, merge_env=True):
        while True:
            current = self.last_release
            try:
                response = self.client.create_release(
                    self.formation, self._name_release(current),
                    author or getpass.getuser(), message,
                    _merge_service_env(current.get('services', {}), services)
                    if (merge_env and current) else services
                    )
            except ConflictError:
                continue
            else:
                return response['name']

    def migrate(self, release, rate):
        while True:
            more = self.client.migrate(self.formation, release)
            if not more:
                break
            else:
                time.sleep(rate)

    def scale(self, release, scales, rate):
        while True:
            more = self.client.scale(self.formation, release,
                                     scales)
            if not more:
                break
            else:
                time.sleep(rate)


class Scheduler(object):

    def __init__(self, client):
        self.client = client

    def formation(self, formation):
        return Formation(self.client, formation)
