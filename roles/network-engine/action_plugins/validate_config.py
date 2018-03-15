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

    def set_args(self):
        """ sets instance variables based on passed arguments
        """
        try:
            self.source_dirs = to_list(self._task.args['source_dirs'])

            self.spec = self._task.args.get('spec')
            self.config = self._task.args.get('config')

        except KeyError as exc:
            raise AnsibleError('missing required argument: %s' % exc)

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        self.set_args()

        result.update({
            'config': self.config
        })

        return result
