#!/usr/bin/env python
# coding=utf-8
#
# Copyright © 2018 VMware, Inc. All Rights Reserved.
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

__author__ = 'virtualelephant'

try:
    from pyVmomi import vim, vmodl
    from pyVmomi.connect import SmartConnect
    HAS_PYVMOMI = True

except ImportError:
    HAS_PYVMOMI = False

def get_syslog_server(client_session, user_id):
    """
    Pre-NSX 6.4 functionality
    Retrieves only the first syslog server among the servers configured.
    :param client_session: An instance of an NsxClient session
    """

    cfg_result = client_session.read('systemSyslogServer')

    if cfg_result['status'] == 200:
        return True
    else:
        return False

def configure_syslog_server(client_session, server, port, protocol):
    """
    Pre-NSX 6.4 functionality
    Configures 1 syslog server. If there are syslog server(s) already configured, 
    this API replaces the first one in the list.
    :param client_session: An instance of an NsxClient session
    :param server: The syslog server to connect to.
    :param port: The port to use to connect to the syslog server. Default is 514.
    :param protocol: The protocol to use to connect to the syslog server. Default is UDP.
    """

    syslog_body_dict = { 'syslogServer': server, 'port': port, 'protocol': protocol }

    cfg_result = client_session.update('systemSyslogServer', request_body_dict={'syslogserver': syslog_body_dict})

    if cfg_result['status'] == 204:
        return True
    else:
        return False

def delete_syslog_server(client_session):
    """
    Pre-NSX 6.4 functionality
    Deletes all the syslog servers.
    Deletes ALL configured syslog servers
    :param client_session: An instance of an NsxClient session
    """

    cfg_result = client_session.delete('systemSyslogServer')

    if cfg_result['status'] == 204:
        return True
    else:
        return False

def main():
    module = AnsibleModule(
            argument_spec=dict(
                state=dict(default='present', choices=['present', 'absent']),
                nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
                syslog_server=dict(required=True),
                syslog_port=dict(default=514),
                syslog_protocol=dict(default='udp', choices=['udp', 'tcp'])
            ),
            supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient

    client_session = NsxClient(module.params['nsxmanager_spec']['raml_file'],
                               module.params['nsxmanager_spec']['host'],
                               module.params['nsxmanager_spec']['user'],
                               module.params['nsxmanager_spec']['password'])

    changed = False

    if module.params['state'] == 'present':
        changed = configure_syslog_server(client_session, module.params['syslog_server'], module.params['syslog_port'], module.params['syslog_protocol'])
    elif module.params['state'] == 'absent':
        changed = delete_syslog_server(client_session)
    

    if changed:
        module.exit_json(changed=True)
    else:
        module.exit_json(changed=False)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
