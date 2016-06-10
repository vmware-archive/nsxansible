#!/usr/bin/env python
# coding=utf-8
#
# Copyright © 2015 VMware, Inc. All Rights Reserved.
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


def get_ippool_id(session, searched_pool_name):
    try:
        ip_pools = session.read('ipPools',
                                uri_parameters={'scopeId':
                                                'globalroot-0'})['body']['ipamAddressPools']['ipamAddressPool']
    except TypeError:
        return None

    if type(ip_pools) is dict:
        if ip_pools['name'] == searched_pool_name:
            return ip_pools['objectId']
    elif type(ip_pools) is list:
        try:
            return [ip_pool['objectId'] for ip_pool in ip_pools if ip_pool['name'] == searched_pool_name][0]
        except IndexError:
            return None


def get_ippool_details(session, pool_object_id):
    return session.read('ipPool', uri_parameters={'poolId': pool_object_id})['body']


def create_ip_pool(session, body_dict):
    return session.create('ipPools', uri_parameters={'scopeId': 'globalroot-0'}, request_body_dict=body_dict)


def delete_ip_pool(session, pool_object_id):
    return session.delete('ipPool', uri_parameters={'poolId': pool_object_id})


def update_ippool(session, pool_object_id, body_dict):
    return session.update('ipPool', uri_parameters={'poolId': pool_object_id}, request_body_dict=body_dict)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True),
            name=dict(required=True),
            start_ip=dict(required=True),
            end_ip=dict(required=True),
            prefix_length=dict(required=True),
            gateway=dict(),
            dns_server_1=dict(),
            dns_server_2=dict()
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient

    s = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                  module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'])

    ip_pool_objectid = get_ippool_id(s, module.params['name'])

    if not ip_pool_objectid and module.params['state'] == 'present':
        new_ip_pool = s.extract_resource_body_example('ipPools', 'create')
        new_ip_pool['ipamAddressPool']['ipRanges']['ipRangeDto']['startAddress'] = module.params['start_ip']
        new_ip_pool['ipamAddressPool']['ipRanges']['ipRangeDto']['endAddress'] = module.params['end_ip']
        new_ip_pool['ipamAddressPool']['gateway'] = module.params['gateway']
        new_ip_pool['ipamAddressPool']['prefixLength'] = module.params['prefix_length']
        new_ip_pool['ipamAddressPool']['dnsServer1'] = module.params['dns_server_1']
        new_ip_pool['ipamAddressPool']['dnsServer2'] = module.params['dns_server_2']
        new_ip_pool['ipamAddressPool']['name'] = module.params['name']

        create_response = create_ip_pool(s, new_ip_pool)
        module.exit_json(changed=True, argument_spec=module.params, create_response=create_response,
                         ippool_id=create_response['objectId'])

    elif module.params['state'] == 'absent':
        if ip_pool_objectid:
            delete_response = delete_ip_pool(s, ip_pool_objectid)
            module.exit_json(changed=True, argument_spec=module.params, delete_response=delete_response)
        else:
            module.exit_json(changed=False, argument_spec=module.params)

    ippool_config = get_ippool_details(s, ip_pool_objectid)
    change_required = False

    for ippool_detail_key, ippool_detail_value in ippool_config['ipamAddressPool'].iteritems():
        if ippool_detail_key == 'ipRanges':
            for range_detail_key, range_detail_value in \
                    ippool_config['ipamAddressPool']['ipRanges']['ipRangeDto'].iteritems():
                if range_detail_key == 'startAddress' and range_detail_value != module.params['start_ip']:
                    ippool_config['ipamAddressPool']['ipRanges']['ipRangeDto']['startAddress'] = \
                        module.params['start_ip']
                    change_required = True
                elif range_detail_key == 'endAddress' and range_detail_value != module.params['end_ip']:
                    ippool_config['ipamAddressPool']['ipRanges']['ipRangeDto']['endAddress'] = \
                        module.params['end_ip']
                    change_required = True
        elif ippool_detail_key == 'gateway' and ippool_detail_value != module.params['gateway']:
            ippool_config['ipamAddressPool']['gateway'] = module.params['gateway']
            change_required = True
        elif ippool_detail_key == 'prefixLength' and ippool_detail_value != module.params['prefix_length']:
            ippool_config['ipamAddressPool']['prefixLength'] = module.params['prefix_length']
            change_required = True
        elif ippool_detail_key == 'name' and ippool_detail_value != module.params['name']:
            ippool_config['ipamAddressPool']['name'] = module.params['name']
            change_required = True
        elif ippool_detail_key == 'dnsServer1' and ippool_detail_value != module.params['dns_server_1']:
            ippool_config['ipamAddressPool']['dnsServer1'] = module.params['dns_server_1']
            change_required = True
        elif ippool_detail_key == 'dnsServer2' and ippool_detail_value != module.params['dns_server_2']:
            ippool_config['ipamAddressPool']['dnsServer2'] = module.params['dns_server_2']
            change_required = True
    if change_required:
        revision = int(ippool_config['ipamAddressPool']['revision'])
        revision += 1
        ippool_config['ipamAddressPool']['revision'] = str(revision)
        updateippool_response = update_ippool(s, ip_pool_objectid, ippool_config)
        module.exit_json(changed=True, argument_spec=module.params, update_response=updateippool_response,
                         ippool_id=ip_pool_objectid)
    else:
        module.exit_json(changed=False, argument_spec=module.params, ippool_config=ippool_config,
                         ippool_id=ip_pool_objectid)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
