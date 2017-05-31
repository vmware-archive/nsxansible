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


def retrieve_vc_config(session):
    vc_reg_resp = session.read('vCenterConfig')
    return vc_reg_resp['body']


def change_vc_config(session, body_dict):
    return session.update('vCenterConfig', request_body_dict=body_dict)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            vcenter=dict(required=True),
            vcusername=dict(required=True),
            vcpassword=dict(required=True, no_log=True),
            vccertthumbprint=dict(),
            accept_all_certs=dict(choices=['True', 'False'])
        ),
        required_one_of = [['accept_all_certs','vccertthumbprint']],
        mutually_exclusive = [['accept_all_certs','vccertthumbprint']],
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    import OpenSSL, ssl

    s = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                  module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'])

    vc_config = retrieve_vc_config(s)

    api_cert = ssl.get_server_certificate((module.params['vcenter'], 443),
                                          ssl_version=2)
    x509_api = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, api_cert)
    api_cert_thumbp = x509_api.digest('sha1')

    if module.params['accept_all_certs']:
        module.params['vccertthumbprint'] = api_cert_thumbp

    if 'ipAddress' not in vc_config['vcInfo'].keys():
        change_required = True
        vc_config['vcInfo']['userName'] = module.params['vcusername']
        vc_config['vcInfo']['ipAddress'] = module.params['vcenter']
        vc_config['vcInfo']['certificateThumbprint'] = module.params['vccertthumbprint']
    else:
       change_required = False

    for vcconfig_detail_key, vcconfig_detail_value in vc_config['vcInfo'].iteritems():
        if vcconfig_detail_key == 'userName' and vcconfig_detail_value != module.params['vcusername']:
            vc_config['vcInfo']['userName'] = module.params['vcusername']
            change_required = True
        elif vcconfig_detail_key == 'ipAddress' and vcconfig_detail_value != module.params['vcenter']:
            vc_config['vcInfo']['ipAddress'] = module.params['vcenter']
            change_required = True
        elif vcconfig_detail_key == 'certificateThumbprint' and \
                        vcconfig_detail_value != module.params['vccertthumbprint']:
            vc_config['vcInfo']['certificateThumbprint'] = module.params['vccertthumbprint']
            change_required = True
    if change_required:
        vc_config['vcInfo']['assignRoleToUser'] = 'true'
        vc_config['vcInfo']['password'] = module.params['vcpassword']
        if 'vcInventoryLastUpdateTime' in vc_config['vcInfo']:
            vc_config['vcInfo'].pop('vcInventoryLastUpdateTime')
        sso_config_response = change_vc_config(s, vc_config)
        module.exit_json(changed=True, argument_spec=module.params, sso_config_response=sso_config_response)
    else:
        module.exit_json(changed=False, argument_spec=module.params)


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
