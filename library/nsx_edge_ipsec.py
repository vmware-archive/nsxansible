#!/usr/bin/env python
# coding=utf-8
#
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: nsx_edge_ipsec
short_description: Create a nsx edge ipsec site to site config
description: This module create a nsx-v edge site so site ipsec config by using the nsxramlclient
version_added: ""
author: Damien Hauser
options:
    nsxmanager_spec:
        description: a dict with the nsx manager spec see: https://github.com/vmware/nsxansible
        required: true
        type: dict
    state:
        description: state should be present or absent
        required: true
        type: str
    edge_id:
        description: the moid of the nsx edge
        required: true
        type: str
    ipsec_config_spec:
        description: the ispec config, see  https://github.com/vmware/nsxansible
        required: true
        type: dict
'''

EXAMPLES = '''
- name: test
  nsx_edge_ipsec:
    nsxmanager_spec: "{{ nsxmanager_spec }}"
    state: "present
    "
    edge_id: "edge-9"
    ipsec_config_spec:
      ipsec:
        enabled: 'true'
        sites:
          site:
          - name: test1
            psk: xxxxxxxxxxxxxxxxxx
            localId: 10.114.209.94
            enablePfs: 'true'
            authenticationMode: psk
            localIp: 10.114.209.94
            dhGroup: dh14
            description: test
            peerIp: 2.2.2.1
            peerSubnets:
              subnet: 10.20.1.0/24
            encryptionAlgorithm: aes
            enabled: 'true'
            peerId: 2.2.2.1
            localSubnets:
              subnet: 10.10.1.0/24
          - name: test2
            psk: xxxxxxxxxxxxxxxxxx
            localId: 10.114.209.94
            enablePfs: 'true'
            authenticationMode: psk
            localIp: 10.114.209.94
            dhGroup: dh14
            description: test
            peerIp: 2.2.2.2
            peerSubnets:
              subnet: 10.20.2.0/24
            encryptionAlgorithm: aes
            enabled: 'true'
            peerId: 2.2.2.2
            localSubnets:
              subnet: 10.10.2.0/24
'''

RETURN = '''# '''

def create_ipsec_config(session, edge_id, body_dict):
    return session.update('ipsecConfig', uri_parameters={'edgeId': edge_id}, request_body_dict=body_dict)

def delete_ipsec_config(session, edge_id):
    return session.delete('ipsecConfig', uri_parameters={'edgeId': edge_id})

def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            ipsec_config_spec=dict(required=True, type='dict'),
            edge_id=dict(required=True)
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient

    client_session = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                  module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'], debug=False)
   
    if module.params['state'] == 'present':
        create_response = create_ipsec_config(client_session, module.params['edge_id'], module.params['ipsec_config_spec'])
        if str(create_response["status"]) == '204': 
            module.exit_json(changed=True, argument_spec=module.params, create_response=create_response,
                         status=create_response["status"])
        else:
            module.fail_json(msg='You requested this to fail')

    elif module.params['state'] == 'absent':
        create_response = delete_ipsec_config(client_session, module.params['edge_id'])
        if str(create_response["status"]) == '204': 
            module.exit_json(changed=True, argument_spec=module.params, create_response=create_response,
                         status=create_response["status"])
        else:
            module.fail_json(msg='You requested this to fail')

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
