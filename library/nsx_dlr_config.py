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


def get_interfaces(session, interface_name, ldr_id):
    '''Get vnic index connected to uplink switch
    '''
    interfaces=session.read('interfaces',
            uri_parameters={'edgeId': ldr_id})['body']['interfaces']['interface']
    try:
        vnic_index = [interface['index'] for interface in interfaces if interface['name'] == interface_name][0]
    except IndexError:
        return None

    return vnic_index


def config_routing(session, module, ldr_id):
    ldr_routing_config_body = session.read('routingConfig', uri_parameters={'edgeId': ldr_id})['body']

    # Global configuration
    ldr_routing_config_body['routing']['routingGlobalConfig']['routerId']= module.params['dlr_router_id']
    ldr_routing_config_body['routing']['routingGlobalConfig']['ecmp']= 'true'

    vnic_index = get_interfaces(session, module.params['uplink_interface_name'], ldr_id)

    if not vnic_index:
        module.fail_json(msg='Uplink interface not found')

    ldr_routing_config_body['routing']['ospf']['enabled'] = 'true'
    ldr_routing_config_body['routing']['ospf']['ospfAreas'] = {'ospfArea': {'areaId': 0, 'type': 'normal'}}

    ldr_routing_config_body['routing']['ospf']['ospfInterfaces'] = {'ospfInterface': {'vnic': vnic_index, 'areaId': 0}}

    ldr_routing_config_body['routing']['ospf']['protocolAddress'] = module.params['protocol_address']
    ldr_routing_config_body['routing']['ospf']['forwardingAddress'] = module.params['forwarding_address']
    ldr_routing_config_body['routing']['ospf']['redistribution']['enabled'] = 'true'

    return session.update('routingConfig', uri_parameters={'edgeId': ldr_id},
                           request_body_dict=ldr_routing_config_body)


def get_ldr_id(session, ldr_name):
    router_res = session.read('nsxEdges', 'read')['body']
    edge_summary_list = router_res['pagedEdgeList']['edgePage']['edgeSummary']
    if isinstance(edge_summary_list, list):
        for edge_summary in edge_summary_list:
            if ldr_name.lower() in edge_summary['name'].lower():
                edge_id = edge_summary['objectId']
                return edge_id
    else:
        edge_id = router_res['pagedEdgeList']['edgePage']['edgeSummary']['objectId']
        return edge_id


def disable_firewall(session, ldr_id):
    '''Disable firewall'''
    disable_firewall_body = session.extract_resource_body_example('nsxEdgeFirewallConfig', 'update')
    disable_firewall_body['firewall']['enabled']='false'

    del disable_firewall_body['firewall']['defaultPolicy']
    del disable_firewall_body['firewall']['globalConfig']
    del disable_firewall_body['firewall']['rules']

    return session.update('nsxEdgeFirewallConfig',
                          uri_parameters={'edgeId': ldr_id},
                          request_body_dict=disable_firewall_body)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            dlr_router_name=dict(required=True),
            dlr_router_id=dict(required=True),
            uplink_interface_name=dict(required=True),
            protocol_address=dict(required=True),
            forwarding_address=dict(required=True),
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    client_session=NsxClient(module.params['nsxmanager_spec']['raml_file'],
                             module.params['nsxmanager_spec']['host'],
                             module.params['nsxmanager_spec']['user'],
                             module.params['nsxmanager_spec']['password'])

    ldr_id=get_ldr_id(client_session, module.params['dlr_router_name'])
    ldr_response=config_routing(client_session, module, ldr_id)
    module.exit_json(changed=True, ldr_response=ldr_response)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
