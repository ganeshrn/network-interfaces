# -*- coding: utf-8 -*-

# (c) 2018, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# You should have received a copy of the GNU General Public License
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re
import collections

from ansible import constants as C
from ansible.plugins.action import ActionBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.six import iteritems, string_types
from ansible.module_utils._text import to_text
from ansible.errors import AnsibleError, AnsibleUndefinedVariable

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def warning(msg):
    if C.ACTION_WARNINGS:
        display.warning(msg)


class ActionModule(ActionBase):

    VALID_FILE_EXTENSIONS = ('.yaml', '.yml', '.json')
    VALID_GROUP_DIRECTIVES = ('context', 'pattern_group')
    VALID_ACTION_DIRECTIVES = ('pattern_match', 'export_facts', 'lines_template', 'json_template')
    VALID_DIRECTIVES = VALID_GROUP_DIRECTIVES + VALID_ACTION_DIRECTIVES

    def set_args(self):
        """ sets instance variables based on passed arguments
        """
        try:
            self.source_dirs = to_list(self._task.args['source_dirs'])

            self.exclude_files = self._task.args.get('exclude_files')
            self.include_files = self._task.args.get('include_files')

            self.private_vars = self._task.args.get('private_vars') or {}

            self.skip = self._task.args.get('skip')

            indent = self._task.args.get('indent') or 1

            if self._task.args.get('inheret', True):
                self.source_dirs = to_list(self.source_dirs[0])

        except KeyError as exc:
            raise AnsibleError('missing required argument: %s' % exc)

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        self.set_args()

        self.ds = task_vars.copy()
        self.ds.update(self.private_vars)

        include_files = self.included_files()

        config_lines = list()

        for source in include_files:
            display.display('including file %s' % source)
            tasks = self._loader.load_from_file(source)

            for task in tasks:
                name = task.pop('name', None)

                register = task.pop('register', None)

                when = task.pop('when', None)
                if when is not None:
                    if not self._check_conditional(when, task_vars):
                        warning('skipping task due to conditional check failure')
                        continue

                loop = task.pop('loop', None)

                if loop:
                    loop = self.template(loop, self.ds)
                    loop_result = list()

                    if isinstance(loop, collections.Mapping):
                        for loop_key, loop_value in iteritems(loop):
                            self.ds['item'] = {'key': loop_key, 'value': loop_value}
                            res = self._process_directive(task)
                            if res:
                                loop_result.extend(to_list(res))

                    elif isinstance(loop, collections.Iterable) and not isinstance(loop, string_types):
                        for loop_item in loop:
                            self.ds['item'] = loop_item
                            res = self._process_directive(task)
                            if res:
                                loop_result.extend(to_list(res))

                    config_lines.extend(loop_result)

                    if register:
                        self.ds[register] = loop_result

                else:
                    res = self._process_directive(task)
                    if res:
                        config_lines.extend(to_list(res))
                        if register:
                            self.ds[register] = res

        result.update({
            'text': '\n'.join(config_lines),
            'lines': config_lines,
            'included_files': include_files
        })

        return result

    def do_context(self, block):

        results = list()

        for entry in block:
            task = entry.copy()

            name = task.pop('name', None)
            register = task.pop('register', None)

            when = task.pop('when', None)
            if when is not None:
                if not self._check_conditional(when, self.ds):
                    warning('skipping context due to conditional check failure')
                    continue

            loop = task.pop('loop', None)
            if loop:
                loop = self.template(loop, self.ds)

            if 'context' in task:
                res = self.do_context(task['context'])
                if res:
                    results.extend(res)

            elif isinstance(loop, collections.Mapping):
                loop_result = list()
                for loop_key, loop_value in iteritems(loop):
                    self.ds['item'] = {'key': loop_key, 'value': loop_value}
                    loop_result.extend(to_list(self._process_directive(task)))
                results.extend(loop_result)

            elif isinstance(loop, collections.Iterable) and not isinstance(loop, string_types):
                loop_result = list()
                for loop_item in loop:
                    self.ds['item'] = loop_item
                    loop_result.extend(to_list(self._process_directive(task)))
                results.extend(loop_result)

            else:
                res = self._process_directive(task)
                if res:
                    results.extend(to_list(res))

        return results

    def _process_directive(self, task):
        for directive, args in iteritems(task):
            if directive in self.VALID_GROUP_DIRECTIVES:
                meth = getattr(self, 'do_%s' % directive)
                if meth:
                    return meth(args)
            elif directive in self.VALID_ACTION_DIRECTIVES:
                meth = getattr(self, 'do_%s' % directive)
                if meth:
                    return meth(**args)

    def _check_file(self, filename, matches):
        """ Checks the file against a list of matches

        If the filename is included as part of the list of matches, this
        method will return True.  If it is not, then this method will
        return False

        :param filename: The filename to be matched
        :param matches: The list of matches to test against

        :returns: True if the filename should be ignored otherwise False
        """
        if isinstance(matches, string_types):
            matches = [matches]
        if not isinstance(matches, list):
            raise AnsibleError("matches must be a valid list")
        for pattern in matches:
            if re.search(r'%s' % pattern, filename):
                return True
        return False

    def should_include(self, filename):
        if self.include_files:
            return self._check_file(filename, self.include_files)
        return True

    def should_exclude(self, filename):
        if self.exclude_files:
            return self._check_file(filename, self.exclude_files)
        return False

    def included_files(self):
        include_files = list()
        _processed = set()

        for source_dir in self.source_dirs:
            if not os.path.isdir(source_dir):
                if self.skip:
                    continue
                raise AnsibleError('%s does not appear to be a valid directory' % source_dir)

            for filename in os.listdir(source_dir):
                fn, fext = os.path.splitext(filename)
                if fn not in _processed:
                    _processed.add(fn)

                    filename = os.path.join(source_dir, filename)

                    if not os.path.isfile(filename) or fext not in self.VALID_FILE_EXTENSIONS:
                        continue

                    elif self.should_exclude(os.path.basename(filename)):
                        warning('excluding file %s' % filename)
                        continue

                    elif not self.should_include(os.path.basename(filename)):
                        warning('skipping file %s' % filename)
                        continue

                    else:
                        include_files.append(filename)

        return include_files


    def do_lines_template(self, template, join=False, when=None, required=False):
        templated_lines = list()
        _processed = list()

        if when is not None:
            if not self._check_conditional(when, self.ds):
                warning("skipping due to conditional failure")
                return templated_lines

        for line in to_list(template):
            res = self.template(line, self.ds)
            if res:
                _processed.append(res)
            elif not res and join:
                break

        if required and not _processed:
            raise AnsibleError('unabled to templated required line')
        elif _processed and join:
            templated_lines.append(' '.join(_processed))
        elif _processed:
            templated_lines.extend(_processed)

        return templated_lines

    def _process_include(self, item, variables):
        name = item.get('name')
        include = item['include']

        src = self.template(include, variables)
        source = self._find_needle('templates', src)

        when = item.get('when')

        if when:
            conditional = "{%% if %s %%}True{%% else %%}False{%% endif %%}"
            if not self.template(conditional % when, variables, fail_on_undefined=False):
                display.vvvvv("include '%s' skipped due to conditional check failure" % name)
                return []

        display.display('including file %s' % source)
        include_data = self._loader.load_from_file(source)

        template_data = item.copy()

        # replace include directive with block directive and contents of
        # included file.  this will preserve other values such as loop,
        # loop_control, etc
        template_data.pop('include')
        template_data['block'] = include_data

        return self.build([template_data], variables)

    def template(self, data, variables, convert_bare=False):

        if isinstance(data, collections.Mapping):
            templated_data = {}
            for key, value in iteritems(data):
                templated_key = self.template(key, variables, convert_bare=convert_bare)
                templated_data[templated_key] = self.template(value, variables, convert_bare=convert_bare)
            return templated_data

        elif isinstance(data, collections.Iterable) and not isinstance(data, string_types):
            return [self.template(i, variables, convert_bare=convert_bare) for i in data]

        else:
            data = data or {}
            tmp_avail_vars = self._templar._available_variables
            self._templar.set_available_variables(variables)
            try:
                resp = self._templar.template(data, convert_bare=convert_bare)
                resp = self._coerce_to_native(resp)
            except AnsibleUndefinedVariable:
                resp = None
                pass
            finally:
                self._templar.set_available_variables(tmp_avail_vars)
            return resp

    def _coerce_to_native(self, value):
        if not isinstance(value, bool):
            try:
                value = int(value)
            except Exception as exc:
                if value is None or len(value) == 0:
                    return None
                pass
        return value

    def _check_conditional(self, when, variables):
        conditional = "{%% if %s %%}True{%% else %%}False{%% endif %%}"
        return self.template(conditional % when, variables)
