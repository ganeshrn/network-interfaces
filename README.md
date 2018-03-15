# Role Name: network-interfaces
The ```network-interfaces``` role provides a set of tasks to configure interfaces on remote network
device. The role provides tasks for 
* Validation input interface configuration in json/yaml format which conforms with a yang model
  (currently only openconfig yang is supported) against Ansible spec file which is dervied 
  from corresponding yang interfaces model. 
* Convert input json/yaml format to corresponding native device specific cli commands or xml string
  based on connection type ie. either nework_cli or netconf.
* Retrive current running interface configuration from remote host
* Generate diff between running and candidate configuration in native format
* Push the diff configuration to remote network device.
 
Any open bugs and/or feature requests are tracked in [Github issues](../../issues).

Interested in contributing to this role, please see [CONTRIBUTING](CONTRIBUTING.md)

## Requirements
None

## Role Tasks
The following are the available tasks provided by this role for use in
playbooks.

* validate_input [[source]](tasks/validate_input.yml) [[docs]](docs/validate_input.md)
* parser [[source]](tasks/parser.yml) [[docs]](docs/parser.md)
* get_config [[source]](tasks/get_config.yml) [[docs]](docs/get_config.md)
* get_config_diff [[source]](tasks/get_config_diff.yml) [[docs]](docs/get_config_diff.md)
* edit_config [[source]](tasks/edit_config.yml) [[docs]](docs/edit_config.md)
* edit_config [[source]](tasks/main.yml) [[docs]](docs/main.md)

## Role Variables
The following role variables are defined by this role.

### ansible_network_os
Configure the network os value for the network device.  This role variable is
used to map the role actions to device specific provider implementations.
Typically this value should be set in the playbook inventory for the host.  

### module
The name of the modules which is same as the yang model suffix name.
The default value is ```interfaces```

### config_file
This role variable is used to determine the path to input json/yaml configuration file.

The default value is ```{{ playbook_dir }}/vars/config.yml```

### spec_file
This role variable is used to determine the path of spec file which is used to validate input 
configuration.

The default value is ```{{ playbook_dir }}/files/spec/{{ yang_variant }}_{{ module }}.yml```

### source_dirs
This role variable is used to determine the pat to the template files that render the device configuration 

The default value is ```{{ playbook_dir }}/templates/{{ yang_variant }}/{{ ansible_network_os }}/{{ ansible_connection }}.cfg```

### xpath_map
This role variable is used to determine the path to the location of xpath map file. 

The default value is ```{{ playbook_dir }}/files/map/{{ yang_variant }}/{{ ansible_network_os }}.yml```

## Modules
The following is a list of modules that are provided by this role.

None

## Plugins
The following is a list of plugins that are provided by this role.

None

## Dependencies
The following is the list of dependencies on other roles this role requires.

* [network-config](http://github.com/ansible-network/network-config)

## License
GPLv3

## Author Information
Ansible Network Engineering Team
