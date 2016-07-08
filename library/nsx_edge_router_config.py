#!/usr/bin/env python
# coding=utf-8
#
# Copyright � 2015 VMware, Inc. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
# to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions
# of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

def config_routing(session, module, edge_id):

    edge_routing_config_body = session.read('routingConfig', uri_parameters={'edgeId': edge_id})['body']

    edge_routing_config_body['routing']['routingGlobalConfig']['routerId']= module.params['router_id']
    edge_routing_config_body['routing']['routingGlobalConfig']['ecmp']= 'true'

    int_vnic_index = get_vnic_index(session, edge_id, module.params['internal_vnic_name'])
    uplink_vnic_index = get_vnic_index(session, edge_id, module.params['uplink_vnic_name'])

    new_areas = [{'areaId':0, 'type':'normal'},
                 {'areaId':1,'type':'normal'}]

    interface = [ {'vnic':int_vnic_index, 'areaId':0},
                  {'vnic':uplink_vnic_index, 'areaId':1}]

    edge_routing_config_body['routing']['ospf'] = {'enabled': 'true',
                                                   'ospfAreas': {'ospfArea': new_areas},
                                                   'ospfInterfaces': {'ospfInterface': interface},
                                                   'redistribution': {'enabled': 'true'}}

    return session.update('routingConfig', uri_parameters={'edgeId': edge_id},
                           request_body_dict=edge_routing_config_body)


def get_edge(client_session, edge_name):
    """
    :param client_session: An instance of an NsxClient Session
    :param edge_name: The name of the edge searched
    :return: A tuple, with the first item being the edge or dlr id as string of the first Scope found with the
             right name and the second item being a dictionary of the logical parameters as return by the NSX API
    """
    all_edge = client_session.read_all_pages('nsxEdges', 'read')

    try:
        edge_params = [scope for scope in all_edge if scope['name'] == edge_name][0]
        edge_id = edge_params['objectId']
    except IndexError:
        return None, None

    return edge_id, edge_params

def get_vnic_index(session, edge_id, vnic_name):
    '''Get vnic index for ospf interface mapping'''
    vnics=session.read('vnics',uri_parameters={'edgeId': edge_id})['body']['vnics']['vnic']
    try:
        vnic_index = [vnic_info['index'] for vnic_info in vnics if vnic_info['name'] == vnic_name][0]
    except IndexError:
        return None

    return vnic_index

def disable_firewall(session, edge_id):
    '''Disable firewall'''
    disable_firewall_body = session.extract_resource_body_example('nsxEdgeFirewallConfig', 'update')
    disable_firewall_body['firewall']['enabled']='false'

    del disable_firewall_body['firewall']['defaultPolicy']
    del disable_firewall_body['firewall']['globalConfig']
    del disable_firewall_body['firewall']['rules']

    return session.update('nsxEdgeFirewallConfig',
                          uri_parameters={'edgeId': edge_id},
                          request_body_dict=disable_firewall_body)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            esg_name=dict(required=True),
            router_id=dict(required=True),
            internal_vnic_name=dict(required=True),
            uplink_vnic_name=dict(required=True),
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    client_session=NsxClient(module.params['nsxmanager_spec']['raml_file'],
                             module.params['nsxmanager_spec']['host'],
                             module.params['nsxmanager_spec']['user'],
                             module.params['nsxmanager_spec']['password'])

    edge_id, edge_params = get_edge(client_session, module.params['esg_name'])

    disable_firewall(client_session, edge_id)
    edge_response=config_routing(client_session, module, edge_id)

    module.exit_json(changed=True, edge_response=edge_response)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
