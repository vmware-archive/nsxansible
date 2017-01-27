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
  - The M(nsx_edge_firewall) module is used to configure an NSX edge firewall (ESG or DLR). (Not to be confused with the distributed firewall). The module can be used to create, append, query, delete and reset firewall rules. Along with that the default firewall policy can also be set using this. 

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
    required: true
    default: null
    aliases: []
    choices: ["create", "append", "query", "delete", "set_default_action"]

  source:
    description:
      - The source dictionary containing multiple ip addresses, vnic group objects or ipsets. The ipAddress field can be specified as a list or space separated string
    required: false
    default: null
    aliases: []

  destination:
    description:
      - The destination dictionary containing multiple ip addresses, vnic group objects or ipsets. The ipAddress field can be specified as a list or space separated string
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

  description:
    description:
      - The description for the rule
    required: false
    default: null
    aliases: []

  application:
    description:
      - The application dictionary containing the application ID. This can also contain multiple 'service' blocks containing the 'protocol', 'sourcePort' and 'port' entities. The 'sourcePort' and 'port' fields can be specified as a list or as a space separated string
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
      - The list of rules to be given while using the 'create' mode. These specified rules will overwrite any existing rules for the given edge. The rules follow the same structure as specified in the API.
    required: false
    default: null
    type: list
    aliases: []

  global_config:
    description:
      - The global configuration settings to be given when the firewall is to be configured using the 'create' mode
    required: false
    default: null
    type: dict
    aliases: []

  default_action:
    description:
      - The default action to be used by the firewall. 
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
#We also modify the default firewall action and some parameters in the global config

- name: Add multiple firewall rules
      nsx_edge_firewall:
        nsxmanager_spec: 
          raml_file: "nsxraml/nsxvapi.raml"
          host: "nsxmanager.example.com"
          user: "admin"
          password: "l0ngPassw0rd!!"
        mode: "create"
        edge_name: "wdc04-0-ops-edge"
        global_config: 
          tcpPickOngoingConnections: true
          dropInvalidTraffic: false
          tcpTimeoutEstablished: 3600
          enableSynFloodProtection: true
        default_action: reject
        rules: 
          - name: SSH Restrict Interface
            action: deny
            destination: 
                ipAddress: 161.202.154.228 100.100.100.1 100.100.200.1 100.64.192.14 10.98.129.1 10.98.129.10
            application:
                service:
                  - protocol: TCP
                    port: 20 21 22 


#The 'append' mode : Appending a firewall rule to the given edge device
- name: Append a firewall rule
      nsx_edge_firewall:
        nsxmanager_spec: 
          raml_file: "nsxraml/nsxvapi.raml"
          host: "nsxmanager.example.com"
          user: "admin"
          password: "l0ngPassw0rd!!"
        mode: append
        edge_id: "edge-18"
        description: "Latest rule"
        name: "My Rule"
        action: "accept"
        source: 
            ipAddress:
                - 10.98.129.0/24
                - 10.98.0.0/23
                - 10.98.130.0/24
                - 10.98.128.0/24
        destination:
            vnicGroupId: vnic-index-0

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

#The 'reset' mode : Resetting an existing firewall configuration
#WARNING : Will remove all existing rules
- name: Reset the edge firewall
  hosts: localhost
  connection: local
  tasks:
    - name: Reset firewall config
      nsx_edge_firewall:
        nsxmanager_spec:
          raml_file: "nsxraml/nsxvapi.raml"
          host: "nsxmanager.example.com"
          user: "admin"
          password: "l0ngPassw0rd!!"
        mode: "reset"
        edge_id: "edge-1"

'''


##Global vars##
'''Resource body dict'''
create_api_resource_body = {'firewall': {'defaultPolicy': dict(),
                                         'enabled': None,
                                         'firewallRules': {'firewallRule': list() },
                                         'globalConfig': {
                                                           'dropInvalidTraffic': None,
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
                                                           'udpTimeout': None}
                                                       } }

append_api_resource_body = {'firewallRules': {'firewallRule': dict() } }

default_action_resource_body = {'firewallDefaultPolicy': dict()}


##Classes##

class Firewall(object):
    """Represents a firewall object. A firewall object is a combination of the global firewall config, multiple 'FirewallRule' objects and the default firewall action""" 
    def __init__(self, rules, global_config=None, default_action=None):
        self._rules = self._remove_duplicate(rules)
        self._global_config = _to_string(global_config)
        self._default_action = default_action
       

    def get_resource_body(self):
        """Fetch the resource body required for configuring the firewall"""
        resource_body = create_api_resource_body
        resource_body["firewall"]["defaultPolicy"]["action"] = self._default_action
        resource_body["firewall"]["globalConfig"] = self._global_config

        for rule in self._rules:
            resource_body["firewall"]["firewallRules"]["firewallRule"].append(rule.get_rule())

        return resource_body

    @staticmethod
    def _remove_duplicate(rules):
        """Removes duplicate firewall rules from the rules which are to be added"""
        hash_list = []
        filtered_rules = []

        for rule in rules:
            rule_hash = hash(rule)
            if rule_hash in hash_list:
                continue
            hash_list.append(rule_hash)
            filtered_rules.append(rule)
        return filtered_rules



class FirewallRule(object):
    """Represents a single firewall rule."""
    def __init__(self, rule):
        self._action = rule.get("action", None)
        self._name = rule.get("name", None)
        self._description = rule.get("description", None)
        self._source = rule.get("source", None)
        self._destination = rule.get("destination", None)
        self._application = rule.get("application", None)
        self._direction = rule.get("direction", None)
        self._services = self._format_services()
        self._format_addresses()

    def _format_addresses(self):
        """Formats the source and destination ipAddress fields to allow space separated inputs"""
        for field in (self._source, self._destination):
            if not field:
                continue

            ip_address = field.get("ipAddress", None)
            if not ip_address:
                continue

            if not isinstance(ip_address,list):
                ip_address = [ip_address]

            field["ipAddress"] = " ".join(ip_address).split()

    
    def _format_services(self):
        """Formats the services block by removing duplicate rules. Formatting also adds capability for space separated src/dst port entries. Also adds certain fields (like 'any') if some parameters (like 'port')  are empty. This helps in comparing existing rules with the rule to be added"""
        if self._application is None:
            return None

        services = self._application.get("service", None)
        if services is None:
            return services

        if isinstance(services, dict):
            services = [services]

        for service in services:
            if not service.get("protocol", None):
                service["protocol"] = "TCP"
            if not service.get("port", None):
                service["port"] = "any"
            if not service.get("sourcePort", None):
                service["sourcePort"] = "any"

            for field in ("port", "sourcePort"):
                ports = service[field]
                if not isinstance(ports, list):
                    ports = [ports]

                service[field] = " ".join(map(str,ports)).split()  

        self._application["service"] = services

        return services     
 
    
    
    def _get_hashable_entity(self, field, dict_keys_to_extract=[], extractor_algorithm=None):  
        """Given an object, extracts the part which needs to be hashed for comparison. For custom objects"""
        if extractor_algorithm:
            return extractor_algorithm(field)

        if isinstance(field, list):
            return ",".join(sorted(map(str,field)))
        elif isinstance(field, (str,int,bool)):
            return str(field)
        elif isinstance(field, dict):
            hash_list = []
            for entity in dict_keys_to_extract:
                value = field.get(entity, "")
                hash_list.append(self._get_hashable_entity(value))
            return "/".join(hash_list)
        else:
            return ""

    
    def _extract_services(self, services):
        """Custom extractor for services block"""
        if not services:
            return ""

        if isinstance(services, dict):
            services = [services]

        service_hash_list = []
        for service in sorted(services):
            service_hash_list.append(self._get_hashable_entity(service, ["protocol", "sourcePort", "port", "icmpType"]))
                
        return "/".join(service_hash_list)


    def get_rule(self):
        """Get the rule represented by this object"""
        return { "name":self._name, "action":self._action, "description":self._description, "direction":self._direction, "source":self._source, "destination":self._destination, "application":self._application }

    def __hash__(self):
        """Get the hash of the rule represented by this object"""
        name_hash_string = self._get_hashable_entity(self._name)
        action_hash_string = self._get_hashable_entity(self._action)
        description_hash_string = self._get_hashable_entity(self._description)

        source_hash_string = self._get_hashable_entity(self._source, ["ipAddress","vnicGroupId","groupingObjectId"])
        destination_hash_string = self._get_hashable_entity(self._destination, ["ipAddress","vnicGroupId","groupingObjectId"])
        application_id_hash_string = self._get_hashable_entity(self._application, ["applicationId"])

        service_hash_string = self._get_hashable_entity(self._services, extractor_algorithm=self._extract_services)
        direction_hash_string = self._get_hashable_entity(self._direction)

        hash_tuple = (name_hash_string, action_hash_string, description_hash_string, source_hash_string, destination_hash_string, application_id_hash_string, service_hash_string, direction_hash_string)

        return hash(hash_tuple)

    def __str__(self):
        return str(self.get_rule())
  
def _to_string(obj):
    """Recursively convert primitive objects to strings(as expected by the API)"""
    if obj is None:
        return obj

    primitive = (int, float, str, bool)
    if isinstance(obj, primitive):
        return str(obj)

    elif isinstance(obj, dict):
        for k in obj:
            obj[k] = _to_string(obj[k])
        return obj

    elif isinstance(obj, (list, tuple)):
        obj = list(map(_to_string, obj))
        return obj

    else:
        raise ValueError("caught unhandled object type: " + str(obj))

 

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
        mode=dict(required=True, choices=["create", "append", "query", "delete", "set_default_action", "reset"]),
        source=dict(required=False, type="dict"),
        destination=dict(required=False, type="dict"),
        action=dict(required=False, choices=["accept", "deny", "reject"]),
        name=dict(required=False),
        description=dict(required=False),
        application=dict(required=False, type="dict"),        
        rule_id=dict(required=False),
        direction=dict(required=False, choices=["in", "out"]),
        global_config=dict(required=False, type="dict"),
        rules=dict(required=False, type="list"),
        default_action=dict(required=False, choices=["accept", "deny", "reject"]),
    ), required_one_of=[["edge_name", "edge_id"]])

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
    name = module.params.get("name", None)
    rule_id = module.params.get("rule_id", None)
    application = module.params.get("application", None)
    source = module.params.get("source", None)
    destination = module.params.get("destination", None)
    description = module.params.get("description", None)
    direction = module.params.get("direction", None)
    rules = module.params.get("rules", None)
    global_config = module.params.get("global_config", None)
    default_action = module.params.get("default_action", None)

    if mode == "create":
        #'create' mode:
        #   1)Create a Firewall object out of the given rules,global_config and default_action
        #   2)Get the resource body to be sent
        #   3)Send the resource body to the NSX Manager
        if not rules:
            module.fail_json(msg="The parameter 'rules' is required in order to create the firewall rules")

        firewall_rules = []
        for rule in rules:
            firewall_rules.append(FirewallRule(rule))
  
        F = Firewall(firewall_rules, global_config, default_action)
        resource_body = F.get_resource_body()


        resp = client_session.update("nsxEdgeFirewallConfig", uri_parameters={"edgeId": edge_id},
                                     request_body_dict=resource_body)
        if resp["status"] == 204:
            module.exit_json(changed=True, msg="Successfully created the rules for the edge with ID %s" % (edge_id))
        else:
            module.fail_json(msg="The resource could not be created")


    elif mode == "append":
        #'append' mode:
        #   1)Check if the rule to be added already exists in the firewall
        #   2)If yes, exit
        #   3)If no, create the resource body and send the request to the NSX Manager

        if not action:
            module.fail_json(msg="The 'action' attribute is mandatory while appending a new rule")


        rule_to_be_added = FirewallRule({"name":name, "action":action, "description":description, "source":source, "destination":destination, "application":application, "direction":direction})

        current_rules = [FirewallRule(rule) for rule in query_firewall_rules(client_session, edge_id)]
        current_hashes = [hash(rule) for rule in current_rules]
        if hash(rule_to_be_added) in current_hashes:
            module.exit_json(changed=False, msg="The given rule already exists in the firewall")

        resource_body = append_api_resource_body
        resource_body["firewallRules"]["firewallRule"] = rule_to_be_added.get_rule() 

        resp = client_session.create("firewallRules", uri_parameters={"edgeId": edge_id},
                                     request_body_dict=resource_body)
        if resp["status"] == 201:
            module.exit_json(changed=True, meta={"ruleId": resp["objectId"]})
        else:
            module.fail_json(msg="The resource could not be created")

    elif mode == "query":
        #'query' mode:
        #   1)Query the rules existing for the given edge
        #   2)Display the results (requires <result>.split("\n") in Ansible as Ansible does not support printing newlines
        rules = query_firewall_rules(client_session, edge_id)
        print_str = display_firewall_rules(rules)

        module.exit_json(changed=False, meta={"output": print_str})

    elif mode == "delete":
        #'delete' mode:
        #   - Delete the rule with the given rule_id
        if not rule_id:
            module.fail_json(msg="The parameter 'rule_id' is required to delete a given rule")
        resp = client_session.delete("firewallRule", uri_parameters={"ruleId": rule_id, "edgeId": edge_id})
        if resp["status"] == 204:
            module.exit_json(changed=True, msg="Rule with the ID %s successfully deleted" % (rule_id))
        else:
            module.fail_json(msg="Could not delete the rule with ID %s. Make sure that the rule exists" % (rule_id))

    elif mode == "set_default_action":
        #'set_default_action' mode:
        #   - Sets the default action for the firewall(can be 'accept', 'deny' or 'reject')
        if not default_action:
            module.fail_json(msg="The parameter 'default_action' is required to set the default action")

        resource_body = default_action_resource_body
        resource_body["firewallDefaultPolicy"]["action"] = default_action

        resp = client_session.update("defaultFirewallPolicy", uri_parameters={"edgeId": edge_id},
                                     request_body_dict=resource_body)
        if resp["status"] == 204:
            module.exit_json(changed=True, msg="Successfully updated the firewall config")
        else:
            module.fail_json(msg="The resource could not be updated")

    elif mode == "reset":
        #'reset' mode:
        #   - Resets the firewall by deleting all the existing rules
        resp = client_session.delete("nsxEdgeFirewallConfig",  uri_parameters={"edgeId": edge_id})
        if resp["status"] == 204:
            module.exit_json(msg="Successfully reset the firewall configuration for the edge with ID %s" %(edge_id), changed=True)
        else:
            module.fail_json(msg="Could not reset the firewall rules for the edge with ID %s" %(edge_id))



from ansible.module_utils.basic import *
from nsxramlclient.client import NsxClient

if __name__ == "__main__":
    main()
