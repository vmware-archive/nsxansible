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
module: nsx_edge_router_facts
short_description: Gather fact aabout edge see
description: This module gather nsx edge information from the api. See: https://vdc-repo.vmware.com/raw.githubusercontent.com/vmware/nsxraml/6.4/html-version/nsxvapi.html#4_0_edges_get
version_added: ""
author: Damien Hauser
options:
    nsxmanager_spec:
        description: a dict with the nsx manager spec see: https://github.com/vmware/nsxansible
        required: true
        type: dict
'''

EXAMPLES = '''
- name: Gather nsx edge facts
  nsx_edge_ipsec:
    nsxmanager_spec: "{{ nsxmanager_spec }}"

'''

RETURN = '''# '''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            nsxmanager_spec=dict(required=True, no_log=False, type='dict')
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    import json

    client_session = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'], debug=False)

    response = client_session.read('nsxEdges')
    edge_facts = response["body"]["pagedEdgeList"]["edgePage"]["edgeSummary"]

    if str(response["status"]) == '200': 

        module.exit_json(changed=False, edge_facts=edge_facts)
    else:
        module.fail_json(msg='You requested this to fail')


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
