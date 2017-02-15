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

module: nsx_loadbalancer

short_description: Configure NSX loadbalancer

description:
  - The M(nsx_loadbalancer) module is used to configure the NSX loadbalancer. This involves the configuration of global parameters, application profiles, application rules, monitors, server pools and virtual servers. These objects are created in a specific order and tied together to create the full load balancer configuration. 

options:

  nsxmanager_spec:
    description:
      - A dictionary accepting the parameters required to connect to the NSX manager
    required: true
    default: null
    aliases: []

  edge_name:
    description:
      - The name of the edge where the loadbalancer will be configured. This parameter is not required if edge_id is given.
    required: true
    default: null
    aliases: []

  edge_id:
    description:
      - The ID of the edge where the loadbalancer will be configured. This parameter is not required if edge_name is given.
    required: true
    default: null
    aliases: []

  configuration:
    description:
      - The loadbalancer configuration to be applied. This will overwrite any existing configuration.
    required: true
    default: null
    aliases: []

author:
  - "VMware"

notes:
    - The module requires the nsxramlclient python module as well as the NSX RAML specification document. For further details please check out U(https://github.com/vmware/nsxramlclient) and U(https://github.com/vmware/nsxraml)
    - All boolean variables to be passed as parameters will have to be quoted as the NSX API can only recognize boolean variables in string format(quoted).   
'''

                  
class BaseObject(object):
    """The parent class for the various loadbalancer objects""" 

    RAML_OBJECT_NAME = None
    MAPPING = dict()
    OBJECT_NAME = None

    def __init__(self, config):
        self._config = config
        self._request_body_dict = self._get_request_body_dict()
        self._object_id = self._create_object()
       
    def _get_request_body_dict(self):
        return { self.__class__.OBJECT_NAME:self._config }
        

    def _create_object(self):
        resp = client_session.create(self.RAML_OBJECT_NAME, uri_parameters = {"edgeId":edge_id}, request_body_dict = self._request_body_dict)
        if resp["status"] == 201:
            object_id = resp["objectId"]
            object_name = self._config.get("name", None)
            self.__class__.MAPPING[object_name] = object_id
            return object_id
        else:
            return None

    @staticmethod
    def _format_config(config, new_entries, to_pop):
        config.update(new_entries)
        for item in to_pop:
            config.pop(item, None)
        return config
    
    
    def get_id(self):
        return self._object_id   

    def get_mapping(self):
        return self.__class__.MAPPING
    
    

class ApplicationProfile(BaseObject):
    """Class representing an application profile"""
    RAML_OBJECT_NAME = "applicationProfiles"
    MAPPING = dict()
    OBJECT_NAME = "applicationProfile"

    def __init__(self, config):
        BaseObject.__init__(self, config)
       

class ApplicationRule(BaseObject):
    """Class representing an application rule"""
    RAML_OBJECT_NAME = "appRules"
    OBJECT_NAME = "applicationRule"
    MAPPING = dict()
    

    def __init__(self, config):
        BaseObject.__init__(self, config)

                        

class Monitor(BaseObject):
    """Class representing a loadbalancer monitor"""
    RAML_OBJECT_NAME = "lbMonitors"
    OBJECT_NAME = "monitor"
    MAPPING = dict()
    
    def __init__(self, config):
        BaseObject.__init__(self, config)
 

class Pool(BaseObject):
    """Class representing the backend server pool"""
    RAML_OBJECT_NAME = "pools"
    OBJECT_NAME = "pool"
    MAPPING = dict()
    
    def __init__(self, config):
        BaseObject.__init__(self, config)

    def _create_object(self):
        monitor_name = self._config.get("monitorName", None)
        monitor_name_to_id = Monitor.MAPPING
        monitor_id = monitor_name_to_id.get(monitor_name, None)
        self._format_config(self._config, {"monitorId":monitor_id}, ["monitorName"])

        BaseObject._create_object(self)
        
        

class VirtualServer(BaseObject):
    """Class representing a virtual server which binds the frontend with the backend"""
    RAML_OBJECT_NAME = "virtualServers"
    OBJECT_NAME = "virtualServer"
    MAPPING = dict()
    
    def __init__(self, config):
        BaseObject.__init__(self, config)

    def _create_object(self):
        pool_name = self._config.get("poolName", None)
        pool_name_to_id = Pool.MAPPING
        pool_id = pool_name_to_id.get(pool_name, None)
        
        application_rule_name = self._config.get("applicationRuleName", None)
        application_rule_name_to_id = ApplicationRule.MAPPING
        application_rule_id = application_rule_name_to_id.get(application_rule_name, None)
        
        application_profile_name = self._config.get("applicationProfileName", None)
        application_profile_name_to_id = ApplicationProfile.MAPPING
        application_profile_id = application_profile_name_to_id.get(application_profile_name, None)
        
        
        self._format_config(self._config, {"applicationRuleId":application_rule_id, "applicationProfileId":application_profile_id, "defaultPoolId":pool_id}, ["poolName", "applicationRuleName", "applicationProfileName"])
        
        BaseObject._create_object(self)


        
class LoadBalancer(object):
    """Class representing the load balancer"""

    RAML_OBJECT_NAME = "loadBalancer"
    OBJECT_NAME = "loadBalancer"
    OBJECT_CREATION_ORDER = ["applicationProfile", "applicationRule", "monitor", "pool", "virtualServer"]
    OBJECT_NAME_TO_CLASS = {"applicationProfile":ApplicationProfile, "applicationRule":ApplicationRule, "monitor":Monitor, "pool":Pool, "virtualServer":VirtualServer}     


    def __init__(self, config):
        self._config = config
        self._global_config = self._fetch_global_config()
        self._request_body_dict = {LoadBalancer.OBJECT_NAME:self._global_config}

    def _fetch_global_config(self):
        enabled = self._config.get("enabled", None)
        enable_service_insertion = self._config.get("enableServiceInsertion", None)
        acceleration_enabled = self._config.get("accelerationEnabled", None)
        logging = self._config.get("logging", None)
        return {"enabled":enabled, "accelerationEnabled":acceleration_enabled, "enableServiceInsertion":enable_service_insertion, "logging":logging}

    def _enable(self):
        resp = client_session.update(LoadBalancer.RAML_OBJECT_NAME, uri_parameters = {"edgeId":edge_id}, request_body_dict = self._request_body_dict)
        if resp["status"] == 204:
            return True
        else:
            return False                
        
        
    def _create_objects(self):
        for obj in LoadBalancer.OBJECT_CREATION_ORDER:
            configs = self._config.pop(obj, None)
            if not configs:
                continue

            if not isinstance(configs, list):
                configs = [configs]

            cls = LoadBalancer.OBJECT_NAME_TO_CLASS[obj]

            for config in configs:
                _ = cls(config)

    def configure(self):
        status = self._enable()
        if not status:
            module.fail_json(msg="Error instantiating the global loadbalancer configuration")

        self._create_objects()
        module.exit_json(changed=True, msg="Successfully created the load balancer with the given configuration")
        
 

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

def main():
    """Main function: 
        1)Get parameters 
        2)Get edge id if edge name is given
        3)Create a LoadBalancer object with the given config
        4)Configure the loadbalancer
            a)Enable the load balancer and configure the global params
            b)Create the objects in the given order:
                - ApplicationProfile
                - ApplicationRule
                - Monitor 
                - Pool (Fetch the monitorId associated with the monitorName for the monitor(s) created above)
                - VirtualServer (Fetch the applicationProfileID, applicationRuleId and defaultPoolId from the applicationProfileName, applicationRuleName and poolName params)
    """

    global edge_id,client_session,module

    module = AnsibleModule(argument_spec=dict(nsxmanager_spec=dict(required=True, type="dict"),
                                                edge_name=dict(required=False),
                                                    edge_id=dict(required=False),
                                                        configuration=dict(required=True, type="dict")
                                                                    ))


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

    configuration = module.params.get("configuration", None)

    L = LoadBalancer(configuration)
    L.configure()

from ansible.module_utils.basic import *
from nsxramlclient.client import NsxClient

if __name__ == "__main__":
    main()
    
