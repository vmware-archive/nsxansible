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


def get_segment_id_pools(session):
    id_pools = session.read('vdnSegmentPools')['body']
    return id_pools['segmentRanges']


def get_mcast_pool(session):
    mcastpool = session.read('vdnMulticastPools')['body']
    return mcastpool['multicastRanges']


def create_segment_id_pool(session, start, end):
    segments_create_body = session.extract_resource_body_schema('vdnSegmentPools', 'create')
    segments_create_body['segmentRange']['begin'] = start
    segments_create_body['segmentRange']['end'] = end
    segments_create_body['segmentRange']['name'] = 'createdByAnsible'
    return session.create('vdnSegmentPools', request_body_dict=segments_create_body)['status']


def create_mcast_pool(session, start, end):
    mcastpool_create_body = session.extract_resource_body_schema('vdnMulticastPools', 'create')
    mcastpool_create_body['multicastRange']['begin'] = start
    mcastpool_create_body['multicastRange']['end'] = end
    mcastpool_create_body['multicastRange']['name'] = 'createdByAnsible'
    return session.create('vdnMulticastPools', request_body_dict=mcastpool_create_body)


def update_segment_id_pool(session, pool_id, end):
    id_pool_body = session.extract_resource_body_schema('vdnSegmentPool', 'update')
    id_pool_body['segmentRange']['end'] = end
    id_pool_body['segmentRange']['name'] = 'createdByAnsible'
    return session.update('vdnSegmentPool', uri_parameters={'segmentPoolId': pool_id},
                          request_body_dict=id_pool_body)


def update_mcast_pool(session, mcast_pool_id, end):
    mcast_pool_body = session.extract_resource_body_schema('vdnMulticastPool', 'update')
    mcast_pool_body['multicastRange']['end'] = end
    mcast_pool_body['multicastRange']['name'] = 'createdByAnsible'
    return session.update('vdnMulticastPool',
                          uri_parameters={'multicastAddresssRangeId': mcast_pool_id},
                          request_body_dict=mcast_pool_body)


def delete_segment_id_pool(session, segment_pool_id):
    return session.delete('vdnSegmentPool', uri_parameters={'segmentPoolId': segment_pool_id})['status']


def delete_mcast_pool(session, mcast_pool_id):
    return session.delete('vdnMulticastPool', uri_parameters={'multicastAddresssRangeId': mcast_pool_id})['status']


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True),
            idpoolstart=dict(default=5000),
            idpoolend=dict(default=15000),
            mcast_enabled=dict(type='bool', default=False),
            mcastpoolstart=dict(default='239.0.0.0'),
            mcastpoolend=dict(default='239.255.255.255')
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient

    s = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                  module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'])

    id_pool_changed = False
    mcast_pool_changed = False

    id_pool = get_segment_id_pools(s)
    mcast_pool = get_mcast_pool(s)

    if id_pool and module.params['state'] == 'absent':
        delete_segment_id_pool(s, id_pool['segmentRange']['id'])
        id_pool_changed = True

    if mcast_pool and module.params['state'] == 'absent':
        delete_mcast_pool(s, mcast_pool['multicastRange']['id'])
        mcast_pool_changed = True

    if id_pool_changed:
        module.exit_json(changed=True)

    if mcast_pool and not module.params['mcast_enabled']:
        delete_mcast_pool(s, mcast_pool['multicastRange']['id'])
        mcast_pool_changed = True

    if not id_pool and module.params['state'] == 'present':
        create_segment_id_pool(s, module.params['idpoolstart'], module.params['idpoolend'])
        id_pool_changed = True

    if not mcast_pool and module.params['mcast_enabled'] and module.params['state'] == 'present':
        create_mcast_pool(s, module.params['mcastpoolstart'], module.params['mcastpoolend'])
        mcast_pool_changed = True

    if id_pool:
        if id_pool['segmentRange']['end'] != str(module.params['idpoolend']):
            update_segment_id_pool(s, id_pool['segmentRange']['id'], module.params['idpoolend'])
            id_pool_changed = True

    if mcast_pool:
        if mcast_pool['multicastRange']['end'] != str(module.params['mcastpoolend']):
            update_mcast_pool(s, mcast_pool['multicastRange']['id'], module.params['mcastpoolend'])
            mcast_pool_changed = True

    if id_pool_changed or mcast_pool_changed:
        module.exit_json(changed=True)
    else:
        module.exit_json(changed=False)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
