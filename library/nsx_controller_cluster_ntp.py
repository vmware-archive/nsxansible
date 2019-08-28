#!/usr/bin/env python
# coding=utf-8
#
# Copyright © 2019 VMware, Inc. All Rights Reserved.
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

from ansible.module_utils.basic import *

__author__ = 'kierenhamps'


def append_into_existing_list(newlist, oldlist, changeflag):
    """ Append a list into another list.

        The order of the items in the final list will be the same as the
        oldlist with any newlist items appended to the end in the order from 
        the newlist.

        Both input lists will be left intact and unchanged.

        Returns a tuple containing:
            tempitems : An array containing the resulting list
            changeflag : A boolean indicating if any new items were appended into
                      the oldlist.
    """
    templist = list(oldlist)
    for newitem in newlist:
        if newitem not in templist:
            templist.append(newitem)
            changeflag = True

    return templist, changeflag


def get_ntp_settings(session):
    return session.read('nsxControllerClusterNtp')


def remove_from_existing_list(newlist, oldlist, changeflag):
    """ Remove a list from another list.

        The order of the items in the final list will be the same as the
        oldlist with any newlist items removed.

        Both input lists will be left intact and unchanged.

        Returns a tuple containing:
            tempitems : An array containing the resulting list
            changeflag : A boolean indicating if any new items were removed from
                      the oldlist.
    """
    templist = list(oldlist)
    for newitem in newlist:
        if newitem in templist:
            templist.remove(newitem)
            changeflag = True

    return templist, changeflag


def replace_existing_list(newlist, oldlist, changeflag):
    """ Replace a list with another list.

        Only replace the list if they are not identical.

        Both input lists will be left intact and unchanged.

        Returns a tuple containing:
            tempitems : the resulting list of the replacement or original list.
            changeflag : A boolean indicating if the list was replaced.
    """
    templist = list(oldlist)
    if templist != newlist:
        templist = newlist
        changeflag = True
    
    return templist, changeflag


def update_ntp_settings(session, body_dict):
    response = session.update('nsxControllerClusterNtp', request_body_dict=body_dict)
    if response['status'] != 200:
        module.fail_json(msg="Unknown response received whilst attempting to update ntp settings.", response=response)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            ntp_servers=dict(default=[], type='list'),
            state=dict(default='present', choices=['present', 'update', 'absent'])
        ),
        supports_check_mode=True
    )

    from nsxramlclient.client import NsxClient

    session = NsxClient(module.params['nsxmanager_spec']['raml_file'],
                        module.params['nsxmanager_spec']['host'],
                        module.params['nsxmanager_spec']['user'],
                        module.params['nsxmanager_spec']['password'])

    changed = False
    change_required = False

    ntp_settings = get_ntp_settings(session)

    ntp_servers = []

    if ('body' in ntp_settings and ntp_settings['body'] is not None):
        if ('ControllerClusterNtpServers' in ntp_settings['body'] and
                ntp_settings['body']['ControllerClusterNtpServers'] is not None):
            if ('ntpServers' in ntp_settings['body']['ControllerClusterNtpServers'] and
                    ntp_settings['body']['ControllerClusterNtpServers']['ntpServers'] is not None):
                if ('string' in ntp_settings['body']['ControllerClusterNtpServers']['ntpServers'] and
                        ntp_settings['body']['ControllerClusterNtpServers']['ntpServers']['string'] is not None):
                    ntp_servers = ntp_settings['body']['ControllerClusterNtpServers']['ntpServers']['string']

    # Ensure everything is a list
    if not isinstance(ntp_servers, list):
        ntp_servers = [ntp_servers]
    if not isinstance(module.params['ntp_servers'], list):
        module.params['ntp_servers'] = [module.params['ntp_servers']]

    # The default return if not changed
    return_dict = {
        "changed": False,
        "ntp_servers": ntp_servers
    }

    if module.params['state'] == 'present':
        # ensure config is as stated
        new_ntp_servers, change_required = replace_existing_list(module.params['ntp_servers'], ntp_servers, change_required)
    elif module.params['state'] == 'update':
        # append to existing config any new servers
        new_ntp_servers, change_required = append_into_existing_list(module.params['ntp_servers'], ntp_servers, change_required)
    elif module.params['state'] == 'absent':
        # remove from existing config any present servers
        new_ntp_servers, change_required = remove_from_existing_list(module.params['ntp_servers'], ntp_servers, change_required)

    if change_required:
        new_ntp_settings = session.extract_resource_body_example('nsxControllerClusterNtp', 'update')
        new_ntp_settings['ControllerClusterNtpServers']['ntpServers']['string'] = new_ntp_servers

        if not module.check_mode:
            update_ntp_settings(session, new_ntp_settings)

        return_dict['changed'] = True
        return_dict['ntp_servers'] = new_ntp_servers

    module.exit_json(**return_dict)


if __name__ == '__main__':
    main()
