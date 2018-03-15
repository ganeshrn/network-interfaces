# -*- coding: utf-8 -*-

# (c) 2018, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# You should have received a copy of the GNU General Public License
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import StringIO

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError

try:
    import textfsm
    HAS_TEXTFSM = True
except ImportError:
    HAS_TEXTFSM = False


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        if not HAS_TEXTFSM:
            raise AnsibleError('textfsm engine requires the TextFSM library to be installed')

        result = super(ActionModule, self).run(tmp, task_vars)

        try:
            filename = self._task.args.get('file')
            src = self._task.args.get('src')
            contents = self._task.args['contents']
            name = self._task.args.get('name')
        except KeyError as exc:
            raise AnsibleError('missing required argument: %s' % exc)

        if src and filename:
            raise AnsibleError('`src` and `file` are mutually exclusive arguments')

        if filename:
            tmpl = open(filename)
        else:
            tmpl = StringIO.StringIO()
            tmpl.write(src.strip())
            tmpl.seek(0)

        try:
            re_table = textfsm.TextFSM(tmpl)
            fsm_results = re_table.ParseText(contents)

        except Exception as exc:
            raise AnsibleError(str(exc))

        facts = {}
        for item in fsm_results:
            facts.update(dict(zip(re_table.header, item)))

        if name:
            result['ansible_facts'] = {name: facts}
        else:
            result['ansible_facts'] = facts

        return result
