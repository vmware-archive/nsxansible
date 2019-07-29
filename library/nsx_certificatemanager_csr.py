#!/usr/bin/env python
# coding=utf-8
#
# Copyright � 2019 VMware, Inc. All Rights Reserved.
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

import OpenSSL
from ansible.errors import AnsibleError

__author__ = 'kierenhamps'


def get_csr(client_session):
    return client_session.read('certificateCsr')


def get_csr_details(client_session, csr):
    req = OpenSSL.crypto.load_certificate_request(OpenSSL.crypto.FILETYPE_PEM, csr)
    key = req.get_pubkey()
    key_type = 'RSA' if key.type() == OpenSSL.crypto.TYPE_RSA else 'DSA'
    subject = req.get_subject()
    components = dict(subject.get_components())

    decoded_csr = client_session.extract_resource_body_example('certificateCsr', 'create')
    decoded_csr['csr']['algorithm'] = key_type
    decoded_csr['csr']['keySize'] = key.bits()
    decoded_csr['csr']['subjectDto']['commonName'] = get_component(components, 'CN')
    decoded_csr['csr']['subjectDto']['organizationUnit'] = get_component(components, 'OU')
    decoded_csr['csr']['subjectDto']['organizationName'] = get_component(components, 'O')
    decoded_csr['csr']['subjectDto']['localityName'] = get_component(components, 'L')
    decoded_csr['csr']['subjectDto']['stateName'] = get_component(components, 'ST')
    decoded_csr['csr']['subjectDto']['countryCode'] = get_component(components, 'C')
    return decoded_csr


def get_component(components, key):
    if key in components:
        return components[key]

    return None


def create_csr(client_session, body_dict):
    return client_session.create('certificateCsr', request_body_dict=body_dict)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            algorithm=dict(default='RSA', choices=['RSA']),
            key_size=dict(required=True, choices=['2048','3072','4096']),
            common_name=dict(required=True, type='str'),
            organization_unit=dict(required=True, type='str'),
            organization_name=dict(required=True, type='str'),
            locality_name=dict(type='str'),
            state_name=dict(type='str'), 
            country_code=dict(required=True, choices=[
                'AD','AE','AF','AG','AI','AL','AM','AN','AO','AQ','AR','AS',
                'AT','AU','AW','AX','AZ','BA','BB','BD','BE','BF','BG','BH',
                'BI','BJ','BL','BM','BN','BO','BQ','BR','BS','BT','BV','BW',
                'BY','BZ','CA','CC','CD','CF','CG','CH','CI','CK','CL','CM',
                'CN','CO','CR','CS','CT','CU','CV','CX','CY','CZ','DD','DE',
                'DJ','DK','DM','DO','DZ','EC','EE','EG','EH','ER','ES','ET',
                'FI','FJ','FK','FM','FO','FQ','FR','FX','GA','GB','GD','GE',
                'GF','GG','GH','GI','GL','GM','GN','GP','GQ','GR','GS','GT',
                'GU','GW','GY','HK','HM','HN','HR','HT','HU','ID','IE','IL',
                'IM','IN','IO','IQ','IR','IS','IT','JE','JM','JO','JP','JT',
                'KE','KG','KH','KI','KM','KN','KP','KR','KW','KY','KZ','LA',
                'LB','LC','LI','LK','LR','LS','LT','LU','LV','LY','MA','MC',
                'MD','ME','MF','MG','MH','MI','MK','ML','MM','MN','MO','MP',
                'MQ','MR','MS','MT','MU','MV','MW','MX','MY','MZ','NA','NC',
                'NE','NF','NG','NI','NL','NO','NP','NQ','NR','NT','NU','NZ',
                'OM','PA','PC','PE','PF','PG','PH','PK','PL','PM','PN','PR',
                'PS','PT','PU','PW','PY','PZ','QA','RE','RO','RS','RU','RW',
                'SA','SB','SC','SD','SE','SG','SH','SI','SJ','SK','SL','SM',
                'SN','SO','SR','ST','SU','SV','SY','SZ','TC','TD','TF','TG',
                'TH','TJ','TK','TL','TM','TN','TO','TR','TT','TV','TW','TZ',
                'UA','UG','UM','US','UY','UZ','VA','VC','VD','VE','VG','VI',
                'VN','VU','WF','WK','WS','YD','YE','YT','ZA','ZM','ZW'])
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient

    client_session = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                               module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'],
                               fail_mode="continue")

    csr = get_csr(client_session)
    
    change_required = False

    if csr['status'] == 400:
        # CSR is not yet generated
        csr_details = client_session.extract_resource_body_example('certificateCsr', 'create')
        csr_details['csr']['algorithm'] = module.params['algorithm']
        csr_details['csr']['keySize'] = module.params['key_size']
        csr_details['csr']['subjectDto']['commonName'] = module.params['common_name']
        csr_details['csr']['subjectDto']['organizationUnit'] = module.params['organization_unit']
        csr_details['csr']['subjectDto']['organizationName'] = module.params['organization_name']
        csr_details['csr']['subjectDto']['localityName'] = module.params['locality_name']
        csr_details['csr']['subjectDto']['stateName'] = module.params['state_name']
        csr_details['csr']['subjectDto']['countryCode'] = module.params['country_code']
        change_required = True

    if csr['status'] == 200:
        csr_details = get_csr_details(client_session, csr['body'])
        if csr_details['csr']['algorithm'] != module.params['algorithm']:
            csr_details['csr']['algorithm'] = module.params['algorithm']
            change_required = True
        if str(csr_details['csr']['keySize']) != str(module.params['key_size']):
            csr_details['csr']['keySize'] = module.params['key_size']
            change_required = True
        if csr_details['csr']['subjectDto']['commonName'] != module.params['common_name']:
            csr_details['csr']['subjectDto']['commonName'] = module.params['common_name']
            change_required = True
        if csr_details['csr']['subjectDto']['organizationUnit'] != module.params['organization_unit']:
            csr_details['csr']['subjectDto']['organizationUnit'] = module.params['organization_unit']
            change_required = True
        if csr_details['csr']['subjectDto']['organizationName'] != module.params['organization_name']:
            csr_details['csr']['subjectDto']['organizationName'] = module.params['organization_name']
            change_required = True
        if csr_details['csr']['subjectDto']['localityName'] != module.params['locality_name']:
            csr_details['csr']['subjectDto']['localityName'] = module.params['locality_name']
            change_required = True
        if csr_details['csr']['subjectDto']['stateName'] != module.params['state_name']:
            csr_details['csr']['subjectDto']['stateName'] = module.params['state_name']
            change_required = True
        if csr_details['csr']['subjectDto']['countryCode'] != module.params['country_code']:
            csr_details['csr']['subjectDto']['countryCode'] = module.params['country_code'] 
            change_required = True

    if change_required:
        create_response = create_csr(client_session, csr_details)

        if create_response['status'] != 201:
            raise AnsibleError(create_response['body']['errors']['error']['details'])

        csr_data = get_csr(client_session)
        csr_details = get_csr_details(client_session, csr_data['body'])

        module.exit_json(changed=True, argument_spec=module.params, create_response=create_response,
                         csr_response=csr_data, csr_details=csr_details)
    else:
        csr_details = get_csr_details(client_session, csr['body'])
        module.exit_json(changed=False, argument_spec=module.params, 
                         csr_response=csr, csr_details=csr_details)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
