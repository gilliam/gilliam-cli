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

import abc


class BaseService(object):
    """Base class for services."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def detect(self, name, data):
        """Detect if the given definition can be of this service type.

        :param name: Name of the service.
        :type name: str.

        :param data: A dictionary of the service definition.
        :type data: dict.

        :returns: True if this service type matches the definition.
        """

    @abc.abstractmethod
    def build(self, name, data):
        """...

        :param name: Name of the service.
        :type name: str.

        :param data: A dictionary of the service definition.
        :type data: dict.
        """
