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
module: nsx_service

short_description: Create/Delete an NSX service

description:
 - The M(nsx_service) module is used to create or delete an NSX service.

options:
  nsxmanager_spec:
    description:
      - A dictionary accepting the parameters required to connect to the NSX manager
    required: true
    default: null
    aliases: []
  description:
    description:
      - The description string for the service.
    required: false
    default: null
    aliases: []
  name:
    description:
      - The name of the service.
    required: false
    default: null
    aliases: []
  application_protocol:
    description:
      - The application protocol for the service.
    required: false
    default: null
    aliases: []
  port_range:
    description:
      - The port number range for the service.
    required: false
    default: null
    aliases: []
  application_id:
    description:
      - The application ID of the application to be removed. Only required for service deletion.
    required: false
    default: null
    aliases: []
  state:
    description:
      - Specifies whether the service is to be created or deleted
    required: false
    default: present
    aliases: []
    choices: ["present", "absent"]

author:
  - "VMware"  

notes:
  - The module requires the nsxramlclient python module as well as the NSX RAML specification document. For further details please check out U(https://github.com/vmware/nsxramlclient) and U(https://github.com/vmware/nsxraml)  
'''

EXAMPLES = '''
#Creating a service
- name: Create a service
  nsx_service:
    nsxmanager_spec: 
      raml_file: "nsxraml/nsxvapi.raml"
      host: "nsxmanager.example.com"
      user: "admin"
      password: "l0ngPassw0rd!!"
    state: present
    name: app_tcp_test
    application_protocol: TCP
    port_range: 20,21,22,80,443

#Deleting a service
- name: Delete a service
  nsx_service:
    nsxmanager_spec: 
      raml_file: "nsxraml/nsxvapi.raml"
      host: "nsxmanager.example.com"
      user: "admin"
      password: "l0ngPassw0rd!!"
    state: absent
    application_id: application-18

#Query for all the services and display them in a human readable format
- name: Query all existing services 
  nsx_service:
    nsxmanager_spec: 
      raml_file: "nsxraml/nsxvapi.raml"
      host: "nsxmanager.example.com"
      user: "admin"
      password: "l0ngPassw0rd!!"
    state: query
    register: result
    
- debug: var=result.msg.split("\n")


#Querying for a specific service 
- name: Query if a service for SSH exists
  nsx_service:
    nsxmanager_spec: 
      raml_file: "nsxraml/nsxvapi.raml"
      host: "nsxmanager.example.com"
      user: "admin"
      password: "l0ngPassw0rd!!"
    state: query
    port_range: 22
  register: result_ssh

#Display the port_range to application_id mapping for the above
- debug: var=result_ssh.answer
   
#Conditionally creating a service listening on port 8080 
#1)Check if the service actually exists
#2)If yes, get the applicaiton ID for the same
#3)If no, create a new service and get the application ID 

- name: Query if a service for port 8080 exists
  nsx_service:
    nsxmanager_spec: 
      raml_file: "nsxraml/nsxvapi.raml"
      host: "nsxmanager.example.com"
      user: "admin"
      password: "l0ngPassw0rd!!"
    state: query
    port_range: 8080
  register: result_8080


- name: If the service above exists, get the application ID for the service
  set_fact: "app_id_8080={{result_8080.answer.application_id}}"
  when: result_8080.answer

- name: If the service for 8080 does not exist, create a new service for the same
  nsx_service:
    nsxmanager_spec: 
      raml_file: "nsxraml/nsxvapi.raml"
      host: "nsxmanager.example.com"
      user: "admin"
      password: "l0ngPassw0rd!!"
    state: present
    name: app_8080
    application_protocol: TCP
    port_range: 8080
  register: result
  when: not result_8080.answer

- name: If the service for 8080 does not exist, get the application ID for the newly created service above
  set_fact: "app_id_8080={{result.meta.objectId}}"
  when: not result_8080.answer

- name: Display the application ID of the service with port 8080
  debug: msg="The application ID for the service is {{app_id_8080}}"

'''


def sort_by_port(port_range):
    """Sorts input port range"""
    try:
        return int(port_range)
    except ValueError:
        try:
            return int(port_range.split("-")[0])
        except ValueError:
            return 65535


def format_output(result):
    """Formats the port range to application ID mapping"""
    print_str = "%-20s %-20s\n" % ("PORT RANGE", "APPLICATION ID")

    for port_range in sorted(result, key=sort_by_port):
        print_str += "%-20s %-20s\n" % (port_range, result[port_range])

    return print_str


def format_port_range(port_range):
    """Formats the given port range string by re-arranging the given ports in ascending order"""
    ports = port_range.split(",")
    sorted_ports = sorted(ports, key=sort_by_port)
    return ",".join(sorted_ports)


def query_data(resp):
    """Queries the NSX manager and retrieves/stores the mappings required to translate between port numbers and application IDs"""
    global port_range_to_application_id, application_id_to_port_range
    port_range_to_application_id = {}
    application_id_to_port_range = {}

    for application in resp["body"]["list"]["application"]:
        application_id = application.get("objectId", None)
        if application.get("element", None):
            port_range = application["element"].get("value", None)
        if application_id and port_range:
            port_range = format_port_range(port_range)
            port_range_to_application_id[port_range] = application_id
            application_id_to_port_range[application_id] = port_range


def parse_data(application_id, port_range):
    """Parses the data retrieved by the NSX manager and returns the status of the query along with the display string"""
    if application_id and port_range:
        port_range = format_port_range(port_range)
        if port_range_to_application_id.get(port_range, None) == application_id:
            print_str = "The given application ID matches the supplied port range"
            answer = {"port_range": port_range, "application_id": application_id}
        else:
            print_str = "The given application ID does not match any existing port range"
            answer = None

    elif port_range:
        port_range = format_port_range(port_range)
        application_id = port_range_to_application_id.get(port_range, None)
        if application_id:
            print_str = "The port_range %s maps to the application with ID %s" % (port_range, application_id)
            answer = {"port_range": port_range, "application_id": application_id}
        else:
            print_str = "The given port range does not match any existing application"
            answer = None

    elif application_id:
        port_range = application_id_to_port_range.get(application_id, None)
        if port_range:
            print_str = "The application with ID %s maps to the port range %s" % (application_id, port_range)
            answer = {"port_range": port_range, "application_id": application_id}
        else:
            print_str = "The given application ID does not match any existing port range"
            answer = None

    else:
        answer = print_str = format_output(port_range_to_application_id)

    return (print_str, answer)


def main():
    """main function : Initializes the Ansible module params and makes the required API calls to create/delete/query a service using the NSX RAML specification and nsxramlclient module"""
    module = AnsibleModule(argument_spec=dict(
        nsxmanager_spec=dict(required=True, type="dict"),
        description=dict(required=False),
        name=dict(required=False),
        application_protocol=dict(required=False),
        port_range=dict(required=False),
        application_id=dict(required=False),
        state=dict(required=False, choices=["present", "absent", "query"], default="present"),
    ))

    from nsxramlclient.client import NsxClient

    client_session = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                               module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'])

    application_id = module.params.get("application_id", None)
    port_range = module.params.get("port_range", None)
    name = module.params.get("name", None)
    application_protocol = module.params.get("application_protocol", None)
    description = module.params.get("description", None)

    if module.params["state"] == "present":
        if not name:
            module.fail_json(msg="The parameter 'name' is required to create a service")

        resource_body = client_session.extract_resource_body_example("servicesScope", "create")
        application = resource_body["application"]
        application["description"] = description

        element = application["element"]
        element["applicationProtocol"] = application_protocol
        element["value"] = port_range
        application["name"] = name
        application["inheritanceAllowed"] = "true"

        resp = client_session.create("servicesScope", uri_parameters={"scopeId": "globalroot-0"},
                                     request_body_dict=resource_body)

        if resp["status"] == 201:
            object_id = resp["objectId"]
            module.exit_json(changed=True, msg="Successfully created object with object ID %s" % (object_id),
                             meta={"objectId": object_id})
        else:
            module.fail_json(msg="The resource could not be created")

    elif module.params["state"] == "absent":
        if not application_id:
            module.fail_json(msg="Required parameter : 'Application Id' is missing")
        resp = client_session.delete("service", uri_parameters={"applicationId": application_id})
        if resp["status"] == 200:
            module.exit_json(changed=True, msg="Successfully deleted the service with ID %s" % (application_id))
        else:
            module.fail_json(msg="Could not remove the given resource")

    elif module.params["state"] == "query":
        resp = client_session.read("servicesScopeGet", uri_parameters={"scopeId": "globalroot-0"})
        query_data(resp)
        print_str, answer = parse_data(application_id, port_range)
        module.exit_json(changed=False, msg=print_str, answer=answer)


from ansible.module_utils.basic import *

main()
