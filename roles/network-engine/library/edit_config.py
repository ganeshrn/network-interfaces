#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: edit_config
short_description: Apply configuration on the remote device
description:
  - This module will connect to the remote network device and apply the configuration on
    remote device.
version_added: "2.5"
options:
  source:
    description:
      - Specifies the configuration to return from the network device.  This
        argument accepts one of two values, either C(running) or C(startup).
    required: false
    default: running
    choices:
      - running
      - candidate
  config:
    description:
      - Configuration change that needs to applied on remote network device.
        If the underlying connetcion type is network_cli the configuration is
        expected to be in cli command format and incase the connection type is netconf
        configuration is expected to be in xml string format
author:
  - Ansible Network Team
"""

EXAMPLES = """
- name: return the current device config
  edit_config:
    source: running
    config: "hostname localhost\nip domain-name ansible.com"
"""

RETURN = """
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        source=dict(default='running', choices=['running', 'startup']),
        config=dict()
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    source = module.params['source']
    config = module.params['config']

    changed = False
    if config:
        connection = Connection(module._socket_path)
        capabilities = connection.get_capabilities()
        output = connection.edit_config(source=source, config=config)

        if 'commit' in capabilities['rpc']:
            connection.commit()
        changed = True


    result = {
        'changed': changed,
        'text': output
    }

    module.exit_json(**result)


if __name__ == '__main__':
    main()
