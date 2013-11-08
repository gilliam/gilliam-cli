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

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = [line for line in f.read().splitlines()
                if not line.startswith("#")]

setup(
    name="gilliam-cli",
    version="0.1.0",
    packages=find_packages(),
    scripts=['bin/gilliam'],
    author="Johan Rydberg",
    author_email="johan.rydberg@gmail.com",
    description="Command-line client for Gilliam",
    license="Apache 2.0",
    keywords="app platform",
    url="https://github.com/gilliam/",
    install_requires=required,
    entry_points={
        'gilliam.commands': [
            'create = gilliam_cli.commands.formation:Create',
            'ps = gilliam_cli.commands.processes:ProcessStatus',
            'scale = gilliam_cli.commands.processes:Scale',
            'spawn = gilliam_cli.commands.processes:Spawn',
            'run = gilliam_cli.commands.run:Run',
            'deploy = gilliam_cli.commands.deploy:Deploy',
            'route = gilliam_cli.commands.route:Route',
            'routes = gilliam_cli.commands.route:Routes',
            'env = gilliam_cli.commands.env:Show',
            'set = gilliam_cli.commands.env:Set',
            'unset = gilliam_cli.commands.env:Unset',
            'releases = gilliam_cli.commands.releases:Releases',
            'dump release = gilliam_cli.commands.releases:DumpRelease',
            ],
        'gilliam.services': [
            'etcd = gilliam_cli.services.etcd:EtcdService'
            ],
        'cliff.formatter.list': [
            'simple-table = gilliam_cli.formatter:SimpleTableFormatter'
            ],
        'cliff.formatter.show': [
            'simple-table = gilliam_cli.formatter:SimpleTableFormatter'
            ],
        },
    zip_safe=False
)
