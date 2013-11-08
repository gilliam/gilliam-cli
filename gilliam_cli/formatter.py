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


from cliff.formatters.base import ListFormatter, SingleFormatter


def pad(s, w):
    return '%-*s' % (w, s)


class SimpleTableFormatter(ListFormatter, SingleFormatter):
    """Simple output formatter with a 'pretty' header."""

    ALIGNMENTS = {
        int: 'r',
        str: 'l',
        float: 'r',
    }

    try:
        ALIGNMENTS[unicode] = 'l'
    except NameError:
        pass

    def add_argument_group(self, parser):
        pass

    def emit_list(self, column_names, data, stdout, parsed_args):
        widths = {name: len(name) for name in column_names}
        alignment = {}
        data_iter = iter(data)
        rows = []
        try:
            first_row = next(data_iter)
        except StopIteration:
            pass
        else:
            for value, name in zip(first_row, column_names):
                alignment[name] = self.ALIGNMENTS.get(type(value), 'l')
                widths[name] = max(len(str(value)), widths[name])
            rows.append(first_row)
            for row in data_iter:
                rows.append(row)
                for value, name in zip(row, column_names):
                    widths[name] = max(len(str(value)), widths[name])

        for name in column_names:
            padded = pad(name, widths[name] + 1)
            stdout.write(padded)
        stdout.write('\n')
        for name in column_names:
            padded = pad('-' * widths[name], widths[name] + 1)
            stdout.write(padded)
        stdout.write('\n')

        for row in rows:
            for value, name in zip(row, column_names):
                w = widths[name]
                a = alignment[name]
                padded = ('%-*s' % (w, str(value)) if a == 'l' else
                          '%*s' % (w, str(value)))
                stdout.write(padded + ' ')
            stdout.write('\n')

    emit_one = emit_list
