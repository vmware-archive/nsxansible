# NSX for vSphere Ansible Modules

This repository contains a number of Ansible modules, written in Python, that can be used
to create, read, update and delete objects in NSX for vSphere.

# Version notice

Due to the latest changes to the way schemas are handled in the nsxraml file starting with NSX-v version 6.2.3, nsxansible requires nsxramlclient 2.0.0 or later. To upgrade the nsxramlclient you can do a ``sudo pip install --upgrade nsxramlclient``. Also please use the latest version of the RAML spec.

## Requirements

This module requires the NSX for vSphere RAML spec (RAML based documentation).
The latest version of the NSX for vSphere RAML spec (raml file + schema files) can be found and downloaded here: http://github.com/vmware/nsxraml.

The Python based ``nsxramlclient`` must also be installed and needs to be on version 2.0.0. Example of installing using pip:
```sh
sudo pip install nsxramlclient
```
More details on this Python client for the NSX for vSphere API can be found here: http://github.com/vmware/nsxramlclient. Additional details on installation is also available.

In addition, the 'vcenter_gather_facts' and 'deploy_nsx_ova' modules require that you have the vCenter python client 'Pyvmomi' installed. Example of installing PyVmomi using pip:
```sh
sudo pip install pyvmomi
```
More details on this Python client for vCenter can be found here: http://github.com/vmware/pyvmomi. Additional details on installation is also available.

The 'deploy_nsx_ova' module also requires that the machine on which the play is executed has ``ovftool`` installed.
Ovftool is part of VMware Fusion on Mac, and can be installed on most Linux systems. For more information see https://www.vmware.com/support/developer/ovf/

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
    nsx_logical_switch:
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

###  Module `nsx_logical_switch`
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
    nsx_logical_switch:
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      state: absent
      transportzone: "TZ"
      name: "TestLS"
      controlplanemode: "UNICAST_MODE"
      description: "My Great Logical Switch"
    register: create_logical_switch

  #- debug: var=create_logical_switch
```

###  Module `nsx_vc_registration`
##### Registers NSX Manager to VC or changes the registration

- vcenter:
Mandatory: Hostname or IP address of the vCenter server to which NSX Manager should be registered/
- vcusername:
Mandatory: Username on the vCenter that should be used to register NSX Manager.
- vcpassword:
Mandatory: Password of the vCenter user used to register NSX Manager.
- vccertthumbprint:
Mandatory if 'accept_all_certs' is not 'True': Certificate thumbprint of vCenter service.
- accept_all_certs:
Mandatory if 'vccertthumbprint' is not supplied: If set to 'True', NSX Manager will be connected to any vCenter Server
without checking the certificate thumbprint

*Note: 'accept_all_certs' and 'vccertthumbprint' are mutualy exclusive*

Example:
```yaml
---
- hosts: localhost
  connection: local
  gather_facts: False
  vars_files:
     - answerfile_new_nsxman.yml
  tasks:
  - name: NSX Manager VC Registration
    nsx_vc_registration:
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      vcenter: 'testvc.emea.nicira'
      vcusername: 'administrator@vsphere.local'
      vcpassword: 'vmware'
      #vccertthumbprint: '04:9D:9B:64:97:73:89:AF:16:4F:60:A0:F8:59:3A:D3:B8:C4:4B:A2'
      accept_all_certs: true
    register: register_to_vc

#  - debug: var=register_to_vc
```

### Module `nsx_sso_registration`
##### Registers NSX Manager to SSO or changes and deletes the SSO Registration

- state:
present or absent, defaults to present
- sso_lookupservice_url:
Mandatory: SSO Lookup Service url. Example format: 'lookupservice/sdk'
- sso_lookupservice_port:
Mandatory: SSO Lookup Service port. E.g. '7444'
- sso_lookupservice_server:
Mandatory: SSO Server Hostname, FQDN or IP Address. E.g. 'testvc.emea.nicira'
- sso_admin_username:
Mandatory: Username to register to SSO. Typically thi sis administrator@vsphere.local
- sso_admin_password:
Mandatory: Password of the SSO user used to register.
- sso_certthumbprint:
Mandatory if 'accept_all_certs' is not 'True': Certificate thumbprint of SSO service.
- accept_all_certs:
Mandatory if 'sso_certthumbprint' is not supplied: If set to 'True', NSX Manager will be connected to any SSO Server without checking the certificate thumbprint

*Note: 'accept_all_certs' and 'vccertthumbprint' are mutualy exclusive*

Example:
```yaml
---
- hosts: localhost
  connection: local
  gather_facts: False
  vars_files:
     - answerfile_new_nsxman.yml
  tasks:
  - name: NSX Manager SSO Registration
    nsx_sso_registration:
      state: present
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      sso_lookupservice_url: 'lookupservice/sdk'
      sso_lookupservice_port: 7444
      sso_lookupservice_server: 'testvc.emea.nicira'
      sso_admin_username: 'administrator@vsphere.local'
      sso_admin_password: 'vmware'
      #sso_certthumbprint: 'DE:D7:57:DC:D3:E4:40:4E:AA:4A:3A:56:91:B0:48:92:6E:68:E6:03'
      accept_all_certs: true
    register: register_to_sso

#  - debug: var=register_to_sso
```

### Module `nsx_ippool`
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

Returns:
ippool_id variable will contain the IP Pool Id in NSX (e.g. "ipaddresspool-2") if the ippool is created, updates or un-changed.
None will be returned when the IP Pool state is absent.

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
    nsx_ippool:
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

Example return:
```yaml
- debug: var=controller_ip_pool.ippool_id
```
```sh
ok: [localhost] => {
    "var": {
        "controller_ip_pool.ippool_id": "ipaddresspool-10"
    }
}
```

### Module `nsx_controllers`
##### Deploy individual controllers, full 3 node clusters as well as 1 node lab deployments including syslog configuration

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
Mandatory: The vSphere Managed Object Id of the vSphere cluster or resource pool to deploy the controller into
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
    nsx_controllers:
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

### Module `nsx_segment_id_pool`
##### Configure or delete the VXLAN Segment Id Pool (VXLAN Id space) and optionally associated Multicast Range

- state:
present or absent, defaults to present
- idpoolstart:
Id Pool start Id. Defaults to 5000 if not supplied
- idpoolend:
Id Pool end Id. Defaults to 15000 if not supplied
- mcast_enabled:
If set to true, a multicast range will be configured alongside the Segment Id. Defaults to false if not set.
Setting mcast_enabled to false for an existing segment pool will remove the multicast pool but keep the segment pool
- mcastpoolstart:
Starting Multicast IP Address. Defaults to '239.0.0.0' if not set explicitly. Only used if 'mcast_enabled' is 'true'
- mcastpoolend:
Ending Multicast IP Address. Defaults to '239.255.255.255' if not set explicitly. Only used if 'mcast_enabled' is 'true'

Example:
```yaml
---
- hosts: localhost
  connection: local
  gather_facts: False
  vars_files:
     - answerfile_new_nsxman.yml
  tasks:
  - name: Segment Pool Configuration
    nsx_segment_id_pool:
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      state: present
      #idpoolstart: 5000
      #idpoolend: 15000
      mcast_enabled: true
      #mcastpoolstart: '239.0.0.0'
      #mcastpoolend: '239.255.255.255'
    register: create_segment_pool

  #- debug: var=create_segment_pool
```

### Module `nsx_cluster_prep`
##### Prepares the vSphere Clusters for the use with NSX (Installs the VIBs)

- state:
present or absent, defaults to present.
Present will start the cluster prep (install VIBs) if the cluster is in the 'UNKNOWN' state.
If the cluster is in 'RED' or 'YELLOW' state, the module will fail and ask for manual intervention.
Absent will un-prep the cluster (uninstall the VIBs). This will leave the cluster in the 'RED'
state, requiring the vSphere Admin to reboot the hypervisors to complete the VIB uninstall
- cluster_moid:
Mandatory: The vSphere managed object Id of the cluster to prep or un-prep

Example:
```yml
---
- hosts: localhost
  connection: local
  gather_facts: False
  vars_files:
     - answerfile_new_nsxman.yml
  tasks:
  - name: Cluster preparation
    nsx_cluster_prep:
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      state: present
      cluster_moid: 'domain-c26'
    register: cluster_prep

  #- debug: var=cluster_prep
```

### Module `nsx_vxlan_prep`
##### Prepares the vSphere Cluster and VDS for VXLAN (Configures VTEP Interfaces)

- state:
present or absent, defaults to present.
Present will configure VXLAN according to the passed details or defaults,
Absent will un-configure VXLAN (remove the VTEPs).
- cluster_moid:
Mandatory: The vSphere managed object Id of the cluster to configure VXLAN VTEPs on
- dvs_moid:
Mandatory: The vSphere managed object Id of the distributed vSwitch (dvs) used as the transport
network dvs
- ippool_id:
Optional: If not passed the VTEPs will be set to receive its IP Address via DHCP. If set to
an valid nsx ippool id, the VTEP IP will be allocated from the IP Pool
- vlan_id:
Optional: Defaults to 0 (untagged), if set to a value this specifies the VLAN Id for the VTEP
- vmknic_count:
Optional: Defaults to 1, number of VTEP Interfaces to deploy. This is only working for the teaming modes 'LOADBALANCE_SRCID' and 'LOADBALANCE_SRCMAC' and when multiple uplinks are present
- teaming:
Optional: Defaults to 'FAILOVER_ORDER'. This specifies the uplink teaming mode for the VTEP port-group. Valid values are: FAILOVER_ORDER,ETHER_CHANNEL,LACP_ACTIVE,LACP_PASSIVE,LOADBALANCE_SRCID,LOADBALANCE_SRCMAC & LACP_V2
- mtu:
Optional: Defaults to 1600, the MTU configured for the VTEP and VTEP port-group

Example:
```yml
---
- hosts: localhost
  connection: local
  gather_facts: False
  vars_files:
     - answerfile_new_nsxman.yml
  tasks:
  - name: Cluster VXLAN Preparation
    nsx_vxlan_prep:
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      state: present
      cluster_moid: 'domain-c26'
      dvs_moid: 'dvs-34'
      ippool_id: 'ipaddresspool-3'
      #vlan_id: 100
      #vmknic_count: 1
      #teaming: 'ETHER_CHANNEL'
      #mtu: 9000
    register: vxlan_prep

  #- debug: var=vxlan_prep
```

### Module `vcenter_gather_moids`
##### Retrieves Managed Object Ids (moids) from vCenter to use them in the NSX plays

The NSX modules often need vCenter moids to be presented to them. To retrieve them dynamically from vCenter in
a playbook, you can use the `vcenter_gather_moids` module.

- hostname:
Mandatory: The Hostname, FQDN or IP Address of your vCenter Server
- username:
Mandatory: The Username used to access you vCenter
- password:
Mandatory: The password of your vCenter users
- datacenter_name:
Mandatory: The name of the datacenter object to search, and to search subsequent objects in
- cluster_names:
Optional: The name of the searched cluster object
- resourcepool_names:
Optional: The name of the searched resourcepool object
- dvs_names:
Optional: The name of the searched dvs object
- portgroup_names:
Optional: The name of the searched portgroup object
- datastore_names:
Optional: The name of the searched datastore object

NOTE: All Optional Parameters are single strings. One of the optional parameters needs to be present. Only one parameters
can be searched in a single task:


Example:
```yml
---
- hosts: localhost
  connection: local
  gather_facts: False
  vars_files:
     - answerfile_new_nsxman.yml
  tasks:
  - name: Gather vCenter MOIDs
    vcenter_gather_moids:
      hostname: 'testvc.emea.nicira'
      username: 'administrator@vsphere.local'
      password: 'vmware'
      datacenter_name: 'nsxlabdc'
      cluster_name: 'compute'
      #resourcepool_name: 'test_rp'
      #dvs_name: 'TransportVDS'
      #portgroup_name: 'VM Network'
      #datastore_name: 'NFS-Storage03'
    register: gather_moids_output

  - debug: msg="The searched moid is {{ gather_moids_output.object_id }}"
```

The output of the above example is:

```sh
ok: [localhost] => {
    "msg": "The searched moid is domain-c28"
}
```

The moid of the searched object can be accessed using the 'object_id' attribute of the registered variable.
E.g. in the above example you can reference to the cluster with ```{{ gather_moids_output.object_id }}```

### Module `nsx_deploy_ova`
##### Deploys the OVA of NSX Manager into a vSphere Cluster

This module uses 'ovftool' to deploy the NSX Manager OVA into a vSphere Cluster. It also uses PyVmomi to check the
cluster for VMs with the same name to make this module idempotent. In addition it checks if the NSX Manager API is reachable
and response both on a fresh deployment, as well as if NSX Manager already exists

- ovftool_path:
Mandatory: The filesystem path to the ovftool. This should be '/usr/bin' on most Linux systems, and '/Applications' on Mac
- vcenter:
Mandatory: The vCenter Server in which the OVA File will be deployed
- vcenter_user:
Mandatory: The vCenter user to use
- vcenter_passwd:
Mandatory: The vCenter user password
- datacenter:
Mandatory: The vCenter datacenter object to deploy NSX Manager into
- datastore:
Mandatory: The datastore used to place the NSX Manager root disk
- portgroup:
Mandatory: The portgroup of the management network to patch NSX Manager into
- cluster:
Mandatory: The cluster in which NSX Manager will be deployed
- vmname:
Mandatory: The VM name of NSX Manager in the vCenter Inventory
- hostname:
Mandatory: The Hostname NSX Manager will be configured to use
- dns_server:
Mandatory: The DNS Server NSX Manager will be configured to use
- dns_domain:
Mandatory: The DNS Domain NSX Manager will be configured to use
- gateway:
Mandatory: The default gateway on the management network
- netmask:
Mandatory: The netmask of the management network
- ip_address:
Mandatory: The netmask of the management network
- admin_password:
Mandatory: The password of the 'admin' user in NSX Manager
- enable_password:
Mandatory: The 'enable' password for the NSX Manager CLI
- path_to_ova:
Mandatory: The filesystem path in which the NSX Manager OVA file can be found
- ova_file:
Mandatory: The NSX Manager OVA File to deploy

Example:
```yml
---
- hosts: jumphost
  gather_facts: False
  vars_files:
     - answerfile_new_nsxman.yml
  tasks:
  - name: deploy nsx-man
    nsx_deploy_ova:
      ovftool_path: '/usr/bin'
      datacenter: 'YF-Sofia-Lab'
      datastore: 'storage03-NFS-10GE'
      portgroup: 'vlan100'
      cluster: 'management-and-edge'
      vmname: 'testnsx'
      hostname: 'testnsx.emea.nicira'
      dns_server: '172.17.100.11'
      dns_domain: 'emea.nicira'
      gateway: '172.17.100.1'
      ip_address: '172.17.100.61'
      netmask: '255.255.255.0'
      admin_password: 'vmware'
      enable_password: 'vmware'
      path_to_ova: '/home/nicira/ISOs'
      ova_file: 'VMware-NSX-Manager-6.1.4-2691049.ova'
      vcenter: '172.17.100.130'
      vcenter_user: 'administrator@vsphere.local'
      vcenter_passwd: 'vmware'
    register: deploy_nsx_man

#  - debug: var=deploy_nsx_man
```

### Module `nsx_transportzone`
##### Deploys, updates or deletes a new transport zone in NSX

- name:
Mandatory: name of the transport zone. Updating the name creates a new switch as it is the unique identifier
- state:
present or absent, defaults to present
- controlplanemode:
Mandatory: Default Control plane mode for logical switches in the transport zone. The value can be 'UNICAST_MODE',
'HYBRID_MODE' or 'MULTICAST_MODE'. Default is 'UNICAST_MODE'.
- cluster_moid_list:
Mandatory: A list of vSphere managed object ids of clusters that are part of the transport zone. The list can either be a single cluster like 'domain-c26', or a python list ['domain-c26', 'domain-c28'] or list items in the yaml format as documented in the example bellow. Changing the list will add or remove clusters from the TZ.

Example:
```yml
---
- hosts: localhost
  connection: local
  gather_facts: False
  vars_files:
     - answerfile_new_nsxman.yml
  tasks:
  - name: Transport Zone Creation
    nsx_transportzone:
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      state: 'present'
      name: 'TZ1'
      controlplanemode: 'HYBRID_MODE'
      description: 'My Transport Zone'
      cluster_moid_list:
        - 'domain-c28'
        - 'domain-c26'
    register: transport_zone

#  - debug: var=transport_zone
```

### Module `nsx_edge_router`
##### Deploys, updates or deletes a NSX Edge Services Gateway in NSX

- name:
Mandatory: name of the Edge Services Gateway to be deployed
- state:
Optional: present or absent, defaults to present
- description:
Optional: A free text description for the ESG
- appliance size:
Optional: The ESG size, choices=['compact', 'large', 'xlarge', 'quadlarge'], defaults to 'large'
- resourcepool_moid:
Mandatory: The vCenter MOID of the ressource pool to deploy the ESG in
- datastore_moid:
Mandatory: The vCenter MOID of the datatore to deploy the ESG on
- datacenter_moid:
Mandatory: The vCenter MOID of the datacenter to deploy the ESG in
- interfaces:
Mandatory: A dictionary that holds the configuration of each vnic as a sub-dictionary. See the interfaces details section for more information
- default_gateway:
Optional: The IP Address of the default gateway
- routes:
Optional: A list of dictionaries holding static route configurations. See the route details section for more information
- username:
Optional: The username used for the CLI access to the ESG
- password:
Optional: The password used for the CLI access to the ESG
- remote_access:
Optional: true / false, is SSH access to the ESG enabled, defaults to false
- firewall:
Optional: true / false, is the ESG Firewall enabled, defaults to true
- ha_enabled:
Optional: true / false, deploy ESG as an HA pair, defaults to false
- ha_deadtime:
Optional: Sets the deadtime for Edge HA, defaults to 15

Example:
```yml
- name: ESG creation
    nsx_edge_router:
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      state: present
      name: 'ansibleESG_testplay'
      description: 'This ESG is created by nsxansible'
      resourcepool_moid: "{{ gather_moids_cl.object_id }}"
      datastore_moid: "{{ gather_moids_ds.object_id }}"
      datacenter_moid: "{{ gather_moids_cl.datacenter_moid }}"
      interfaces:
        vnic0: {ip: '10.114.209.94', prefix_len: 27, portgroup_id: "{{ gather_moids_upl_pg.object_id }}", name: 'Uplink vnic', iftype: 'uplink', fence_param: 'ethernet0.filter1.param1=1'}
        vnic1: {ip: '192.168.178.1', prefix_len: 24, logical_switch: 'transit_net', name: 'Internal vnic', iftype: 'internal', fence_param: 'ethernet0.filter1.param1=1'}
      default_gateway: '10.114.209.65'
      routes:
        - {network: '10.11.12.0/24', next_hop: '192.168.178.2', admin_distance: '1', mtu: '1500', description: 'very important route'}
        - {network: '10.11.13.0/24', next_hop: '192.168.178.2', mtu: '1600'}
        - {network: '10.11.14.0/24', next_hop: '192.168.178.2'}
      remote_access: 'true'
      username: 'admin'
      password: 'VMware1!VMware1!'
      firewall: 'false'
      ha_enabled: 'true'
    register: create_esg
    tags: esg_create
```

##### Interfaces Dict
Each vnic passed to the module in the interfaces dictionary variable is defined as a sub-dictionary with the following key / value pairs:

dict key: Each parent disctionary has the key set to the vnic id (e.g. vnic0), followed by a sub-directory with the vnic settings.

Sub-Directory:
- ip:
Mandatory: The IP Address of the vnic
- prefix_len:
Mandatory: The prefix length for the IP on the vnic, e.g. 24 for a /24 (255.255.255.0)
- if_type:
Mandatory: The interface type, either 'uplink' or 'internal'
- logical_switch:
Optional: The logical switch id to attach the ESG vnic to, e.g. virtualwire-10. NOTE: Either logical_switch or portgroupid need to be supplied.
- portgroupid:
Optional: The Portgroup MOID to attach the ESG vnic to, e.g. network-10. NOTE: Either logical_switch or portgroupid need to be supplied.
- fence_param:
Optional: Additional fence parameters supplied to the vnic, e.g. 'ethernet0.filter1.param1=1'

Example:
```yml
interfaces:
  vnic0: {ip: '10.114.209.94', prefix_len: 27, portgroup_id: "{{ gather_moids_upl_pg.object_id }}", name: 'Uplink vnic', iftype: 'uplink', fence_param: 'ethernet0.filter1.param1=1'}
  vnic1: {ip: '192.168.178.1', prefix_len: 24, logical_switch: 'transit_net', name: 'Internal vnic', iftype: 'internal', fence_param: 'ethernet0.filter1.param1=1'}
```

##### Routes list
Each route is passed to the module as a dictionary in a list. Each dictionary has the following key / value pairs:
- network:
Mandatory: The target network for the route, e.g. '10.11.12.0/24'
- next_hop:
Mandatory: The next hop IP for the route, e.g. '192.168.178.2'
- admin_distance:
Optional: The admin_distance to be used for this route
- mtu:
Optional: The MTU supported by this route
- description:
Optional: A free text description for the static route

Example:
```yml
routes:
  - {network: '10.11.12.0/24', next_hop: '192.168.178.2', admin_distance: '1', mtu: '1500', description: 'very important route'}
  - {network: '10.11.13.0/24', next_hop: '192.168.178.2', mtu: '1600'}
  - {network: '10.11.14.0/24', next_hop: '192.168.178.2'}
```


### Module `nsx_dlr`
##### Deploys, updates or deletes a Distributed Logical Router (DLR) in NSX

- name:
Mandatory: name of the DLR to be deployed
- state:
Optional: present or absent, defaults to present
- description:
Optional: A free text description for the DLR
- resourcepool_moid:
Mandatory: The vCenter MOID of the ressource pool to deploy the DLR control VM in
- datastore_moid:
Mandatory: The vCenter MOID of the datatore to deploy the DLR control VM on
- datacenter_moid:
Mandatory: The vCenter MOID of the datacenter to deploy the DLR control VM in
- mgmt_portgroup_moid:
Mandatory: The vCenter MOID of the portgroup used for the HA network and control VM management
- interfaces:
Mandatory: A list that holds the configuration of each interface as a dictionary. See the interfaces details section for more information
- default_gateway:
Optional: The IP Address of the default gateway
- routes:
Optional: A list of dictionaries holding static route configurations. See the route details section for more information
- username:
Optional: The username used for the CLI access to the DLR Control VM
- password:
Optional: The password used for the CLI access to the DLR Control VM
- remote_access:
Optional: true / false, is SSH access to the DLR Control VM enabled, defaults to false
- ha_enabled:
Optional: true / false, deploy DLR Control VM as an HA pair, defaults to false
- ha_deadtime:
Optional: Sets the deadtime for Edge HA, defaults to 15

Example:
```yml
  - name: DLR creation
    nsx_dlr:
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      state: present
      name: 'ansibleDLR'
      description: 'This DLR is created by nsxansible'
      resourcepool_moid: "{{ gather_moids_cl.object_id }}"
      datastore_moid: "{{ gather_moids_ds.object_id }}"
      datacenter_moid: "{{ gather_moids_cl.datacenter_moid }}"
      mgmt_portgroup_moid: "{{ gather_moids_pg.object_id }}"
      interfaces:
        - {name: 'Uplink vnic', ip: '192.168.178.2', prefix_len: 24, logical_switch: 'edge_ls', iftype: 'uplink'}
        - {name: 'Internal iface', ip: '172.16.1.1', prefix_len: 24, portgroup_id: "{{ gather_moids_pg.object_id }}", iftype: 'uplink'}
        - {name: 'Internal new', ip: '172.16.4.1', prefix_len: 26, logical_switch: 'new_lswitch_name', iftype: 'internal'}
      routes:
        - {network: '10.11.22.0/24', next_hop: '172.16.1.2', admin_distance: '1', mtu: '1500', description: 'very important route'}
        - {network: '10.11.23.0/24', next_hop: '172.16.1.2', mtu: '1600'}
        - {network: '10.11.24.0/24', next_hop: '172.16.4.2'}
        - {network: '10.11.25.0/24', next_hop: '172.16.4.2'}
      default_gateway: '192.168.178.1'
      remote_access: 'true'
      username: 'admin'
      password: 'VMware1!VMware1!'
      ha_enabled: 'true'
    register: create_dlr
    tags: dlr_create
```

##### Interfaces list
Each interface passed to the module in the interfaces list variable is defined as a dictionary with the following key / value pairs:

- ip:
Mandatory: The IP Address of the interface
- prefix_len:
Mandatory: The prefix length for the IP on the interface, e.g. 24 for a /24 (255.255.255.0)
- if_type:
Mandatory: The interface type, either 'uplink' or 'internal'
- logical_switch:
Optional: The logical switch id to attach the DLR Interface to, e.g. virtualwire-10. NOTE: Either logical_switch or portgroupid need to be supplied.
- portgroupid:
Optional: The Portgroup MOID to attach the DLR Interface to, e.g. network-10. NOTE: Either logical_switch or portgroupid need to be supplied.

Example:
```yml
interfaces:
  - {name: 'Uplink vnic', ip: '192.168.178.2', prefix_len: 24, logical_switch: 'edge_ls', iftype: 'uplink'}
  - {name: 'Internal iface', ip: '172.16.1.1', prefix_len: 24, portgroup_id: "{{ gather_moids_pg.object_id }}", iftype: 'uplink'}
  - {name: 'Internal new', ip: '172.16.4.1', prefix_len: 26, logical_switch: 'new_lswitch_name', iftype: 'internal'}
```

##### Routes list
Each route is passed to the module as a dictionary in a list. Each dictionary has the following key / value pairs:
- network:
Mandatory: The target network for the route, e.g. '10.11.12.0/24'
- next_hop:
Mandatory: The next hop IP for the route, e.g. '192.168.178.2'
- admin_distance:
Optional: The admin_distance to be used for this route
- mtu:
Optional: The MTU supported by this route
- description:
Optional: A free text description for the static route

Example:
```yml
routes:
  - {network: '10.11.12.0/24', next_hop: '192.168.178.2', admin_distance: '1', mtu: '1500', description: 'very important route'}
  - {network: '10.11.13.0/24', next_hop: '192.168.178.2', mtu: '1600'}
  - {network: '10.11.14.0/24', next_hop: '192.168.178.2'}
```

### Module `nsx_ospf`
##### enables, updates or deletes OSPF configurations in NSX for ESGs and DLRs

- state:
Optional: present or absent, defaults to present
- edge_name:
Mandatory: The name of the ESG or DLR to be configured for OSPF
- router_id:
Mandatory: The ESG or DLR Router id to be configured, e.g. configured as an IP Address
- graceful_restart:
Optional: true / false, is graceful restart enabled, defaults to true
- default_originate:
Optional: true / false, will the ESG or DLR announce its default route into OSPF, defaults to false
- protocol_address:
Unused for ESG, Mandatory for DLR: The IP address to be used to send OSPF message from
- forwarding_address:
Unused for ESG, Mandatory for DLR: The IP address to be used as the next-hop for the traffic
- logging:
Optional: true / false, will the ESG or DLR log state changes, defaults to false
- log_level:
Optional: Log level for OSPF state changes, choices=['debug', 'info', 'notice', 'warning', 'error', 'critical', 'alert', 'emergency'], defaults to 'info'
- areas:
Optional: A list of Dictionaries with Areas, See the Area details section for more information
- area_map:
Optional: A list of Dictionaries with Area to interface mappings, See the area_map details section for more information

Example:
```yml
  - name: Configure OSPF DLR
    nsx_ospf:
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      state: present
      edge_name: 'ansibleDLR'
      router_id: '172.24.1.3'
      default_originate: True
      graceful_restart: False
      logging: True
      log_level: debug
      forwarding_address: '172.24.1.2'
      protocol_address: '172.24.1.3'
      areas:
        - { area_id: 10 }
      area_map:
        - { area_id: 10, vnic: "{{ dlr_uplink_index }}" }      
    register: ospf_dlr
    tags: ospf_dlr
```

##### Area list
Each Area is defined as a dictionary holding the following Key / Value pairs:

- area_id:
Mandatory: The Area id, e.g. 0
- type:
Optional: The area type, e.g. 'nssa' or 'normal', defaults to 'normal'
- authentication:
Optional: Authentication type, 'none', 'password' or 'md5', defaults to 'none'
- password:
Mandatory for Authentication types 'password' or 'md5', the password or md5 hash used to authenticate

NOTE: When Authentication types are used, the module will always report a change as the password can't be retrieved and check from NSX Manager

Example:
```yml
areas:
  - { area_id: 0 }
  - { area_id: 61 }
  - { area_id: 59, type: 'nssa' }
  - { area_id: 62, type: 'nssa', authentication: 'password', password: 'mysecret' }
```

##### Area mapping list
Each Area / Interface mapping list is holding the following Key / Value pairs:

- area_id:
Mandatory: The Area Id, e.g. 0
- vnic:
Mandatory: The vnic Id to map the Area to, e.g. 0 for vnic0
- ignore_mtu:
Optional: true / false, Ignore MTU mismatches between OSPF interfaces, defaults to false
- hello:
Optional: The Hello Interval, defaults to 10
- dead:
Optional: The dead interval, defaults to 40
- cost:
Optional: The Interface Cost, default to 1
- priority:
Optional: The Interface Priority, defaults to 128

Example:
```yml
area_map:
  - { area_id: 0, vnic: 0, hello: 20}
  - { area_id: 61, vnic: 1, ignore_mtu: True , hello: 15, dead: 60, priority: 128, cost: 1}
```

### Module `nsx_redistribution`
##### enables, updates or deletes routing protocol redistribution in NSX for ESGs and DLRs (OSPF & BGP)

- ospf_state:
Mandatory: true / false, is redistribution enabled for OSPF
- bgp_state:
Mandatory: true / false, is redistribution enabled for BGP
- prefixes:
Optional: A list of dictionaries containing prefixes, See the prefixes details section for more information
- rules:
Optional: A list of dictionaries containing redistribution rules, See the rules details section for more information

Example:
```yml
  - name: Configure OSPF ESG
    nsx_redistribution:
      ospf_state: present
      bgp_state: present
      nsxmanager_spec: "{{ nsxmanager_spec }}"
      edge_name: 'ansibleESG'
      prefixes:
        - {name: 'testprfx1', network: '192.168.179.0/24'}
        - {name: 'testprfx2', network: '10.11.12.0/24'}
      rules:
        - {learner: 'ospf', priority: 0, static: false, connected: true, bgp: false, ospf: false, action: 'permit'}
        - {learner: 'ospf', priority: 1, static: 'true', connected: 'true', bgp: 'false', ospf: 'false', prefix: 'testprfx1', action: 'deny'}
        - {learner: 'bgp', priority: 1, connected: true, prefix: 'testprfx2', action: 'deny'}
        - {learner: 'bgp', priority: 0, connected: true, prefix: 'testprfx1'}
    register: redist
    tags: redist
```

##### Prefixes list
The prefixes variable holds a list of dictionaries with the following Key / Value pairs:

- name:
Mandatory: The name of the prefix list
- network:
Mandatory: The network to match, in the form of '<network>/<prefix_len>', e.g. '192.168.179.0/24'

Example:
```yml
prefixes:
  - {name: 'testprfx1', network: '192.168.179.0/24'}
  - {name: 'testprfx2', network: '10.11.12.0/24'}
```

##### Rules list
The rules variable holds a list of dictionaries with the following Key / Value pairs:

- learner:
Mandatory: The learner protocol, this can be 'bgp' or 'ospf'
- priority:
Mandatory: The priority (order) in which rules are applied, e.g. 0,1,2,3,...
- static:
Optional: true / false, reditribute static routes, defaults to false
- connected:
Optional: true / false, reditribute connected routes, defaults to false
- bgp:
Optional: true / false, reditribute bgp routes, defaults to false
- ospf:
Optional: true / false, reditribute ospf routes, defaults to false
- prefix:
Optional: A prefix list name to use as a filter for the routes
- action:
Optional: The action to apply with this rule, can be 'permit', 'deny', defaults to 'permit'

Example:
```yml
rules:
  - {learner: 'ospf', priority: 0, static: false, connected: true, bgp: false, ospf: false, action: 'permit'}
  - {learner: 'ospf', priority: 1, static: 'true', connected: 'true', bgp: 'false', ospf: 'false', prefix: 'testprfx1', action: 'deny'}
  - {learner: 'bgp', priority: 1, connected: true, prefix: 'testprfx2', action: 'deny'}
  - {learner: 'bgp', priority: 0, connected: true, prefix: 'testprfx1'}
```

## Example Playbooks and roles
### As part of this repo you will find example playbooks and roles:

#### Playbooks
`deployNsx.yml`
This is a playbook that can be used with the ``base-config-nsx`` and ``deploy-nsx-ova`` roles to deploy NSX
in an existing vSphere cluster

#### Roles
`deploy-nsx-ova`: An example role that uses the ``nsx_deploy_ova`` module to deploy NSX Manager into a vSphere Cluster
`base-config-nsx`: An example role that creates all needed NSX Objects, Controllers, VIB and configuration for a base NSX deployment


## License

This project is dual licensed under the BSD 3-clause and GPLv3 licenses.


LICENSE

NSX Ansible

This product is licensed to you under the BSD 3-Clause License (the "License"); you may not use this file except in compliance with the License.

Copyright © 2015-2016 VMware, Inc. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of VMware, Inc. nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


LICENSE

NSX Ansible

Copyright © 2015-2016 VMware, Inc.  All rights reserved.

This product is licensed to you under the GNU General Public License Version 3 (the "License").  You may not use this product except in compliance with the License.

                  GNU GENERAL PUBLIC LICENSE
                   Version 3, 29 June 2007

Copyright © 2007 Free Software Foundation, Inc. <http://fsf.org/>

Everyone is permitted to copy and distribute verbatim copies of this license document, but changing it is not allowed.
Preamble

The GNU General Public License is a free, copyleft license for software and other kinds of works.

The licenses for most software and other practical works are designed to take away your freedom to share and change the works. By contrast, the GNU General Public License is intended to guarantee your freedom to share and change all versions of a program--to make sure it remains free software for all its users. We, the Free Software Foundation, use the GNU General Public License for most of our software; it applies also to any other work released this way by its authors. You can apply it to your programs, too.

When we speak of free software, we are referring to freedom, not price. Our General Public Licenses are designed to make sure that you have the freedom to distribute copies of free software (and charge for them if you wish), that you receive source code or can get it if you want it, that you can change the software or use pieces of it in new free programs, and that you know you can do these things.

To protect your rights, we need to prevent others from denying you these rights or asking you to surrender the rights. Therefore, you have certain responsibilities if you distribute copies of the software, or if you modify it: responsibilities to respect the freedom of others.

For example, if you distribute copies of such a program, whether gratis or for a fee, you must pass on to the recipients the same freedoms that you received. You must make sure that they, too, receive or can get the source code. And you must show them these terms so they know their rights.

Developers that use the GNU GPL protect your rights with two steps: (1) assert copyright on the software, and (2) offer you this License giving you legal permission to copy, distribute and/or modify it.

For the developers' and authors' protection, the GPL clearly explains that there is no warranty for this free software. For both users' and authors' sake, the GPL requires that modified versions be marked as changed, so that their problems will not be attributed erroneously to authors of previous versions.

Some devices are designed to deny users access to install or run modified versions of the software inside them, although the manufacturer can do so. This is fundamentally incompatible with the aim of protecting users' freedom to change the software. The systematic pattern of such abuse occurs in the area of products for individuals to use, which is precisely where it is most unacceptable. Therefore, we have designed this version of the GPL to prohibit the practice for those products. If such problems arise substantially in other domains, we stand ready to extend this provision to those domains in future versions of the GPL, as needed to protect the freedom of users.

Finally, every program is threatened constantly by software patents. States should not allow patents to restrict development and use of software on general-purpose computers, but in those that do, we wish to avoid the special danger that patents applied to a free program could make it effectively proprietary. To prevent this, the GPL assures that patents cannot be used to render the program non-free.
The precise terms and conditions for copying, distribution and modification follow.

TERMS AND CONDITIONS

0. Definitions.

"This License" refers to version 3 of the GNU General Public License.

"Copyright" also means copyright-like laws that apply to other kinds of works, such as semiconductor masks.

"The Program" refers to any copyrightable work licensed under this License. Each licensee is addressed as "you". "Licensees" and "recipients" may be individuals or organizations.

To "modify" a work means to copy from or adapt all or part of the work in a fashion requiring copyright permission, other than the making of an exact copy. The resulting work is called a "modified version" of the earlier work or a work "based on" the earlier work.

A "covered work" means either the unmodified Program or a work based on the Program.

To "propagate" a work means to do anything with it that, without permission, would make you directly or secondarily liable for infringement under applicable copyright law, except executing it on a computer or modifying a private copy. Propagation includes copying, distribution (with or without modification), making available to the public, and in some countries other activities as well.

To "convey" a work means any kind of propagation that enables other parties to make or receive copies. Mere interaction with a user through a computer network, with no transfer of a copy, is not conveying.

An interactive user interface displays "Appropriate Legal Notices" to the extent that it includes a convenient and prominently visible feature that (1) displays an appropriate copyright notice, and (2) tells the user that there is no warranty for the work (except to the extent that warranties are provided), that licensees may convey the work under this License, and how to view a copy of this License. If the interface presents a list of user commands or options, such as a menu, a prominent item in the list meets this criterion.

1. Source Code.

The "source code" for a work means the preferred form of the work for making modifications to it. "Object code" means any non-source form of a work.

A "Standard Interface" means an interface that either is an official standard defined by a recognized standards body, or, in the case of interfaces specified for a particular programming language, one that is widely used among developers working in that language.

The "System Libraries" of an executable work include anything, other than the work as a whole, that (a) is included in the normal form of packaging a Major Component, but which is not part of that Major Component, and (b) serves only to enable use of the work with that Major Component, or to implement a Standard Interface for which an implementation is available to the public in source code form. A "Major Component", in this context, means a major essential component (kernel, window system, and so on) of the specific operating system (if any) on which the executable work runs, or a compiler used to produce the work, or an object code interpreter used to run it.

The "Corresponding Source" for a work in object code form means all the source code needed to generate, install, and (for an executable work) run the object code and to modify the work, including scripts to control those activities. However, it does not include the work's System Libraries, or general-purpose tools or generally available free programs which are used unmodified in performing those activities but which are not part of the work. For example, Corresponding Source includes interface definition files associated with source files for the work, and the source code for shared libraries and dynamically linked subprograms that the work is specifically designed to require, such as by intimate data communication or control flow between those subprograms and other parts of the work.

The Corresponding Source need not include anything that users can regenerate automatically from other parts of the Corresponding Source.
The Corresponding Source for a work in source code form is that same work.

2. Basic Permissions.

All rights granted under this License are granted for the term of copyright on the Program, and are irrevocable provided the stated conditions are met. This License explicitly affirms your unlimited permission to run the unmodified Program. The output from running a covered work is covered by this License only if the output, given its content, constitutes a covered work. This License acknowledges your rights of fair use or other equivalent, as provided by copyright law.

You may make, run and propagate covered works that you do not convey, without conditions so long as your license otherwise remains in force. You may convey covered works to others for the sole purpose of having them make modifications exclusively for you, or provide you with facilities for running those works, provided that you comply with the terms of this License in conveying all material for which you do not control copyright. Those thus making or running the covered works for you must do so exclusively on your behalf, under your direction and control, on terms that prohibit them from making any copies of your copyrighted material outside their relationship with you.

Conveying under any other circumstances is permitted solely under the conditions stated below. Sublicensing is not allowed; section 10 makes it unnecessary.

3. Protecting Users' Legal Rights From Anti-Circumvention Law.

No covered work shall be deemed part of an effective technological measure under any applicable law fulfilling obligations under article 11 of the WIPO copyright treaty adopted on 20 December 1996, or similar laws prohibiting or restricting circumvention of such measures.

When you convey a covered work, you waive any legal power to forbid circumvention of technological measures to the extent such circumvention is effected by exercising rights under this License with respect to the covered work, and you disclaim any intention to limit operation or modification of the work as a means of enforcing, against the work's users, your or third parties' legal rights to forbid circumvention of technological measures.

4. Conveying Verbatim Copies.

You may convey verbatim copies of the Program's source code as you receive it, in any medium, provided that you conspicuously and appropriately publish on each copy an appropriate copyright notice; keep intact all notices stating that this License and any non-permissive terms added in accord with section 7 apply to the code; keep intact all notices of the absence of any warranty; and give all recipients a copy of this License along with the Program.

You may charge any price or no price for each copy that you convey, and you may offer support or warranty protection for a fee.

5. Conveying Modified Source Versions.
You may convey a work based on the Program, or the modifications to produce it from the Program, in the form of source code under the terms of section 4, provided that you also meet all of these conditions:

a) The work must carry prominent notices stating that you modified it, and giving a relevant date.

b) The work must carry prominent notices stating that it is released under this License and any conditions added under section 7. This requirement modifies the requirement in section 4 to "keep intact all notices".

c) You must license the entire work, as a whole, under this License to anyone who comes into possession of a copy.  This License will therefore                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          apply, along with any applicable section 7 additional terms, to the whole of the work, and all its parts, regardless of how they are packaged. This License gives no permission to license the work in any other way, but it does not invalidate such permission if you have separately received it.

d) If the work has interactive user interfaces, each must display Appropriate Legal Notices; however, if the Program has interactive interfaces that do not display Appropriate Legal Notices, your work need not make them do so.

A compilation of a covered work with other separate and independent works, which are not by their nature extensions of the covered work, and which are not combined with it such as to form a larger program, in or on a volume of a storage or distribution medium, is called an "aggregate" if the compilation and its resulting copyright are not used to limit the access or legal rights of the compilation's users beyond what the individual works permit. Inclusion of a covered work in an aggregate does not cause this License to apply to the other parts of the aggregate.

6. Conveying Non-Source Forms.

You may convey a covered work in object code form under the terms of sections 4 and 5, provided that you also convey the machine-readable Corresponding Source under the terms of this License, in one of these ways:

a) Convey the object code in, or embodied in, a physical product (including a physical distribution medium), accompanied by the Corresponding Source fixed on a durable physical medium customarily used for software interchange.

b) Convey the object code in, or embodied in, a physical product (including a physical distribution medium), accompanied by a written offer, valid for at least three years and valid for as long as you offer spare parts or customer support for that product model, to give anyone who possesses the object code either (1) a copy of the Corresponding Source for all the software in the product that is covered by this License, on a durable physical medium customarily used for software interchange, for a price no more than your reasonable cost of physically performing this conveying of source, or (2) access to copy the Corresponding Source from a network server at no charge.

c) Convey individual copies of the object code with a copy of the written offer to provide the Corresponding Source. This alternative is allowed only occasionally and noncommercially, and only if you received the object code with such an offer, in accord with subsection 6b.

d) Convey the object code by offering access from a designated place (gratis or for a charge), and offer equivalent access to the Corresponding Source in the same way through the same place at no further charge. You need not require recipients to copy the Corresponding Source along with the object code. If the place to copy the object code is a network server, the Corresponding Source may be on a different server (operated by you or a third party) that supports equivalent copying facilities, provided you maintain clear directions next to the object code saying where to find the Corresponding Source. Regardless of what server hosts the Corresponding Source, you remain obligated to ensure that it is available for as long as needed to satisfy these requirements.

e) Convey the object code using peer-to-peer transmission, provided you inform other peers where the object code and Corresponding Source of the work are being offered to the general public at no charge under subsection 6d.

A separable portion of the object code, whose source code is excluded from the Corresponding Source as a System Library, need not be included in conveying the object code work.

A "User Product" is either (1) a "consumer product", which means any tangible personal property which is normally used for personal, family, or household purposes, or (2) anything designed or sold for incorporation into a dwelling. In determining whether a product is a consumer product, doubtful cases shall be resolved in favor of coverage. For a particular product received by a particular user, "normally used" refers to a typical or common use of that class of product, regardless of the status of the particular user or of the way in which the particular user actually uses, or expects or is expected to use, the product. A product is a consumer product regardless of whether the product has substantial commercial, industrial or non-consumer uses, unless such uses represent the only significant mode of use of the product.

"Installation Information" for a User Product means any methods, procedures, authorization keys, or other information required to install and execute modified versions of a covered work in that User Product from a modified version of its Corresponding Source. The information must suffice to ensure that the continued functioning of the modified object code is in no case prevented or interfered with solely because modification has been made.

If you convey an object code work under this section in, or with, or specifically for use in, a User Product, and the conveying occurs as part of a transaction in which the right of possession and use of the User Product is transferred to the recipient in perpetuity or for a fixed term (regardless of how the transaction is characterized), the Corresponding Source conveyed under this section must be accompanied by the Installation Information. But this requirement does not apply if neither you nor any third party retains the ability to install modified object code on the User Product (for example, the work has been installed in ROM).

The requirement to provide Installation Information does not include a requirement to continue to provide support service, warranty, or updates for a work that has been modified or installed by the recipient, or for the User Product in which it has been modified or installed. Access to a network may be denied when the modification itself materially and adversely affects the operation of the network or violates the rules and protocols for communication across the network.

Corresponding Source conveyed, and Installation Information provided, in accord with this section must be in a format that is publicly documented (and with an implementation available to the public in source code form), and must require no special password or key for unpacking, reading or copying.

7. Additional Terms.

"Additional permissions" are terms that supplement the terms of this License by making exceptions from one or more of its conditions. Additional permissions that are applicable to the entire Program shall be treated as though they were included in this License, to the extent that they are valid under applicable law. If additional permissions apply only to part of the Program, that part may be used separately under those permissions, but the entire Program remains governed by this License without regard to the additional permissions.

When you convey a copy of a covered work, you may at your option remove any additional permissions from that copy, or from any part of it. (Additional permissions may be written to require their own removal in certain cases when you modify the work.) You may place additional permissions on material, added by you to a covered work, for which you have or can give appropriate copyright permission.

Notwithstanding any other provision of this License, for material you add to a covered work, you may (if authorized by the copyright holders of that material) supplement the terms of this License with terms:

a) Disclaiming warranty or limiting liability differently from the terms of sections 15 and 16 of this License; or

b) Requiring preservation of specified reasonable legal notices or author attributions in that material or in the Appropriate Legal Notices displayed by works containing it; or

c) Prohibiting misrepresentation of the origin of that material, or requiring that modified versions of such material be marked in reasonable ways as different from the original version; or

d) Limiting the use for publicity purposes of names of licensors or authors of the material; or

e) Declining to grant rights under trademark law for use of some trade names, trademarks, or service marks; or

f) Requiring indemnification of licensors and authors of that material by anyone who conveys the material (or modified versions of it) with contractual assumptions of liability to the recipient, for any liability that these contractual assumptions directly impose on those licensors and authors.

All other non-permissive additional terms are considered "further restrictions" within the meaning of section 10. If the Program as you received it, or any part of it, contains a notice stating that it is governed by this License along with a term that is a further restriction, you may remove that term. If a license document contains a further restriction but permits relicensing or conveying under this License, you may add to a covered work material governed by the terms of that license document, provided that the further restriction does not survive such relicensing or conveying.

If you add terms to a covered work in accord with this section, you must place, in the relevant source files, a statement of the additional terms that apply to those files, or a notice indicating where to find the applicable terms.

Additional terms, permissive or non-permissive, may be stated in the form of a separately written license, or stated as exceptions; the above requirements apply either way.

8. Termination.

You may not propagate or modify a covered work except as expressly provided under this License. Any attempt otherwise to propagate or modify it is void, and will automatically terminate your rights under this License (including any patent licenses granted under the third paragraph of section 11).

However, if you cease all violation of this License, then your license from a particular copyright holder is reinstated (a) provisionally, unless and until the copyright holder explicitly and finally terminates your license, and (b) permanently, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation.

Moreover, your license from a particular copyright holder is reinstated permanently if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of this License (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice.

Termination of your rights under this section does not terminate the licenses of parties who have received copies or rights from you under this License. If your rights have been terminated and not permanently reinstated, you do not qualify to receive new licenses for the same material under section 10.

9. Acceptance Not Required for Having Copies.

You are not required to accept this License in order to receive or run a copy of the Program. Ancillary propagation of a covered work occurring solely as a consequence of using peer-to-peer transmission to receive a copy likewise does not require acceptance. However, nothing other than this License grants you permission to propagate or modify any covered work. These actions infringe copyright if you do not accept this License. Therefore, by modifying or propagating a covered work, you indicate your acceptance of this License to do so.

10. Automatic Licensing of Downstream Recipients.

Each time you convey a covered work, the recipient automatically receives a license from the original licensors, to run, modify and propagate that work, subject to this License. You are not responsible for enforcing compliance by third parties with this License.

An "entity transaction" is a transaction transferring control of an organization, or substantially all assets of one, or subdividing an organization, or merging organizations. If propagation of a covered work results from an entity transaction, each party to that transaction who receives a copy of the work also receives whatever licenses to the work the party's predecessor in interest had or could give under the previous paragraph, plus a right to possession of the Corresponding Source of the work from the predecessor in interest, if the predecessor has it or can get it with reasonable efforts.

You may not impose any further restrictions on the exercise of the rights granted or affirmed under this License. For example, you may not impose a license fee, royalty, or other charge for exercise of rights granted under this License, and you may not initiate litigation (including a cross-claim or counterclaim in a lawsuit) alleging that any patent claim is infringed by making, using, selling, offering for sale, or importing the Program or any portion of it.

11. Patents.

A "contributor" is a copyright holder who authorizes use under this License of the Program or a work on which the Program is based. The work thus licensed is called the contributor's "contributor version".

A contributor's "essential patent claims" are all patent claims owned or controlled by the contributor, whether already acquired or hereafter acquired, that would be infringed by some manner, permitted by this License, of making, using, or selling its contributor version, but do not include claims that would be infringed only as a consequence of further modification of the contributor version. For purposes of this definition, "control" includes the right to grant patent sublicenses in a manner consistent with the requirements of this License.

Each contributor grants you a non-exclusive, worldwide, royalty-free patent license under the contributor's essential patent claims, to make, use, sell, offer for sale, import and otherwise run, modify and propagate the contents of its contributor version.

In the following three paragraphs, a "patent license" is any express agreement or commitment, however denominated, not to enforce a patent (such as an express permission to practice a patent or covenant not to sue for patent infringement). To "grant" such a patent license to a party means to make such an agreement or commitment not to enforce a patent against the party.

If you convey a covered work, knowingly relying on a patent license, and the Corresponding Source of the work is not available for anyone to copy, free of charge and under the terms of this License, through a publicly available network server or other readily accessible means, then you must either (1) cause the Corresponding Source to be so available, or (2) arrange to deprive yourself of the benefit of the patent license for this particular work, or (3) arrange, in a manner consistent with the requirements of this License, to extend the patent license to downstream recipients. "Knowingly relying" means you have actual knowledge that, but for the patent license, your conveying the covered work in a country, or your recipient's use of the covered work in a country, would infringe one or more identifiable patents in that country that you have reason to believe are valid.

If, pursuant to or in connection with a single transaction or arrangement, you convey, or propagate by procuring conveyance of, a covered work, and grant a patent license to some of the parties receiving the covered work authorizing them to use, propagate, modify or convey a specific copy of the covered work, then the patent license you grant is automatically extended to all recipients of the covered work and works based on it.

A patent license is "discriminatory" if it does not include within the scope of its coverage, prohibits the exercise of, or is conditioned on the non-exercise of one or more of the rights that are specifically granted under this License. You may not convey a covered work if you are a party to an arrangement with a third party that is in the business of distributing software, under which you make payment to the third party based on the extent of your activity of conveying the work, and under which the third party grants, to any of the parties who would receive the covered work from you, a discriminatory patent license (a) in connection with copies of the covered work conveyed by you (or copies made from those copies), or (b) primarily for and in connection with specific products or compilations that contain the covered work, unless you entered into that arrangement, or that patent license was granted, prior to 28 March 2007.

Nothing in this License shall be construed as excluding or limiting any implied license or other defenses to infringement that may otherwise be available to you under applicable patent law.

12. No Surrender of Others' Freedom.

If conditions are imposed on you (whether by court order, agreement or otherwise) that contradict the conditions of this License, they do not excuse you from the conditions of this License. If you cannot convey a covered work so as to satisfy simultaneously your obligations under this License and any other pertinent obligations, then as a consequence you may not convey it at all. For example, if you agree to terms that obligate you to collect a royalty for further conveying from those to whom you convey the Program, the only way you could satisfy both those terms and this License would be to refrain entirely from conveying the Program.

13. Use with the GNU Affero General Public License.

Notwithstanding any other provision of this License, you have permission to link or combine any covered work with a work licensed under version 3 of the GNU Affero General Public License into a single combined work, and to convey the resulting work. The terms of this License will continue to apply to the part which is the covered work, but the special requirements of the GNU Affero General Public License, section 13, concerning interaction through a network will apply to the combination as such.

14. Revised Versions of this License.

The Free Software Foundation may publish revised and/or new versions of the GNU General Public License from time to time. Such new versions will be similar in spirit to the present version, but may differ in detail to address new problems or concerns.

Each version is given a distinguishing version number. If the Program specifies that a certain numbered version of the GNU General Public License "or any later version" applies to it, you have the option of following the terms and conditions either of that numbered version or of any later version published by the Free Software Foundation. If the Program does not specify a version number of the GNU General Public License, you may choose any version ever published by the Free Software Foundation.

If the Program specifies that a proxy can decide which future versions of the GNU General Public License can be used, that proxy's public statement of acceptance of a version permanently authorizes you to choose that version for the Program.

Later license versions may give you additional or different permissions. However, no additional obligations are imposed on any author or copyright holder as a result of your choosing to follow a later version.

15. Disclaimer of Warranty.

THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW. EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

16. Limitation of Liability.

IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

17. Interpretation of Sections 15 and 16.

If the disclaimer of warranty and limitation of liability provided above cannot be given local legal effect according to their terms, reviewing courts shall apply local law that most closely approximates an absolute waiver of all civil liability in connection with the Program, unless a warranty or assumption of liability accompanies a copy of the Program in return for a fee.

END OF TERMS AND CONDITIONS
