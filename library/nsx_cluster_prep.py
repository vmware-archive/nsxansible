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


def get_cluster_status(session, cluster_moid):
    cluster_status = session.read('nwfabricStatus', query_parameters_dict={'resource': cluster_moid})['body']
    for feature_status in cluster_status['resourceStatuses']['resourceStatus']['nwFabricFeatureStatus']:
        if feature_status['featureId'] == 'com.vmware.vshield.vsm.nwfabric.hostPrep':
            return feature_status['status']
    else:
        return 'UNKNOWN'


def cluster_prep(session, cluster_moid):
    cluster_prep_body = session.extract_resource_body_schema('nwfabricConfig', 'create')
    cluster_prep_body['nwFabricFeatureConfig']['resourceConfig']['resourceId'] = cluster_moid
    return session.create('nwfabricConfig', request_body_dict=cluster_prep_body)


def cluster_unprep(session, cluster_moid):
    cluster_prep_body = session.extract_resource_body_schema('nwfabricConfig', 'delete')
    cluster_prep_body['nwFabricFeatureConfig']['resourceConfig']['resourceId'] = cluster_moid
    return session.delete('nwfabricConfig', request_body_dict=cluster_prep_body)


def wait_for_status(session, cluster_moid, completion_status):
    status_poll_count = 0
    while status_poll_count < 20:
        status = get_cluster_status(session, cluster_moid)
        if status == completion_status:
            return True
        else:
            time.sleep(30)
            status_poll_count += 1

    return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True),
            cluster_moid=dict(required=True)
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient

    s = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                  module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'])

    cluster_status = get_cluster_status(s, module.params['cluster_moid'])

    if cluster_status == 'GREEN' and module.params['state'] == 'absent':
        unprep_response = cluster_unprep(s, module.params['cluster_moid'])
        module.exit_json(changed=True, unprep_response=unprep_response)

    if cluster_status == 'RED' or cluster_status == 'YELLOW' and module.params['state'] == 'present':
        module.fail_json(msg='Cluster is in {} status, please check manually'.format(cluster_status),
                         cluster_status=cluster_status)

    if cluster_status != 'GREEN' and module.params['state'] == 'present':
        prep_response = cluster_prep(s, module.params['cluster_moid'])
        prep_status = wait_for_status(s, module.params['cluster_moid'], completion_status='GREEN')
        if not prep_status:
            module.fail_json(msg='Timeout waiting for Cluster Prep to go GREEN', prep_response=prep_response)
        else:
            module.exit_json(changed=True, prep_response=prep_response)

    module.exit_json(changed=False, cluster_status=cluster_status)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
