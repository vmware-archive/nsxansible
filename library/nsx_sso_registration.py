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

def check_sso_status(session):
    status_response = session.read('ssoStatus')['body']['boolean']
    if status_response == 'true':
        return True
    else:
        return False


def config_sso(session, body_dict):
    return session.create('ssoConfig', request_body_dict=body_dict)


def retrieve_sso_config(session):
    sso_reg_resp = session.read('ssoConfig')
    return sso_reg_resp['body']


def delete_sso_config(session):
    return session.delete('ssoConfig')


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True),
            sso_lookupservice_url=dict(required=True),
            sso_lookupservice_port=dict(required=True),
            sso_lookupservice_server=dict(required=True),
            sso_admin_username=dict(required=True),
            sso_admin_password=dict(required=True, no_log=True),
            sso_certthumbprint=dict(),
            accept_all_certs=dict(choices=[True, False])
        ),
        required_one_of = [['accept_all_certs','sso_certthumbprint']],
        mutually_exclusive = [['accept_all_certs','sso_certthumbprint']],
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    import OpenSSL, ssl

    s = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                  module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'])

    lookup_service_full_url = 'https://{}:{}/{}'.format(module.params['sso_lookupservice_server'],
                                                        module.params['sso_lookupservice_port'],
                                                        module.params['sso_lookupservice_url'])

    sso_cert = ssl.get_server_certificate((module.params['sso_lookupservice_server'],
                                           module.params['sso_lookupservice_port']))
    x509_sso = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, sso_cert)
    sso_cert_thumbp = x509_sso.digest('sha1')

    if module.params['accept_all_certs']:
        module.params['sso_certthumbprint'] = sso_cert_thumbp

    if not check_sso_status(s) and module.params['state'] == 'present':
        sso_reg = s.extract_resource_body_schema('ssoConfig', 'create')
        sso_reg['ssoConfig']['ssoAdminUsername'] = module.params['sso_admin_username']
        sso_reg['ssoConfig']['ssoAdminUserpassword'] = module.params['sso_admin_password']
        sso_reg['ssoConfig']['ssoLookupServiceUrl'] = lookup_service_full_url
        sso_reg['ssoConfig']['certificateThumbprint'] = module.params['sso_certthumbprint']
        sso_config_response = config_sso(s, sso_reg)
        module.exit_json(changed=True, argument_spec=module.params, sso_config_response=sso_config_response)
    elif check_sso_status(s) and module.params['state'] == 'absent':
        sso_config_response = delete_sso_config(s)
        module.exit_json(changed=True, argument_spec=module.params, sso_config_response=sso_config_response)

    sso_config = retrieve_sso_config(s)
    change_required = False

    for ssoconfig_detail_key, ssoconfig_detail_value in sso_config['ssoConfig'].iteritems():
        if ssoconfig_detail_key == 'ssoAdminUsername' and ssoconfig_detail_value != module.params['sso_admin_username']:
            sso_config['ssoConfig']['ssoAdminUsername'] = module.params['sso_admin_username']
            change_required = True
        elif ssoconfig_detail_key == 'ssoLookupServiceUrl' and \
                        ssoconfig_detail_value != lookup_service_full_url:
            sso_config['ssoConfig']['ssoLookupServiceUrl'] = lookup_service_full_url
            change_required = True
        elif ssoconfig_detail_key == 'certificateThumbprint' and \
                        ssoconfig_detail_value != module.params['sso_certthumbprint']:
            sso_config['ssoConfig']['certificateThumbprint'] = module.params[' sso_certthumbprint']
            change_required = True
    if change_required:
        sso_config['ssoConfig']['ssoAdminUserpassword'] = module.params['sso_admin_password']
        delete_sso_config(s)
        sso_config_response = config_sso(s, sso_config)
        module.exit_json(changed=True, argument_spec=module.params, sso_config_response=sso_config_response)
    else:
        module.exit_json(changed=False, argument_spec=module.params)


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
