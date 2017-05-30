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
        if feature_status['featureId'] == 'com.vmware.vshield.vsm.vxlan':
            return feature_status['status']
    else:
        return 'UNKNOWN'


def vxlan_prep(session, cluster_moid, dvs_moid, ipaddresspool, vlan_id, vmknics, teaming, mtu):
    vxlan_prep_dvs = session.extract_resource_body_example('nwfabricConfig', 'create')
    vxlan_prep_dvs['nwFabricFeatureConfig']['resourceConfig']['resourceId'] = dvs_moid
    vxlan_prep_dvs['nwFabricFeatureConfig']['featureId'] = 'com.vmware.vshield.vsm.vxlan'
    vxlan_prep_dvs['nwFabricFeatureConfig']['resourceConfig'].update({'configSpec': {'@class': 'vdsContext',
                                                                                     'switch': {'objectId': dvs_moid},
                                                                                     'mtu': mtu,
                                                                                     'teaming': teaming}})
    session.create('nwfabricConfig', request_body_dict=vxlan_prep_dvs)

    vxlan_prep_cluster = session.extract_resource_body_example('nwfabricConfig', 'create')
    vxlan_prep_cluster['nwFabricFeatureConfig']['resourceConfig']['resourceId'] = cluster_moid
    vxlan_prep_cluster['nwFabricFeatureConfig']['featureId'] = 'com.vmware.vshield.vsm.vxlan'
    vxlan_prep_cluster['nwFabricFeatureConfig']['resourceConfig'].update({'configSpec': {'@class': 'clusterMappingSpec',
                                                                                         'switch': {'objectId':
                                                                                                    dvs_moid},
                                                                                         'vlanId': vlan_id,
                                                                                         'vmknicCount': vmknics,
                                                                                         'ipPoolId': ipaddresspool}})

    vxlan_prep_cluster_response = session.create('nwfabricConfig', request_body_dict=vxlan_prep_cluster)
    return vxlan_prep_cluster_response['objectId']


def vxlan_unprep_cluster(session, cluster_moid):
    vxlan_prep_cluster = session.extract_resource_body_example('nwfabricConfig', 'delete')
    vxlan_prep_cluster['nwFabricFeatureConfig']['resourceConfig']['resourceId'] = cluster_moid
    vxlan_prep_cluster['nwFabricFeatureConfig']['featureId'] = 'com.vmware.vshield.vsm.vxlan'

    vxlan_prep_cluster_response = session.delete('nwfabricConfig', request_body_dict=vxlan_prep_cluster)
    return vxlan_prep_cluster_response['objectId']


def vxlan_unprep_dvs_context(session, dvs_moid):
    vxlan_prep_dvs = session.extract_resource_body_example('nwfabricConfig', 'delete')
    vxlan_prep_dvs['nwFabricFeatureConfig']['resourceConfig']['resourceId'] = dvs_moid
    vxlan_prep_dvs['nwFabricFeatureConfig']['featureId'] = 'com.vmware.vshield.vsm.vxlan'

    vxlan_prep_dvs_response = session.delete('nwfabricConfig', request_body_dict=vxlan_prep_dvs)
    return vxlan_prep_dvs_response['objectId']


def wait_for_job_completion(session, job_id, completion_status):
    status_poll_count = 0
    while status_poll_count < 20:
        response = session.read('taskFrameworkJobs', uri_parameters={'jobId': job_id})
        status = response['body']['jobInstances']['jobInstance']['status']
        if status == completion_status:
            return True
        else:
            time.sleep(10)
            status_poll_count += 1

    return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            cluster_moid=dict(required=True),
            dvs_moid=dict(required=True),
            ippool_id=dict(),
            vlan_id=dict(default=0, type='int'),
            vmknic_count=dict(default=1),
            teaming=dict(default='FAILOVER_ORDER', choices=['FAILOVER_ORDER',
                                                            'ETHER_CHANNEL',
                                                            'LACP_ACTIVE',
                                                            'LACP_PASSIVE',
                                                            'LOADBALANCE_SRCID',
                                                            'LOADBALANCE_SRCMAC'
                                                            'LACP_V2']),
            mtu=dict(default=1600)
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient

    s = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                  module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'])

    vxlan_status = get_cluster_status(s, module.params['cluster_moid'])

    if vxlan_status == 'GREEN' and module.params['state'] == 'absent':
        unprep_job = vxlan_unprep_cluster(s, module.params['cluster_moid'])
        wait_for_job_completion(s, unprep_job, completion_status='COMPLETED')
        vxlan_unprep_dvs_context(s, module.params['dvs_moid'])
        module.exit_json(changed=True)

    if vxlan_status != 'GREEN' and module.params['state'] == 'present':
        vxlan_prep_response = vxlan_prep(s, module.params['cluster_moid'], module.params['dvs_moid'],
                                         module.params['ippool_id'], module.params['vlan_id'],
                                         module.params['vmknic_count'], module.params['teaming'], module.params['mtu'])
        wait_for_job_completion(s, vxlan_prep_response, completion_status='COMPLETED')
        module.exit_json(changed=True, vxlan_prep_response=vxlan_prep_response)

    module.exit_json(changed=False, vxlan_status=vxlan_status)

from ansible.module_utils.basic import *


if __name__ == '__main__':
    main()
