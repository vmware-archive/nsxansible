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

DOCUMENTATION = '''
'''

EXAMPLE = '''
- name: Testing changing edge fw rules
  nsx_update_esg_fw:
    nsxmanager_spec: "{{ nsxmanager_spec }}"
    esg_name: 'dev-Esg01'
    firewall_ipsets:
      ipset: True
      inheritance: False
    firewall_default:
      only: True
      action: 'accept'
    firewall_rules:
      - name: 'rule123'
        loggingEnabled: 'false'
        matchTranslated: 'false'
        destination:
          exclude: 'false'
          ipAddress: '123.123.123.23'
        enabled: 'true'
        source:
          exclude: 'false'
          ipAddress: '123.123.234.5'
        action: 'accept'
        description: 'this is a fw rule'
    state: present
  register: esg_fw_results
  tags: esg_fw
'''

try:
    import inspect
    import logging
    from nsxramlclient.client import NsxClient
    HAS_CLIENTS = True
except ImportError:
    HAS_CLIENTS = False

LOG = logging.getLogger(__name__)
handler = logging.FileHandler('/var/log/chaperone/nsx_esg_fw.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
LOG.addHandler(handler)
LOG.setLevel(logging.DEBUG)

def log(message=None):
    func = inspect.currentframe().f_back.f_code
    msg="Method: {} Line Number: {} Message: {}".format(func.co_name, func.co_firstlineno, message)
    LOG.debug(msg)

class NsxEsgFirewall(object):
    """docstring for NxsEsgFirewall"""

    def __init__(self, module):
        super(NsxEsgFirewall, self).__init__()
        self.module = module
        self.edge_name = module.params['esg_name']
        self.nsx_spec = module.params['nsxmanager_spec']
        self.firewallrules = module.params['firewall_rules']
        self.ipsets = module.params['firewall_ipsets']
        self.client_session = self.nsx_sess()
        self.edge_id = None
        self.edge_params = None
        self.rules_not_present = []

    def nsx_sess(self):
        log("Getting NsxClient...")
        return NsxClient(self.nsx_spec['raml_file'],
                         self.nsx_spec['host'],
                         self.nsx_spec['user'],
                         self.nsx_spec['password'])

    def state_exit_unchanged(self):
        changed = False
        msg = "EXIT UNCHANGED"
        log("STATE: {} CHANGED: {} object_id: {}".format(msg, changed, self.edge_id))
        log("object_data: {}".format(self.edge_params))
        self.module.exit_json(changed=changed, msg=msg, object_id=self.edge_id, object_data=self.edge_params)

    def state_delete(self):
        changed = False
        msg = "DELETE"
        log("STATE: {} CHANGED: {} object_id: {}".format(msg, changed, self.edge_id))
        log("object_data: {}".format(self.edge_params))
        self.module.exit_json(changed=changed, msg=msg, object_id=self.edge_id, object_data=self.edge_params)

    def process_state(self):

        fw_states = {
            'absent': {
                'absent': self.state_exit_unchanged,
                'present': self.state_delete,
                'update_default': self.state_exit_unchanged
            },
            'present': {
                'present': self.state_exit_unchanged,
                'absent': self.update_fw_rules,
                'update_default': self.state_update_default_rule
            }
        }

        desired_state = self.module.params['state']
        log("DESIRED STATE --> {}".format(desired_state))

        current_state = self.check_state()
        log("CURRENT STATE --> {}".format(current_state))

        fw_states[desired_state][current_state]()

    def get_edge(self):
        all_edge = self.client_session.read_all_pages('nsxEdges', 'read')

        try:
            edge_params = [scope for scope in all_edge if scope['name'] == self.edge_name][0]
            edge_id = edge_params['objectId']
        except IndexError:
            edge_id, edge_params = None, None

        return edge_id, edge_params

    def edge_fw_state(self):

        fw_state = self.client_session.read('nsxEdgeFirewallConfig', uri_parameters={'edgeId': self.edge_id})['body']

        if fw_state['firewall']['enabled'] == 'false':
            return False
        elif fw_state['firewall']['enabled'] == 'true':
            return True
        else:
            return None

    def enable_esg_fw(self):
        firewall_body = self.client_session.read('nsxEdgeFirewallConfig', uri_parameters={'edgeId': self.edge_id})['body']
        firewall_body['firewall']['enabled'] = 'true'
        return self.client_session.update('nsxEdgeFirewallConfig', uri_parameters={'edgeId': self.edge_id}, request_body_dict=firewall_body)

    def update_fw_rules(self):
        fw_body = self.client_session.read('nsxEdgeFirewallConfig', uri_parameters={'edgeId': self.edge_id})['body']

        if self.ipsets['ipset']:
            new_rules_to_update = self.create_new_fw_rule_ipset()
            log("new rules to update --> {}".format(new_rules_to_update))
        else:
            new_rules_to_update = self.firewallrules
            log("new rules to update --> {}".format(new_rules_to_update))

        for fw_rule in new_rules_to_update:
            if fw_rule['name'] in self.rules_not_present:
                fw_body['firewall']['firewallRules']['firewallRule'].append(fw_rule)

        fw_body['firewall']['defaultPolicy']['action'] = self.module.params['firewall_default']['action']

        update_rules = self.client_session.update('nsxEdgeFirewallConfig', uri_parameters={'edgeId': self.edge_id}, request_body_dict=fw_body)

        log("UPDATE RULES --> {}".format(update_rules))
        self.module.exit_json(changed=True, updated_rules=str(update_rules))

    def get_esg_fw_rules(self):
        state = False

        fwdefaulttrules = ['highAvailability', 'firewall', 'default rule for ingress traffic']

        fw_rules = self.client_session.read('nsxEdgeFirewallConfig', uri_parameters={'edgeId': self.edge_id})['body']
        current_fw_rules = fw_rules['firewall']['firewallRules']['firewallRule']

        if not current_fw_rules:
            return state

        current_fw_rule_names = [v for n in current_fw_rules for k, v in n.iteritems() if k == 'name' and v not in fwdefaulttrules]
        log("Current fw rules present not default: {}".format(current_fw_rule_names))

        desired_rules_names = [j for fw in self.firewallrules for i, j in fw.iteritems() if i == 'name']
        log("Desired fw rules names: {}".format(desired_rules_names))

        for f in desired_rules_names:
            if f not in current_fw_rule_names:
                self.rules_not_present.append(f)

        log("List of fw rules not present: {}".format(self.rules_not_present))

        if not self.rules_not_present:
            state = True

        return state

    def get_default_fw_rule(self):
        state = False

        fw_body = self.client_session.read('nsxEdgeFirewallConfig', uri_parameters={'edgeId': self.edge_id})['body']

        if fw_body['firewall']['defaultPolicy']['action'] == self.module.params['firewall_default']['action']:
            state = True

        return state

    def state_update_default_rule(self):
        fw_body = self.client_session.read('nsxEdgeFirewallConfig', uri_parameters={'edgeId': self.edge_id})['body']
        fw_body['firewall']['defaultPolicy']['action'] = self.module.params['firewall_default']['action']
        update_rules = self.client_session.update('nsxEdgeFirewallConfig', uri_parameters={'edgeId': self.edge_id},
                                                  request_body_dict=fw_body)

        self.module.exit_json(changed=True, result=str(update_rules))

    def get_ipsets(self, sess, esg_id):
        ipsets = sess.read('ipsetList', uri_parameters={'scopeMoref': esg_id})

        try:
            ipset_esg_scope = [v['list']['ipset'] for k, v in ipsets.iteritems() if
                               k == 'body' and isinstance(v, dict) and isinstance(v['list']['ipset'], list)][0]
        except IndexError:
            ipset_esg_scope = None
        else:
            ipset_esg_scope = [i for i in ipset_esg_scope if i['scope']['id'] == esg_id]

        return ipset_esg_scope

    def create_ipset(self, ipset_data):

        if self.ipsets['inheritance'] == True:
            inheritance = 'True'
        elif self.ipsets['inheritance'] == False:
            inheritance = 'False'

        log('ip set values used --> {}'.format(ipset_data))

        ipset_dict = self.client_session.extract_resource_body_example('ipsetCreate', 'create')
        ipset_dict['ipset']['name'] = ipset_data['name']
        ipset_dict['ipset']['value'] = ipset_data['ip']
        ipset_dict['ipset']['inheritanceAllowed'] = inheritance

        new_ipset = self.client_session.create('ipsetCreate',
                                               uri_parameters={'scopeMoref': self.edge_id},
                                               request_body_dict=ipset_dict)

        log("new ipset id--> {}".format(new_ipset['objectId']))
        return new_ipset['objectId']

    def _ipset_data(self, fw_rule, source_attr):
        ipset_vals = {}
        ipset_vals['name'] = fw_rule['name'] + '_' + source_attr + '_ip_set'
        ipset_vals['ip'] = fw_rule[source_attr]['ipAddress']
        return ipset_vals

    def _replace_fw_rule_vals_ipset(self, fw_rule, source_attr):

        ipset_data = self._ipset_data(fw_rule, source_attr)
        ipset_id = self.create_ipset(ipset_data)

        for k, v in fw_rule.iteritems():
            if k == source_attr and isinstance(v, dict):
                for i, j in v.iteritems():
                    if i == 'ipAddress':
                        v['groupingObjectId'] = v[i]
                        del v[i]
                        v['groupingObjectId'] = ipset_id

        return fw_rule

    def create_new_fw_rule_ipset(self):

        fw_rules_to_create = []
        for fw_rule in self.firewallrules:

            if ('destination' in fw_rule) and ('source' in fw_rule):
                dest_rule = self._replace_fw_rule_vals_ipset(fw_rule, 'destination')
                source_rule = self._replace_fw_rule_vals_ipset(dest_rule, 'source')

                fw_rules_to_create.append(source_rule)

            if ('destination' in fw_rule) and ('source' not in fw_rule):
                dest_rule = self._replace_fw_rule_vals_ipset(fw_rule, 'destination')
                fw_rules_to_create.append(dest_rule)

            if ('source' in fw_rule) and ('destination' not in fw_rule):
                source_rule = self._replace_fw_rule_vals_ipset(fw_rule, 'source')
                fw_rules_to_create.append(source_rule)

        log("FW Rules to Create --> {}".format(fw_rules_to_create))
        return fw_rules_to_create

    def check_state(self):
        esg_data = self.get_edge()

        if not esg_data[0]:
            msg = "Failed to find esg: {}".format(self.edge_name)
            log(msg)
            self.module.fail_json(msg=msg)

        self.edge_id = esg_data[0]
        self.edge_params = esg_data[1]
        log("ESG ID--> {} ESG DATA--> {}".format(self.edge_id, self.edge_params))

        fw_enabled = self.edge_fw_state()
        log("ESG FW ENABLED --> {}".format(fw_enabled))

        if not fw_enabled:

            if self.module.params['state'] == 'absent':
                log("FW is Disabled Desired state is ABSENT")
                return 'absent'

            log("Firewall is disabled, ENABLING")
            self.enable_esg_fw()

        if self.module.params['firewall_default']['only']:
            if not self.get_default_fw_rule():
                return 'update_default'
            else:
                return 'present'

        fw_rules_present = self.get_esg_fw_rules()
        log("FW rules present --> {}".format(fw_rules_present))

        if not fw_rules_present:
            return 'absent'
        elif fw_rules_present:
            return 'present'



def main():

    argument_spec = dict(
        nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
        esg_name=dict(required=True, type='str'),
        firewall_ipsets=dict(type='dict', required=True),
        firewall_rules=dict(required=False, type='list'),
        firewall_default=dict(required=True, type='dict'),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_CLIENTS:
        module.fail_json(msg='Nsxramlclient is required')

    nef = NsxEsgFirewall(module)
    nef.process_state()

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
