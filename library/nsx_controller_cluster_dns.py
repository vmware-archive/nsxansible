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


def get_dns_settings(session):
    return session.read('nsxControllerClusterDns')


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


def update_dns_settings(session, body_dict):
    response =  session.update('nsxControllerClusterDns', request_body_dict=body_dict)
    if response['status'] != 200:
        module.fail_json(msg="Unknown response received whilst attempting to update dns settings.", response=response)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            dns_servers=dict(default=[], type='list'),
            dns_suffixes=dict(default=[], type='list'),
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

    dns_settings = get_dns_settings(session)

    dns_servers = []
    dns_suffixes = []

    if ('body' in dns_settings and dns_settings['body'] is not None):
        if ('ControllerClusterDns' in dns_settings['body'] and
                dns_settings['body']['ControllerClusterDns'] is not None):
            if ('dnsServer' in dns_settings['body']['ControllerClusterDns'] and
                    dns_settings['body']['ControllerClusterDns']['dnsServer'] is not None):
                dns_servers = dns_settings['body']['ControllerClusterDns']['dnsServer']
            if ('dnsSuffix' in dns_settings['body']['ControllerClusterDns'] and
                    dns_settings['body']['ControllerClusterDns']['dnsSuffix'] is not None):
                dns_suffixes = dns_settings['body']['ControllerClusterDns']['dnsSuffix']

    # Ensure everything is a list
    if not isinstance(dns_servers, list):
        dns_servers = [dns_servers]
    if not isinstance(dns_suffixes, list):
        dns_suffixes = [dns_suffixes]
    if not isinstance(module.params['dns_servers'], list):
        module.params['dns_servers'] = [module.params['dns_servers']]
    if not isinstance(module.params['dns_suffixes'], list):
        module.params['dns_suffixes'] = [module.params['dns_suffixes']]

    # The default return if not changed
    return_dict = {
        "changed": False,
        "dns_servers": dns_servers,
        "dns_suffixes": dns_suffixes
    }

    if module.params['state'] == 'present':
        # ensure config is as stated
        new_dns_servers, change_required = replace_existing_list(module.params['dns_servers'], dns_servers, change_required)
        new_dns_suffixes, change_required = replace_existing_list(module.params['dns_suffixes'], dns_suffixes, change_required)
    elif module.params['state'] == 'update':
        # append to existing config any new servers or suffixes
        new_dns_servers, change_required = append_into_existing_list(module.params['dns_servers'], dns_servers, change_required)
        new_dns_suffixes, change_required = append_into_existing_list(module.params['dns_suffixes'], dns_suffixes, change_required)
    elif module.params['state'] == 'absent':
        # remove from existing config any present servers or suffixes
        new_dns_servers, change_required = remove_from_existing_list(module.params['dns_servers'], dns_servers, change_required)
        new_dns_suffixes, change_required = remove_from_existing_list(module.params['dns_suffixes'], dns_suffixes, change_required)

    if change_required:
        new_dns_settings = session.extract_resource_body_example('nsxControllerClusterDns', 'update')
        new_dns_settings['ControllerClusterDns']['dnsServer'] = new_dns_servers
        new_dns_settings['ControllerClusterDns']['dnsSuffix'] = new_dns_suffixes

        if not module.check_mode:
            update_dns_settings(session, new_dns_settings)

        return_dict['changed'] = True
        return_dict['dns_servers'] = new_dns_servers
        return_dict['dns_suffixes'] = new_dns_suffixes

    module.exit_json(**return_dict)


if __name__ == '__main__':
    main()
