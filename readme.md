# NSX for vSphere Ansible Modules

This repository contains a number of Ansible modules, written in Python, that can be used
to create, read, update and delete objects in NSX for vSphere.

## Requirements

This module requires the NSX for vSphere RAML file (RAML based documentation).
The latest version of the NSX for vSphere RAML file can be found and downloaded here: http://github.com/vmware/nsxraml.

The Python based ``nsxramlclient`` must also be installed. Example of installing using pip:
```sh
sudo pip install nsxramlclient
```
More details on this Python client for the NSX for vSphere API can be found here: http://github.com/vmware/nsxramlclient. Additional details on installation is also available.

## How to use these modules

Before using these modules the library from ``nsxansible`` needs to be either copied into the top level ansible directory where playbooks are stored or there needs to be a soft link to the library directory.

All modules need to be executed on a host that has ``nsxramclient`` installed and the host must have access to a copy of the NSX RAML File. In most deployments this likely to be localhost.
```yaml
---
- hosts: localhost
  connection: local
  gather_facts: False
```
Each module needs an array called ```nsxmanager_spec``` with following parameters supplied:
- The location of the NSX-v RAML file describing the NSX for vSphere API
- The NSX Manager where the API is running. Can be referenced by either a hostname or an IP Address.
- The NSX Manager username
- The NSX Manager password for the above user

These parameters are usually placed in a common variables file:

`answerfile.yml`
```yaml
nsxmanager_spec: 
  raml_file: '/raml/nsxraml/nsxvapiv614.raml'
  host: 'nsxmanager.invalid.org'
  user: 'admin'
  password: 'vmware'
```
`test_logicalswitch.yml`
```yaml
---
- hosts: localhost
  connection: local
  gather_facts: False
  vars_files:
     - answerfile.yml
  tasks:
  - name: logicalSwitch Operation
    logicalSwitch:
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      state: present
      transportzone: "TZ"
      name: "TestLS"
      controlplanemode: "UNICAST_MODE"
      description: "My Great Logical Switch"
    register: create_logical_switch

  - debug: var=create_logical_switch
```
The example shows thes ```nsxmanager_spec``` is read out of the file ```answerfile.yml```.

## Module specific parameters

Every module has specific parameters that are explained in the following sections:

###  Module `logicalSwitch`
##### Create, update and delete logical Switches
- state: 
present or absent, defaults to present
- name: 
Mandatory: Name of the logical switch. Updating the name creates a new switch as it is the unique
identifier.
- transportzone: 
Mandatory: Name of the transport zone in which the logical switch is created.
- controlplanemode:
Mandatory: Control plane mode for the logical switch. The value can be 'UNICAST_MODE',
'HYBRID_MODE' or 'MULTICAST_MODE'. Default is 'UNICAST_MODE'.
- description:
Optional: Free text description for the logical switch.

Example:
```yaml
---
- hosts: localhost
  connection: local
  gather_facts: False
  vars_files:
     - answerfile.yml
  tasks:
  - name: logicalSwitch Operation
    logicalSwitch:
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      state: absent
      transportzone: "TZ"
      name: "TestLS"
      controlplanemode: "UNICAST_MODE"
      description: "My Great Logical Switch"
    register: create_logical_switch

  #- debug: var=create_logical_switch
```

###  Module `nsxVcRegistration`
##### Registers NSX Manager to VC or changes the registration

- vcenter: 
Hostname or IP address of the vCenter server to which NSX Manager should be registered/
- vcusername:
Username on the vCenter that should be used to register NSX Manager.
- vcpassword:
Password of the vCenter user used to register NSX Manager.
- vccertthumbprint: 
Certificate thumbprint of vCenter service.

All above values are mandatory.

Example:
```yaml
---
- hosts: localhost
  connection: local
  gather_facts: False
  vars_files:
     - answerfile.yml
  tasks:
  - name: NSX Manager VC Registration
    nsxVcRegistration:
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      vcenter: 'testvc'
      vcusername: 'root'
      vcpassword: 'vmware'
      vccertthumbprint: 'D8:E1:1F:C1:AD:F7:BA:08:34:0B:20:63:CE:2B:42:C3:CC:90:20:AE'
    register: register_to_vc

  #  - debug: var=register_to_vc
```

### Module `nsxSsoRegistration`
##### Registers NSX Manager to SSO or changes and deletes the SSO Registration

- state:
present or absent, defaults to present
- sso_lookupservice_url:
SSO Lookup Service url. Example format: https://ip_or_hostname:7444/lookupservice/sdk
- sso_admin_username: 
Username to register to SSO. Typically thi sis administrator@vsphere.local
- sso_admin_password:
Password of the SSO user used to register.
- sso_certthumbprint: 
Certificate thumbprint of SSO service.

All above values are mandatory

Example:
```yaml
---
- hosts: localhost
  connection: local
  gather_facts: False
  vars_files:
     - answerfile.yml
  tasks:
  - name: NSX Manager SSO Registration
    nsxSsoRegistration:
      state: present
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      sso_lookupservice_url: 'https://172.17.100.60:7444/lookupservice/sdk'
      sso_admin_username: 'administrator@vsphere.local'
      sso_admin_password: 'vmware'
      sso_certthumbprint: '33:80:F0:58:DB:D4:59:A2:46:14:83:14:2C:48:C3:29:70:25:BE:31'
    register: register_to_sso

#  - debug: var=register_to_sso
```

### Module `nsxIpPool`
##### Create, update and delete an IP Pool in NSX Manager

- state:
present or absent, defaults to present
- name: 
Mandatory: Name of the IP Pool. Updating the name creates a new IP Pool as it is the unique
identifier.
- start_ip:
Mandatory: Start IP address in the pool.
- end_ip:
Mandatory: End IP address in the pool.
- prefix_length:
Mandatory: Prefix length of the IP pool (i.e. the number of bits in the subnet mask).
- gateway:
Optional: Default gateway in the IP pool.
- dns_server_1:
Optional: First DNS server in the pool.
- dns_server_2:
Optional: Second DNS server in the pool.

Example:
```yaml
---
- hosts: localhost
  connection: local
  gather_facts: False
  vars_files:
     - answerfile.yml
  tasks:
  - name: Controller IP Pool creation
    nsxIpPool:
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      state: present
      name: 'ansible_controller_ip_pool'
      start_ip: '172.17.100.65'
      end_ip: '172.17.100.67'
      prefix_length: '24'
      gateway: '172.17.100.1'
      dns_server_1: '172.17.100.11'
      dns_server_2: '172.17.100.12'
    register: create_ip_pool

  #- debug: var=create_ip_pool
```

### Module `nsxControllers`
##### Deploy individual controllers, full 3 node clusters as well as 1 node lab deyployments including syslog configuration

- state:
present or absent, defaults to present
- deploytype: 
lab, single of full, defaults to full
 - lab: Only a single controller gets deployed. If there are already controllers deployed in the setup, 'lab' will leave the environment unchanged, and will only apply changes to syslog if needed
 - single: This will create a new controller if the number of existing controllers in the setup is 0, 1 or 2. If the number of existing controllers is 3, 'single'  will leave the environment unchanged, and only apply changes to syslog if needed. You can use this option if you want to deploy a controller cluster with individual nodes placed into e.g. different datastores, clusters or networks
 - full: This will create a full cluster of 3 controller nodes. If there is any existing controller found, 'full' will leave the environment unchanged and only apply changes to syslog if needed. Use this option if you want to deploy a full 3 node cluster, and all node should be placed on the the same datastore, cluster, network, etc.
- syslog_server: 
Optional: This will set the syslog server on **all** controller nodes found in the setup.
  - If not set or left out in the play: If no value is set, but existing controllers have syslog configured, all controller syslog configuration will be blanked out
  - SyslogIP: If the IP of the syslog server is passed, if will be configured on **all** controller nodes found in the setup
- ippool_id:
Mandatory: The IP Pool used to assign IP Addresses to controller nodes
- resourcepool_moid:
Mandatory: The vSphere Managed Object Id of the vSphere cluster or ressource pool to deploy the controller into
- host_moid:
Optional: The vSphere Managed Object Id of an individual host where to place the controller in
- datastore_moid:
Mandatory: The vSphere Managed Object Id of a datastore to deploy the controller into
- network_moid:
Mandatory: The vSphere Managed Object Id of the management network the controller should be using
- password:
Mandatory: The controller CLI and SSH password of the 'admin' user


Example:
```yaml
---
- hosts: localhost
  connection: local
  gather_facts: False
  vars_files:
     - answerfile_new_nsxman.yml
  tasks:
  - name: Controller Cluster Creation
    nsxControllers:
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      state: present
      deploytype: 'lab'
      syslog_server: '172.17.100.129'
      ippool_id: 'ipaddresspool-2'
      resourcepool_moid: 'domain-c26'
      #host_moid: 'host-29'
      datastore_moid: 'datastore-37'
      network_moid: 'dvportgroup-36'
      password: 'VMware1!VMware1!'
    register: create_controller_cluster

  #- debug: var=create_controller_cluster
```

## License

Copyright © 2015 VMware, Inc. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.


