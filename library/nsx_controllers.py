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


def get_controller_cluster_info(session):
    return session.read('nsxControllers')['body']


def create_controllers(session, controller_count, module):
    controller_spec = session.extract_resource_body_example('nsxControllers', 'create')
    controller_spec['controllerSpec']['datastoreId'] = module.params['datastore_moid']
    controller_spec['controllerSpec']['networkId'] = module.params['network_moid']
    controller_spec['controllerSpec']['resourcePoolId'] = module.params['resourcepool_moid']
    controller_spec['controllerSpec']['ipPoolId'] = module.params['ippool_id']
    controller_spec['controllerSpec']['password'] = module.params['password']
    controller_spec['controllerSpec']['hostId'] = module.params['host_moid']
    controller_spec['controllerSpec']['deployType'] = module.params['deploysize']

    for controller_nr in range(controller_count):
        job_id = session.create('nsxControllers', request_body_dict=controller_spec)['body']

        status_poll_count = 0
        while status_poll_count < 20:
            response = session.read('nsxControllerJob', uri_parameters={'jobId': job_id})
            status = response['body']['controllerDeploymentInfo']['status']
            if status == 'Success':
                break
            elif status == 'Failure':
                return False
            else:
                status_poll_count += 1
                time.sleep(30)

        if status_poll_count == 20:
            return False

    return True


def get_controller_id_list(controller_cluster):
    if not controller_cluster['controllers']:
        return []
    if type(controller_cluster['controllers']['controller']) is dict:
        return [controller_cluster['controllers']['controller']['id']]
    elif type(controller_cluster['controllers']['controller']) is list:
        return [controller_ids['id'] for controller_ids in controller_cluster['controllers']['controller']]


def delete_controller_cluster(session, controller_id_list):
        for controller_id in controller_id_list:
            session.delete('nsxController', uri_parameters={'controllerId': controller_id},
                           query_parameters_dict={'forceRemoval': 'true'})


def get_controller_syslog(session, controller_id_list):
    controller_syslog_dict = {}
    for controller_id in controller_id_list:
        try:
            syslog_ip_response = session.read('nsxControllerSyslog', uri_parameters={'controllerId': controller_id})
            syslog_ip = syslog_ip_response['body']['controllerSyslogServer']['syslogServer']
        except SystemExit:
            syslog_ip = None
        controller_syslog_dict.update({controller_id: syslog_ip})
    return controller_syslog_dict


def set_controller_syslog(session, controller_id, syslog_server):
    syslog_spec = session.extract_resource_body_example('nsxControllerSyslog', 'create')
    syslog_spec['controllerSyslogServer']['syslogServer'] = syslog_server
    syslog_spec['controllerSyslogServer']['port'] = '514'
    syslog_spec['controllerSyslogServer']['protocol'] = 'UDP'
    syslog_spec['controllerSyslogServer']['level'] = 'INFO'
    session.create('nsxControllerSyslog', uri_parameters={'controllerId': controller_id}, request_body_dict=syslog_spec)


def clear_controller_syslog(session, controller_id):
    session.delete('nsxControllerSyslog', uri_parameters={'controllerId': controller_id})


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            deploytype=dict(default='full', choices=['single', 'full', 'lab']),
            deploysize=dict(default='small', choices=['small', 'medium', 'large']),
            syslog_server=dict(),
            ippool_id=dict(required=True),
            resourcepool_moid=dict(required=True),
            datastore_moid=dict(required=True),
            host_moid=dict(),
            network_moid=dict(required=True),
            password=dict(required=True)
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient

    s = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                  module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'])

    new_controllers_deployed = False
    controller_cluster = get_controller_cluster_info(s)
    controller_id_list = get_controller_id_list(controller_cluster)

    if module.params['state'] == 'absent' and not controller_cluster['controllers']:
        module.exit_json(changed=False, argument_spec=module.params)
    elif module.params['state'] == 'absent' and controller_cluster['controllers']:
        delete_controller_cluster(s, controller_id_list)
        module.exit_json(changed=True, argument_spec=module.params)
    elif module.params['state'] == 'present':
        controller_to_deploy = 0
        if module.params['deploytype'] == 'single':
            if len(controller_id_list) < 3:
                controller_to_deploy = 1
        elif module.params['deploytype'] == 'full':
            if len(controller_id_list) == 0:
                controller_to_deploy = 3
        elif module.params['deploytype'] == 'lab':
            if len(controller_id_list) == 0:
                controller_to_deploy = 1
        if controller_to_deploy != 0:
            if not create_controllers(s, controller_to_deploy, module):
                module.fail_json(msg='failed to deploy controllers')
            else:
                controller_cluster = get_controller_cluster_info(s)
                controller_id_list = get_controller_id_list(controller_cluster)
                new_controllers_deployed = True

    controller_syslog = get_controller_syslog(s, controller_id_list)
    controller_syslog_changed = False

    for controller in controller_id_list:
        if module.params['syslog_server'] and controller_syslog[controller] != module.params['syslog_server']:
            clear_controller_syslog(s, controller)
            set_controller_syslog(s, controller, module.params['syslog_server'])
            controller_syslog_changed = True
        elif not module.params['syslog_server'] and controller_syslog[controller]:
            clear_controller_syslog(s, controller)
            controller_syslog_changed = True

    if new_controllers_deployed or controller_syslog_changed:
        module.exit_json(changed=True, argument_spec=module.params)
    else:
        module.exit_json(changed=False, argument_spec=module.params)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
