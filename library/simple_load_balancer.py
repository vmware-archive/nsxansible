#!/usr/bin/env python
# coding=utf-8
#
# Copyright ï¿½ 2015 VMware, Inc. All Rights Reserved.
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

def lb_config(client_session, module, edge_id):
#    lb_config_body = client_session.extract_resource_body_schema('loadBalancer', 'update')
    lb_config_body = client_session.extract_resource_body_example('loadBalancer', 'update')
    lb_config_body['loadBalancer']['enabled']='true'

    #certificate_id = get_certificate_id(client_session, edge_id)
    app_profiles=[{'applicationProfileId': 'applicationProfile-1',
                   'name': module.params['app_profile_name_http'], 'insertXForwardedFor': 'false',
                   'sslPassthrough':'false', 'template':'HTTP',
                   }
#                  {'applicationProfileId': 'applicationProfile-2',
#                   'name': module.params['app_profile_name_https'], 'insertXForwardedFor': 'false',
#                   'sslPassthrough':'false', 'template':'HTTPS',
#                   'sslPassthrough': 'true'},
#                  {'applicationProfileId': 'applicationProfile-3',
#                   'name': module.params['app_profile_name_tcp'], 'insertXForwardedFor': 'false',
#                   'sslPassthrough':'false','template':'TCP',
#                   'serverSslEnabled':'false'}
                 ]

    lb_config_body['loadBalancer']['applicationProfile'] = app_profiles
    lb_config_body['loadBalancer']['monitor'] = {'name': module.params['monitor_name'],
                                        'type': module.params['monitor_type'],
                                        'interval': module.params['monitor_interval'],
                                         'timeout': module.params['monitor_time_out'],
                                         'maxRetries': module.params['monitor_retries'],
                                         'method': module.params['monitor_url_method'],
                                         'url': module.params['monitor_url']}

    del lb_config_body['loadBalancer']['applicationRule']
    del lb_config_body['loadBalancer']['virtualServer']
    del lb_config_body['loadBalancer']['pool']
    return client_session.update('loadBalancer', uri_parameters={'edgeId': edge_id},
                         request_body_dict=lb_config_body)

def get_monitor_id(client_session, monitor_name, edge_id):
    monitor_res = client_session.read('lbMonitors', uri_parameters={'edgeId': edge_id})['body']['loadBalancer']['monitor']
    if isinstance(monitor_res, list):
        try:
            monitor_id = [monitor_info['monitorId'] for monitor_info in monitor_res if monitor_info['name'] == 'tcp_monitor']
        except IndexError:
            return None
    else:
        if monitor_res['name'] == monitor_name:
            monitor_id = monitor_res['monitorId']
    return monitor_id

def get_application_rule_id(client_session, app_rule_name, edge_id):
    app_rules_res = client_session.read('appRules', uri_parameters={'edgeId': edge_id})['body']['loadBalancer']['applicationRule']
    try:
        app_rule_id = [app_rule_info['applicationRuleId'] for app_rule_info in app_rules_res if app_rule_info['name'] == app_rule_name][0]
    except IndexError:
        return None
    return app_rule_id

def get_application_profile_id(client_session, profile_type, edge_id):
#    app_profiles_res = client_session.read('applicationProfiles', uri_parameters={'edgeId': edge_id})['body']['loadBalancer']['applicationProfile']
    app_profiles_list = client_session.read('applicationProfiles', uri_parameters={'edgeId': edge_id})['body']['loadBalancer']
    app_profiles_res = app_profiles_list['applicationProfile']
    try:
      if len(app_profiles_list) == 1 and app_profiles_res['template'] == profile_type:
        app_profile_id = app_profiles_res['applicationProfileId'] 
        return app_profile_id
      elif len(app_profiles_list) > 1:
        app_profile_id = [app_profile_info['applicationProfileId'] for app_profile_info in app_profiles_res if app_profile_info['template'] == profile_type][0]
        return app_profile_id
      else:
        return None
    except IndexError:
        return None

def get_pool_id(client_session, pool_name, edge_id):
    pools_list = client_session.read('pools', uri_parameters={'edgeId': edge_id})['body']['loadBalancer']
    pools_res = pools_list['pool']
    try:
      if len(pools_list) == 1 and pools_res['name'] == pool_name:
        pool_id = pools_res['poolId']
        return pool_id
      elif len(pools_list) > 1:
        pool_id = [pool_info['poolId'] for pool_info in pools_res if pool_info['name'] == pool_name][0]
        return pool_id
      else:
        return None
    except IndexError:
        return None

def add_virtual_servers(client_session, module, edge_id):
#    virtual_server_config_body = client_session.extract_resource_body_schema('virtualServers', 'create')
    virtual_server_config_body = client_session.extract_resource_body_example('virtualServers', 'create')

#    https_app_profile_id= get_application_profile_id(client_session, 'HTTPS', edge_id)
    http_app_profile_id= get_application_profile_id(client_session, 'HTTP', edge_id)

#    https_pool_id = get_pool_id(client_session,
#                               module.params['https_pool_name'], edge_id)
    http_pool_id = get_pool_id(client_session,
                              module.params['http_pool_name'], edge_id)

    #http_app_rule_id = get_application_rule_id(client_session,
    #                                module.params['app_rule_name_http'], edge_id)
    #tcp_app_rule_id = get_application_rule_id(client_session,
    #                                module.params['app_rule_name_tcp'], edge_id)

    virtual_servers=[{'applicationProfileId': http_app_profile_id,
                      'name': module.params['http_virtual_server_name'], 'enabled':'true',
                      'ipAddress': module.params['virtual_ip_address'], 'protocol':'http',
                      'port': module.params['http_virtual_server_port'],
                      'defaultPoolId': http_pool_id}
#                     {'applicationProfileId': https_app_profile_id,
#                      'name': module.params['https_virtual_server_name'],'enabled':'true',
#                      'ipAddress': module.params['virtual_ip_address'], 'protocol':'https',
#                      'port': module.params['https_virtual_server_port'], 
#                      'defaultPoolId': https_pool_id}
                    ]

    for virtual_server_info in virtual_servers:
        virtual_server_config_body['virtualServer'] = virtual_server_info
        virtual_servers_res = client_session.create('virtualServers',
                                uri_parameters={'edgeId': edge_id},
                         request_body_dict=virtual_server_config_body)
    return virtual_servers_res

def add_pools(client_session, module, edge_id):
    '''Function to add pools for load balancer
    inputs:
        client_session: client session of NSX
            type: object
        edge_id: NSX edge id
            type: string
    '''
#    pool_config_body = client_session.extract_resource_body_schema('pools', 'create')
    pool_config_body = client_session.extract_resource_body_example('pools', 'create')
    # Get monitor id
    monitor_id = get_monitor_id(client_session, module.params['monitor_name'], edge_id)
    pools_dict = [{'name': module.params['http_pool_name'], 'algorithm':'round-robin',
                   'transparent':'false', 'monitorId':monitor_id,
                    'member': [{'name': module.params['http_pool_first_member_name'],
                               'ipAddress': module.params['http_pool_first_member_ip'],
                               'port': module.params['http_pool_first_member_port'],
                               'monitorPort': module.params['http_pool_first_member_monitor_port']},
                               {'name': module.params['http_pool_second_member_name'],
                               'ipAddress': module.params['http_pool_second_member_ip'],
                               'port': module.params['http_pool_second_member_port'],
                               'monitorPort': module.params['http_pool_second_member_monitor_port']}
                               ]}
#            {'name': module.params['https_pool_name'], 'algorithm':'round-robin',
#             'transparent':'false', 'monitorId':monitor_id,
#              'member': [{'name': module.params['https_pool_first_member_name'],
#                       'ipAddress': module.params['https_pool_first_member_ip'],
#                       'port': module.params['https_pool_first_member_port'],
#                       'monitorPort': module.params['https_pool_first_member_monitor_port']},
#                       {'name': module.params['https_pool_second_member_name'],
#                       'ipAddress': module.params['https_pool_second_member_ip'],
#                       'port': module.params['https_pool_second_member_port'],
#                       'monitorPort': module.params['https_pool_second_member_monitor_port']}
#                               ]}
                   ]

    for pool_info in pools_dict:
        pool_config_body['pool'] = pool_info
        add_pools_res = client_session.create('pools', uri_parameters={'edgeId': edge_id},
                         request_body_dict=pool_config_body)
    return add_pools_res

def get_edge_id(session, edge_name):
    router_res = session.read('nsxEdges', 'read')['body']
    edge_summary_list = router_res['pagedEdgeList']['edgePage']['edgeSummary']
    if isinstance(edge_summary_list, list):
        for edge_summary in edge_summary_list:
            if edge_name.lower() in edge_summary['name'].lower():
                edge_id = edge_summary['objectId']
                return edge_id
    else:
        edge_id = router_res['pagedEdgeList']['edgePage']['edgeSummary']['objectId']
        return edge_id


def disable_firewall(session, edge_id):
    '''Disable firewall'''
#    disable_firewall_body = session.extract_resource_body_schema('nsxEdgeFirewallConfig', 'update')
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
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            nsx_edge_gateway_name=dict(required=True),

#            app_profile_name_https=dict(required=True),
            app_profile_name_http=dict(required=True),
#            app_profile_name_tcp=dict(required=True),

            monitor_name=dict(required=True),
            monitor_type=dict(required=True),
            monitor_interval=dict(required=True),
            monitor_time_out=dict(required=True),
            monitor_retries=dict(required=True),
            monitor_url_method=dict(required=True),
            monitor_url=dict(required=True),

            http_pool_name=dict(required=True),
            http_pool_first_member_name=dict(required=True),
            http_pool_first_member_ip=dict(required=True),
            http_pool_first_member_port=dict(required=True),
            http_pool_first_member_monitor_port=dict(required=True),

            http_pool_second_member_name=dict(required=True),
            http_pool_second_member_ip=dict(required=True),
            http_pool_second_member_port=dict(required=True),
            http_pool_second_member_monitor_port=dict(required=True),

#            https_pool_name=dict(required=True),
#            https_pool_first_member_name=dict(required=True),
#            https_pool_first_member_ip=dict(required=True),
#            https_pool_first_member_port=dict(required=True),
#            https_pool_first_member_monitor_port=dict(required=True),
#
#            https_pool_second_member_name=dict(required=True),
#            https_pool_second_member_ip=dict(required=True),
#            https_pool_second_member_port=dict(required=True),
#            https_pool_second_member_monitor_port=dict(required=True),

            http_virtual_server_name=dict(required=True),
            virtual_ip_address=dict(required=True),
            http_virtual_server_port=dict(required=True),

#            https_virtual_server_name=dict(required=True),
#            https_virtual_server_port=dict(required=True),
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    client_session=NsxClient(module.params['nsxmanager_spec']['raml_file'],
                             module.params['nsxmanager_spec']['host'],
                             module.params['nsxmanager_spec']['user'],
                             module.params['nsxmanager_spec']['password'])

    edge_id = get_edge_id(client_session, module.params['nsx_edge_gateway_name'])
    disable=disable_firewall(client_session, edge_id)
    loadBalancer_config = lb_config(client_session, module, edge_id)
    update_pool_res = add_pools(client_session, module, edge_id)
    virtual_servers = add_virtual_servers(client_session, module, edge_id)

    module.exit_json(changed=True, argument_spec=module.params['state'], virtual_servers=virtual_servers)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
