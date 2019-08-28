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


def get_syslog_settings(session):
    return session.read('nsxControllerClusterSyslog')


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


def update_syslog_settings(session, body_dict):
    response =  session.update('nsxControllerClusterSyslog', request_body_dict=body_dict)
    if response['status'] != 200:
        module.fail_json(msg="Unknown response received whilst attempting to update syslog settings.", response=response)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            syslog_servers=dict(required=True, type='list', elements='dict', options=dict(
                server=dict(required=True, type='str'),
                port=dict(type='str', default="6514"),
                level=dict(type='str', default='INFO', choices=['INFO', 'ERROR', 'WARN']),
                protocol=dict(type='str', default='TLS', choices=['TLS', 'UDP', 'TCP']),
                certificate=dict(type='str')
            )),
            state=dict(default='present', choices=['present', 'update', 'absent'])
        ),
        supports_check_mode=True
    )

    from nsxramlclient.client import NsxClient

    session = NsxClient(module.params['nsxmanager_spec']['raml_file'],
                        module.params['nsxmanager_spec']['host'],
                        module.params['nsxmanager_spec']['user'],
                        module.params['nsxmanager_spec']['password'])

    # Ensure given syslog_servers meet spec
    for idx, syslog_server in enumerate(module.params['syslog_servers']):
        # rename server to match Nsx
        syslog_server['syslogServer'] = syslog_server.pop('server')

        if (int(syslog_server['port']) < 1 or int(syslog_server['port']) > 65535):
            module.fail_json(msg="syslog server %s 'port' must be between 1 and 65535." % syslog_server['syslogServer'] )

        if 'TLS' in syslog_server['protocol'] and module.params['state'] != 'absent':
            if ('certificate' not in syslog_server or syslog_server['certificate'] is None):
                module.fail_json(msg="syslog server %s must contain a 'certificate' with the x509 PEM encoded certificate when 'protocol' is set to 'TLS' (default)." % syslog_server['syslogServer'])

    # Get settings from NSX
    syslog_settings = get_syslog_settings(session)

    syslog_servers = []

    # Extract syslog servers
    if ('body' in syslog_settings and syslog_settings['body'] is not None):
        if ('ControllerSyslogServerList' in syslog_settings['body'] and
                syslog_settings['body']['ControllerSyslogServerList'] is not None):
            if ('controllerSyslogServer' in syslog_settings['body']['ControllerSyslogServerList'] and
                    syslog_settings['body']['ControllerSyslogServerList']['controllerSyslogServer'] is not None):
                syslog_servers = syslog_settings['body']['ControllerSyslogServerList']['controllerSyslogServer']

    # Ensure everything is a list
    if not isinstance(syslog_servers, list):
        syslog_servers = [syslog_servers]

    # Fill in certificate for easier comparison later on
    for syslog_server in syslog_servers:
        if 'certificate' not in syslog_server:
            syslog_server['certificate'] = None

    # The default return if not changed
    return_dict = {
        "changed": False,
        "syslog_servers": syslog_servers,
    }

    changed = False
    change_required = False

    new_syslog_servers = []

    if module.params['state'] == 'present':
        # ensure config is as stated else replace the lot
        merged_list = zip(syslog_servers, module.params['syslog_servers'])
        if (len(syslog_servers) != len(module.params['syslog_servers']) or
                any(a != b for a, b in merged_list)):
            new_syslog_servers = module.params['syslog_servers']
            change_required = True

    if module.params['state'] == 'update':
        # update any existing syslog servers else add to the list
        new_syslog_servers = list(syslog_servers)
        for update_syslog_server in module.params['syslog_servers']:
            for idx, existing_syslog_server in enumerate(new_syslog_servers):
                if existing_syslog_server['syslogServer'] == update_syslog_server['syslogServer']:
                    if (existing_syslog_server['port'] != update_syslog_server['port'] or
                        existing_syslog_server['level'] != update_syslog_server['level'] or
                        existing_syslog_server['protocol'] != update_syslog_server['protocol'] or
                        ('TLS' in existing_syslog_server['protocol'] and 
                        existing_syslog_server['certificate'] != update_syslog_server['certificate'])
                        ):
                        new_syslog_servers[idx].update(update_syslog_server)
                        change_required = True
                        break
                    else:
                        break
            else:
                # update_syslog_server not found in existing syslog servers
                new_syslog_servers.append(update_syslog_server)
                change_required = True

    elif module.params['state'] == 'absent':
        # remove from existing config any present servers
        new_syslog_servers = list(syslog_servers)
        for remove_syslog_server in module.params['syslog_servers']:
            for idx, existing_syslog_server in enumerate(new_syslog_servers):
                if existing_syslog_server['syslogServer'] == remove_syslog_server['syslogServer']:
                    del new_syslog_servers[idx]
                    change_required = True
                    break

    if change_required:
        # Fail if too many syslog servers requested to be configured. Current limitaton is 2.
        if len(new_syslog_servers) > 2:
            module.fail_json(msg="A maximum of 2 syslog servers is permitted.")

        new_syslog_settings = session.extract_resource_body_example('nsxControllerClusterSyslog', 'update')
        new_syslog_settings['ControllerSyslogServerList']['controllerSyslogServer'] = new_syslog_servers

        if not module.check_mode:
            update_syslog_settings(session, new_syslog_settings)

        return_dict['changed'] = True
        return_dict['syslog_servers'] = new_syslog_servers

    module.exit_json(**return_dict)


if __name__ == '__main__':
    main()
