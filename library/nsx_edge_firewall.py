#!/usr/bin/python
# coding=utf-8
#
# Copyright � 2016 VMware, Inc. All Rights Reserved.
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
---

module: nsx_edge_firewall

short_description: Configure edge firewall rules

description:
  - The M(nsx_edge_firewall) module is used to configure an NSX edge firewall (ESG or DLR). (Not to be confused with the distributed firewall). The module can be used to create, append, query and delete firewall rules. Along with that the default firewall policy can also be set using this. 

options:

  nsxmanager_spec:
    description:
      - A dictionary accepting the parameters required to connect to the NSX manager
    required: true
    default: null
    aliases: []

  edge_name:
    description:
      - The name of the edge where the firewall will be configured. This parameter is not required if edge_id is given.
    required: true
    default: null
    aliases: []

  edge_id:
    description:
      - The ID of the edge where the firewall will be configured. This parameter is not required if edge_name is given.
    required: true
    default: null
    aliases: []

  mode:
    description:
      - Specifies the mode of operation. 
    required: false
    default: null
    aliases: []
    choices: ["create", "append", "query", "delete", "set_default_action"]

  source_ip_address:
    description:
      - The source IP address that will be matched
    required: false
    default: null
    aliases: []

  destination_ip_address:
    description:
      - The destination IP address that will be matched
    required: false
    default: null
    aliases: []

  action:
    description:
      - The action to be taken if the rule gets matched
    required: true
    default: null
    aliases: []
    choices: ["accept", "deny", "reject"]

  name:
    description:
      - The name of the rule
    required: false
    default: null
    aliases: []

  ruletag:
    description:
      - The rule-tag to be added for the rule
    required: false
    default: null
    aliases: []

  description:
    description:
      - The description for the rule
    required: false
    default: null
    aliases: []

  application_id:
    description:
      - The application ID to be added for the rule. An application ID maps to a service and is used to specify port number ranges
    required: false
    default: null
    aliases: []

  rule_id:
    description:
      - The rule ID to be used while deleting a given rule. Only required for the 'delete' mode
    required: false
    default: null
    aliases: []

  direction:
    description:
      - The direction of traffic to be considered while filtering
    choices: [ "in", "out"]
    default: "any"
    required: false
    default: null
    aliases: []

  rules:
    description:
      - The list of rules to be given while using the 'create' mode. These specified rules will overwrite any existing rules for the given edge
    required: false
    default: null
    aliases: []

  default_action:
    description:
      - The default action to be used by the firewall. This option is required if the 'set_default_action' mode is used
    required: false
    default: null
    aliases: []
    choices: [ "accept", "deny" , "reject"]

author:
  - "VMware"  

notes:
  - The module requires the nsxramlclient python module as well as the NSX RAML specification document. For further details please check out U(https://github.com/vmware/nsxramlclient) and U(https://github.com/vmware/nsxraml)  

'''

EXAMPLES = '''
#The 'create' mode : Adding multiple firewall rules for the given edge device. This will overwrite the existing firewall config.
- name: Add multiple firewall rules
      nsx_edge_firewall:
        nsxmanager_spec: 
          raml_file: "nsxraml/nsxvapi.raml"
          host: "nsxmanager.example.com"
          user: "admin"
          password: "l0ngPassw0rd!!"
        mode: "create"
        edge_name: "wdc04-0-ops-edge"
        rules: 
            - action: accept
              destination_ip_address: 10.0.0.0/24
              name: allow_ssh
              description: Allow all SSH requests to 10.0.0.0/24
              application_id: "application-18"
            - action: accept
              source_ip_address: 172.16.0.0/12
              name: allow_dns_dhcp
              description: Allow all DNS/DHCP requests from 172.16.0.0/12
              application_id: "application-18"

#The 'append' mode : Appending a firewall rule to the given edge device
- name: Append a firewall rule
      nsx_edge_firewall:
        nsxmanager_spec: 
          raml_file: "nsxraml/nsxvapi.raml"
          host: "nsxmanager.example.com"
          user: "admin"
          password: "l0ngPassw0rd!!"
        mode: append
        edge_name: "wdc04-0-ops-edge"
        description: "Latest rule"
        name: "My Rule"
        action: "accept"
        source_ip_address: "18.1.11.0/24"
        destination_ip_address: "8.11.11.111"
        application_id: dns_application

#The 'query' mode : Querying all the firewall rules for an edge
- name: Query all the firewall rules for an edge
      nsx_edge_firewall:
        nsxmanager_spec: 
          raml_file: "nsxraml/nsxvapi.raml"
          host: "nsxmanager.example.com"
          user: "admin"
          password: "l0ngPassw0rd!!"
        edge_id: "edge-8"
        mode: query


#The 'delete' mode : Deleting a firewall rule with the given rule ID
- name: Delete a firewall rule
      nsx_edge_firewall:
        nsxmanager_spec: 
          raml_file: "nsxraml/nsxvapi.raml"
          host: "nsxmanager.example.com"
          user: "admin"
          password: "l0ngPassw0rd!!"
        mode: delete
        edge_id: "edge-8"
        rule_id: 181110

#The 'set_default_action' mode : Setting the default firewall action for an edge
- name: Set default firewall action for an edge firewall
      nsx_edge_firewall:
        nsxmanager_spec: 
          raml_file: "nsxraml/nsxvapi.raml"
          host: "nsxmanager.example.com"
          user: "admin"
          password: "l0ngPassw0rd!!"
        default_action: "accept"
        edge_name: "wdc04-0-ops-edge"
        mode: "set_default_action"
'''

'''Defining the resource bodies'''
create_api_resource_body = {'firewall': {'defaultPolicy': {'action': None, 'loggingEnabled': None},
                                         'enabled': None,
                                         'firewallRules': {'firewallRule': [{'action': None,
                                                                             'application': {'applicationId': None,
                                                                                             'service': {'port': None,
                                                                                                         'protocol': None,
                                                                                                         'sourcePort': None}},
                                                                             'description': None,
                                                                             'destination': {'groupingObjectId': [None,
                                                                                                                  None],
                                                                                             'ipAddress': None,
                                                                                             'vnicGroupId': None},
                                                                             'direction': None,
                                                                             'enabled': None,
                                                                             'loggingEnabled': None,
                                                                             'matchTranslated': None,
                                                                             'name': None,
                                                                             'ruleTag': None,
                                                                             'source': {'groupingObjectId': None,
                                                                                        'ipAddress': None,
                                                                                        'vnicGroupId': None}},
                                                                            {'action': None,
                                                                             'application': {'applicationId': None,
                                                                                             'service': {'port': None,
                                                                                                         'protocol': None,
                                                                                                         'sourcePort': None}},
                                                                             'description': None,
                                                                             'destination': {'groupingObjectId': [None,
                                                                                                                  None],
                                                                                             'ipAddress': None,
                                                                                             'vnicGroupId': None},
                                                                             'direction': None,
                                                                             'enabled': None,
                                                                             'loggingEnabled': None,
                                                                             'matchTranslated': None,
                                                                             'name': None,
                                                                             'ruleTag': None,
                                                                             'source': {'groupingObjectId': None,
                                                                                        'ipAddress': None,
                                                                                        'vnicGroupId': None}}]},
                                         'globalConfig': {'dropInvalidTraffic': None,
                                                          'icmp6Timeout': None,
                                                          'icmpTimeout': None,
                                                          'ipGenericTimeout': None,
                                                          'logInvalidTraffic': None,
                                                          'tcpAllowOutOfWindowPackets': None,
                                                          'tcpPickOngoingConnections': None,
                                                          'tcpSendResetForClosedVsePorts': None,
                                                          'tcpTimeoutClose': None,
                                                          'tcpTimeoutEstablished': None,
                                                          'tcpTimeoutOpen': None,
                                                          'udpTimeout': None}}}

append_api_resource_body = {'firewallRules': {'firewallRule': {'action': None,
                                                               'application': {'applicationId': None},
                                                               'description': None,
                                                               'destination': {'ipAddress': None},
                                                               'direction': None,
                                                               'enabled': None,
                                                               'loggingEnabled': None,
                                                               'matchTranslated': None,
                                                               'name': None,
                                                               'ruleTag': None,
                                                               'source': {'ipAddress': None}}}}

delete_api_resource_body = {'firewallDefaultPolicy': {'action': None, 'loggingEnabled': None}}


def get_current_hash(rules):
    """
      Input : Currently existing firewall rules for the edge ([rule1,rule2,rule3,...])
      Output : MD5 hash list of specific fields ([MD5(rule1["field1"]+rule1["field2"]+..), MD5(rule2["field1"]+rule2["field2"]+..)])

      This function is used for the easy comparison of the existing rules with the rule to be appended to prevent duplicate rule addition
    """

    rule_hash_list = []
    for rule in rules:

        action = rule.get("action", None)
        source = rule.get("source", None)
        destination = rule.get("destination", None)
        name = rule.get("name", "")
        application = rule.get("application", None)

        if source:
            source_ip_address = source.get("ipAddress", "")
        else:
            source_ip_address = ""

        if destination:
            destination_ip_address = destination.get("ipAddress", "")
        else:
            destination_ip_address = ""

        if application:
            application_id = application.get("applicationId", None)
            if not application_id:
                application_id = ""
        else:
            application_id = ""
        m = hashlib.md5()
        m.update(name + action + source_ip_address + destination_ip_address + application_id)
        digest = m.digest()
        rule_hash_list.append(digest)

    return rule_hash_list


def query_firewall_rules(client_session, edge_id):
    """ Queries the edge for the list of currently existing firewall rules"""
    resp = client_session.read("nsxEdgeFirewallConfig", uri_parameters={"edgeId": edge_id})
    return resp["body"]["firewall"]["firewallRules"]["firewallRule"]


def get_edge_id(client_session, edge_name):
    """Returns the edge_id for a given edge_name"""
    resp = client_session.read("nsxEdges")
    edges = resp["body"]["pagedEdgeList"]["edgePage"]["edgeSummary"]

    if not isinstance(edges, list):
        edges = [edges]
    for edge in edges:
        if edge["name"] == edge_name:
            return edge["id"]
    return None


def remove_duplicates(rules):
    """Removes any duplicate rules that the user supplies while using the 'create' mode of the module"""
    hash_list = []
    filtered_rules = []

    for rule in rules:

        hashed_rule = get_current_hash([rule])
        if hashed_rule[0] in hash_list:
            continue

        hash_list.append(hashed_rule[0])
        filtered_rules.append(rule)

    return filtered_rules


def format_rules(rules):
    """Converts the input rules to the form recognized by the API. The input rules to be added to the firewall are read from a YAML file."""

    for rule in rules:

        source_ip_address = rule.get("source_ip_address", None)
        destination_ip_address = rule.get("destination_ip_address", None)
        application_id = rule.get("application_id", None)

        if (not source_ip_address) and (not destination_ip_address) and (not application_id):
            continue

        if source_ip_address:
            source_block = {}
            source_block["ipAddress"] = source_ip_address

            rule.pop("source_ip_address")
            rule["source"] = source_block

        if destination_ip_address:
            destination_block = {}
            destination_block["ipAddress"] = destination_ip_address

            rule.pop("destination_ip_address")
            rule["destination"] = destination_block

        if application_id:
            application_block = {}
            application_block["applicationId"] = application_id

            rule.pop("application_id")
            rule["application"] = application_block

    return rules


def display_firewall_rules(rules):
    """ Displays the firewall rules in human readable format when the 'query' mode is used"""
    print_str = ""
    for rule in rules:
        print_str += "-" * 100

        rule_id = rule["id"]
        rule_name = rule.get("name", "")

        print_str += "\n%-20s %-40s" % ("RULE ID", rule_id)
        print_str += "\n%-20s %-40s" % ("RULE NAME", rule_name)

        source = rule.get("source", None)

        if source:
            print_str += "\n%-20s %-40s" % ("SOURCE", source)
        else:
            print_str += "\n%-20s %-40s" % ("SOURCE", "ANY")

        destination = rule.get("destination", None)
        if destination:
            print_str += "\n%-20s %-40s" % ("DESTINATION", destination)
        else:
            print_str += "\n%-20s %-40s" % ("DESTINATION", "ANY")

        application = rule.get("application", None)
        if application:
            print_str += "\n%-20s %-40s" % ("APPLICATION", application)
        else:
            print_str += "\n%-20s %-40s" % ("APPLICATION", "ANY")

        action = rule["action"]
        print_str += "\n%-20s %-40s" % ("ACTION", action)

        description = rule.get("description", "")
        print_str += "\n%-20s %-40s" % ("DESCRIPTION", description)

        print_str += "\n" + "-" * 100
        print_str += "\n\n"

    return print_str


def main():
    """main function:
         Accept arguments from Ansible
         Create an nsxramlclient session
         Depending on the mode of operation call the specific function
    """
    module = AnsibleModule(argument_spec=
    dict(
        nsxmanager_spec=dict(required=True, type="dict"),
        edge_name=dict(required=False),
        edge_id=dict(required=False),
        mode=dict(required=True, choices=["create", "append", "query", "delete", "set_default_action"]),
        source_ip_address=dict(required=False),
        destination_ip_address=dict(required=False),
        action=dict(required=False, choices=["accept", "deny", "reject"]),
        name=dict(required=False),
        ruletag=dict(required=False),
        description=dict(required=False),
        application_id=dict(required=False),
        rule_id=dict(required=False),
        direction=dict(required=False, choices=["in", "out"]),
        rules=dict(required=False, type="list"),
        default_action=dict(required=False, choices=["accept", "deny", "reject"]),
    ), required_one_of=[["edge_name", "edge_id"]])

    from nsxramlclient.client import NsxClient

    try:
        client_session = NsxClient(module.params['nsxmanager_spec']['raml_file'],
                                   module.params['nsxmanager_spec']['host'],
                                   module.params['nsxmanager_spec']['user'],
                                   module.params['nsxmanager_spec']['password'])
    except:
        module.fail_json(msg="Could not connect to the NSX manager")

    edge_name = module.params.get("edge_name", None)
    if not edge_name:
        edge_id = module.params["edge_id"]
    else:
        edge_id = get_edge_id(client_session, edge_name)
        if not edge_id:
            module.fail_json(msg="The edge with the name %s does not exist." % (edge_name))

    mode = module.params["mode"]
    action = module.params.get("action", None)
    rule_name = module.params.get("name", None)
    rule_id = module.params.get("rule_id", None)
    application_id = module.params.get("application_id", None)
    source_ip_address = module.params.get("source_ip_address", None)
    destination_ip_address = module.params.get("destination_ip_address", None)
    ruletag = module.params.get("ruletag", None)
    description = module.params.get("description", None)
    direction = module.params.get("direction", None)
    rules = module.params.get("rules", None)
    default_action = module.params.get("default_action", None)

    if mode == "create":
        if not rules:
            module.fail_json(msg="The parameter 'rules' is required in order to create the firewall rules")

        rules = format_rules(rules)
        rules = remove_duplicates(rules)

        resource_body = create_api_resource_body

        resource_body["firewall"]["firewallRules"]["firewallRule"] = rules

        resp = client_session.update("nsxEdgeFirewallConfig", uri_parameters={"edgeId": edge_id},
                                     request_body_dict=resource_body)
        if resp["status"] == 204:
            module.exit_json(changed=True, msg="Successfully created the rules for the edge with ID %s" % (edge_id))
        else:
            module.fail_json(msg="The resource could not be created")


    elif mode == "append":

        if not action:
            module.fail_json(msg="The 'action' attribute is mandatory while appending a new rule")

        source_ip_address_hash = source_ip_address if source_ip_address else ""
        destination_ip_address_hash = destination_ip_address if destination_ip_address else ""
        rule_name_hash = rule_name if rule_name else ""
        application_id_hash = application_id if application_id else ""

        m = hashlib.md5()
        m.update(rule_name_hash + action + source_ip_address_hash + destination_ip_address_hash + application_id_hash)
        md5_hash = m.digest()

        rules = query_firewall_rules(client_session, edge_id)
        current_hashes = get_current_hash(rules)

        if md5_hash in current_hashes:
            module.exit_json(changed=False, msg="The given rule already exists")

        resource_body = append_api_resource_body

        firewall_rules = resource_body["firewallRules"]["firewallRule"]
        firewall_rules["action"] = action

        firewall_rules["name"] = rule_name

        application = firewall_rules["application"]
        application["applicationId"] = application_id

        firewall_rules["application"]["applicationId"] = application_id

        firewall_rules["ruleTag"] = ruletag
        firewall_rules["description"] = description
        firewall_rules["direction"] = direction

        source = firewall_rules["source"]
        source["ipAddress"] = source_ip_address

        destination = firewall_rules["destination"]
        destination["ipAddress"] = destination_ip_address

        resp = client_session.create("firewallRules", uri_parameters={"edgeId": edge_id},
                                     request_body_dict=resource_body)
        if resp["status"] == 201:
            module.exit_json(changed=True, meta={"ruleId": resp["objectId"]})
        else:
            module.fail_json(msg="The resource could not be created")

    elif mode == "query":
        rules = query_firewall_rules(client_session, edge_id)
        print_str = display_firewall_rules(rules)

        module.exit_json(changed=False, meta={"output": print_str})

    elif mode == "delete":
        if not rule_id:
            module.fail_json(msg="The parameter 'rule_id' is required to delete a given rule")
        resp = client_session.delete("firewallRule", uri_parameters={"ruleId": rule_id, "edgeId": edge_id})
        if resp["status"] == 204:
            module.exit_json(changed=True, msg="Rule with the ID %s successfully deleted" % (rule_id))
        else:
            module.fail_json(msg="Could not delete the rule with ID %s. Make sure that the rule exists" % (rule_id))

    elif mode == "set_default_action":
        if not default_action:
            module.fail_json(msg="The parameter 'default_action' is required to set the default action")

        resource_body = delete_api_resource_body
        resource_body["firewallDefaultPolicy"]["action"] = default_action

        resp = client_session.update("defaultFirewallPolicy", uri_parameters={"edgeId": edge_id},
                                     request_body_dict=resource_body)
        if resp["status"] == 204:
            module.exit_json(changed=True, msg="Successfully updated the firewall config")
        else:
            module.fail_json(msg="The resource could not be updated")


import hashlib
from ansible.module_utils.basic import *

main()
