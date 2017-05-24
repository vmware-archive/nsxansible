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

from pynsxv.library.libutils import nametovalue, dfw_rule_list_helper, get_ipsets, get_macsets, get_secgroups

def dfw_section_list(client_session):
    """
    This function returns all the sections of the NSX distributed firewall
    :param client_session: An instance of an NsxClient Session
    :return returns
            - for each of the three available sections types (L2, L3Redirect, L3) a list with item 0 containing the
              section name as string, item 1 containing the section id as string, item 2 containing the section type
              as a string
            - a dictionary containing all sections' details, including dfw rules
    """
    all_dfw_sections = client_session.read('dfwConfig')['body']['firewallConfiguration']

    if str(all_dfw_sections['layer2Sections']) != 'None':
        l2_dfw_sections = all_dfw_sections['layer2Sections']['section']
    else:
        l2_dfw_sections = list()

    if str(all_dfw_sections['layer2Sections']) != 'None':
        l3r_dfw_sections = all_dfw_sections['layer3RedirectSections']['section']
    else:
        l3r_dfw_sections = list()

    if str(all_dfw_sections['layer3Sections']) != 'None':
        l3_dfw_sections = all_dfw_sections['layer3Sections']['section']
    else:
        l3_dfw_sections = list()

    l2_section_list = [['---', '---', '---']]
    l3r_section_list = [['---', '---', '---']]
    l3_section_list = [['---', '---', '---']]

    if type(l2_dfw_sections) is not list:
        keys_and_values = zip(dict.keys(l2_dfw_sections), dict.values(l2_dfw_sections))
        l2_dfw_sections = list()
        l2_dfw_sections.append(dict(keys_and_values))

    if type(l3_dfw_sections) is not list:
        keys_and_values = zip(dict.keys(l3_dfw_sections), dict.values(l3_dfw_sections))
        l3_dfw_sections = list()
        l3_dfw_sections.append(dict(keys_and_values))

    if type(l3r_dfw_sections) is not list:
        keys_and_values = zip(dict.keys(l3r_dfw_sections), dict.values(l3r_dfw_sections))
        l3r_dfw_sections = list()
        l3r_dfw_sections.append(dict(keys_and_values))

    if len(l2_dfw_sections) != 0:
        l2_section_list = list()
        for sl in l2_dfw_sections:
            try:
                section_name = sl['@name']
            except KeyError:
                section_name = '<empty name>'
            l2_section_list.append((section_name, sl['@id'], sl['@type']))

    if len(l3r_dfw_sections) != 0:
        l3r_section_list = list()
        for sl in l3r_dfw_sections:
            try:
                section_name = sl['@name']
            except KeyError:
                section_name = '<empty name>'
            l3r_section_list.append((section_name, sl['@id'], sl['@type']))

    if len(l3_dfw_sections) != 0:
        l3_section_list = list()
        for sl in l3_dfw_sections:
            try:
                section_name = sl['@name']
            except KeyError:
                section_name = '<empty name>'
            l3_section_list.append((section_name, sl['@id'], sl['@type']))

    return l2_section_list, l3r_section_list, l3_section_list, all_dfw_sections

def dfw_section_read(client_session, dfw_section_name, dfw_section_type):
    """
    This function retrieves details of a dfw section given its id
    :param client_session: An instance of an NsxClient Session
    :param dfw_section_name: The name string of the dfw section to retrieve details from
    :param dfw_section_type: The name string of the dfw section type
    :return: returns
            - a tabular view of the section with the following information: Name, Section id, Section type, Etag
            - ( verbose option ) a dictionary containing all sections's details
    """
    section_list = []
    query_parameters_dict = {'name': dfw_section_name}

    if dfw_section_type == 'L2':
      dfw_section_details = dict(client_session.read('dfwL2Section', query_parameters_dict=query_parameters_dict))
    elif dfw_section_type == 'L3':
      dfw_section_details = dict(client_session.read('dfwL3Section', query_parameters_dict=query_parameters_dict))
    else:
      return None 

    section_name = dfw_section_details['body']['sections']['section']['@name']
    section_id = dfw_section_details['body']['sections']['section']['@id']
    section_type = dfw_section_details['body']['sections']['section']['@type']
    section_etag = dfw_section_details['Etag']
    section_list.append((section_name, section_id, section_type, section_etag))

    return section_list, dfw_section_details

def dfw_section_create(client_session, dfw_section_name, dfw_section_type, rules_schema):
    """
    This function creates a new dfw section given its name and its type
    The new section is created on top of all other existing sections and with no rules
    If a section of the same time and with the same name already exist, nothing is done
    :param client_session: An instance of an NsxClient Session
    :param dfw_section_name: The name of the dfw section to be created
    :param dfw_section_type: The type of the section. Allowed values are L2/L3/L3R
    :param rules_schema: The list of schema of rules. Rule schema is dictionaly type object.
    :return: returns
            - a tabular view of all the sections of the same type of the one just created. The table contains the
              following information: Name, Section id, Section type
            - ( verbose option ) a dictionary containing for each possible type all sections' details, including
              dfw rules
    """

    dfw_section_name = str(dfw_section_name)
    dfw_section_selector = str(dfw_section_type)

    if dfw_section_selector != 'L2' and dfw_section_selector != 'L3' and dfw_section_selector != 'L3R':
        print ('Section Type Unknown - Allowed values are L2/L3/L3R -- Aborting')
        return

    if dfw_section_selector == 'L2':
        dfw_section_type = 'dfwL2Section'

    elif dfw_section_selector == 'L3':
        dfw_section_type = 'dfwL3Section'

    else:
        dfw_section_type = 'layer3RedirectSections'

    # Regardless of the final rule type this line below is the correct way to get the empty schema
    section_schema = client_session.extract_resource_body_example('dfwL3Section', 'create')
    section_schema['section']['@name'] = dfw_section_name

    if rules_schema is None:
        # Delete the rule section to create an empty section
        del section_schema['section']['rule']
    else:
        # Append rule schema to section schema
        del section_schema['section']['rule']    # Clean up
        section_schema['section']['rule'] = []   # Initialize
        for params in rules_schema:
            section_schema['section']['rule'].append(params['rule'])

    # Check for duplicate sections of the same type as the one that will be created, create and return

    try:
        if dfw_section_type == 'dfwL2Section':
            section = client_session.create(dfw_section_type, request_body_dict=section_schema)
            return section
    
        if dfw_section_type == 'dfwL3Section':
            section = client_session.create(dfw_section_type, request_body_dict=section_schema)
            return section
    
        if dfw_section_type == 'layer3RedirectSections':
            section = client_session.create(dfw_section_type, request_body_dict=section_schema)
            return section
    except:
        print 'DFW section creation error. Sent body is: '
        print section_schema

def dfw_section_update(client_session, dfw_section_id, dfw_section_name, dfw_section_type, rules_schema):
    """
    This function updates a existing dfw section given its name and its type
    The new section is created on top of all other existing sections and with no rules
    If a section of the same time and with the same name already exist, nothing is done
    :param client_session: An instance of an NsxClient Session
    :param dfw_section_name: The name of the dfw section to be created
    :param dfw_section_type: The type of the section. Allowed values are L2/L3/L3R
    :param rules_schema: The list of schema of rules. Rule schema is dictionaly type object.
    :return: returns
            - a tabular view of all the sections of the same type of the one just created. The table contains the
              following information: Name, Section id, Section type
            - ( verbose option ) a dictionary containing for each possible type all sections' details, including
              dfw rules
    """

    dfw_section_name = str(dfw_section_name)
    dfw_section_selector = str(dfw_section_type)

    if dfw_section_selector != 'L2' and dfw_section_selector != 'L3' and dfw_section_selector != 'L3R':
        print ('Section Type Unknown - Allowed values are L2/L3/L3R -- Aborting')
        return

    if dfw_section_selector == 'L2':
        dfw_section_type = 'dfwL2SectionId'

    elif dfw_section_selector == 'L3':
        dfw_section_type = 'dfwL3SectionId'

    else:
        dfw_section_type = 'layer3RedirectSections'

    # Regardless of the final rule type this line below is the correct way to get the empty schema
    section_schema = client_session.extract_resource_body_example('dfwL3Section', 'create')
    section_schema['section']['@name'] = dfw_section_name
    section_schema['section']['@id'] = dfw_section_id

    if rules_schema is None:
        # Delete the rule section to create an empty section
        del section_schema['section']['rule']
    else:
        # Append rule schema to section schema
        del section_schema['section']['rule']    # Clean up
        section_schema['section']['rule'] = []   # Initialize
        for params in rules_schema:
            section_schema['section']['rule'].append(params['rule'])

    # Check for duplicate sections of the same type as the one that will be created, create and return

    try:
        if dfw_section_type == 'dfwL2SectionId':
            section = client_session.read(dfw_section_type, uri_parameters={'sectionId': dfw_section_id})
            etag = section.items()[-1][1]
            section = client_session.update(dfw_section_typ, uri_parameters={'sectionId': dfw_section_id}, request_body_dict=section_schema, additional_headers={'If-match': etag})
            return section
    
        elif dfw_section_type == 'dfwL3SectionId':
            section = client_session.read(dfw_section_type, uri_parameters={'sectionId': dfw_section_id})
            etag = section.items()[-1][1]
            section = client_session.update(dfw_section_type, uri_parameters={'sectionId': dfw_section_id}, request_body_dict=section_schema, additional_headers={'If-match': etag})
            return section
    
#        if dfw_section_type == 'layer3RedirectSections':
#            section = client_session.read('dfwL3SectionId', uri_parameters={'sectionId': dfw_section_id})
#            etag = section.items()[-1][1]
#            section = client_session.update(dfw_section_type, request_body_dict=section_schema)
#            return section
    except:
        print 'DFW section update error. Sent body is: '
        print section_schema


def dfw_section_delete(client_session, section_id, section_type):
    """
    This function delete a section given its id
    :param client_session: An instance of an NsxClient Session
    :param section_id: The id of the section that must be deleted
    :param section_type: The section type of the section, choice from 'L2', L3' and 'L3R'
    :return returns
            - A table containing these information: Return Code (True/False), Section ID, Section Name, Section Type
            - ( verbose option ) A list containing a single list which elements are Return Code (True/False),
              Section ID, Section Name, Section Type

            If there is no matching list
                - Return Code is set to False
                - Section ID is set to the value passed as input parameter
                - Section Name is set to "---"
                - Section Type is set to "---"
    """
    dfw_section_id = str(section_id)

    if section_type == 'L3':
        client_session.delete('dfwL3SectionId', uri_parameters={'sectionId': dfw_section_id})
        result = [["True", dfw_section_id, section_type]]
        return result

    if section_type == 'L2':
        client_session.delete('dfwL2SectionId', uri_parameters={'sectionId': dfw_section_id})
        result = [["True", dfw_section_id, section_type]]
        return result

    if section_type == 'L3R':
        client_session.delete('section', uri_parameters={'section': dfw_section_id})
        result = [["True", dfw_section_id, section_type]]

    result = [["False", dfw_section_id, section_type]]
    return result

def dfw_rule_list(client_session):
    """
    This function returns all the rules of the NSX distributed firewall
    :param client_session: An instance of an NsxClient Session
    :return returns
            - a tabular view of all the  dfw rules defined across L2, L3, L3Redirect
            - ( verbose option ) a list containing as many list as the number of dfw rules defined across
              L2, L3, L3Redirect (in this order). For each rule, these fields are returned:
              "ID", "Name", "Source", "Destination", "Service", "Action", "Direction", "Packet Type", "Applied-To",
              "ID (Section)"
    """
    all_dfw_sections_response = client_session.read('dfwConfig')
    all_dfw_sections = client_session.normalize_list_return(all_dfw_sections_response['body']['firewallConfiguration'])

    if str(all_dfw_sections[0]['layer3Sections']) != 'None':
        l3_dfw_sections = all_dfw_sections[0]['layer3Sections']['section']
    else:
        l3_dfw_sections = list()

    if str(all_dfw_sections[0]['layer2Sections']) != 'None':
        l2_dfw_sections = all_dfw_sections[0]['layer2Sections']['section']
    else:
        l2_dfw_sections = list()

    if str(all_dfw_sections[0]['layer3RedirectSections']) != 'None':
        l3r_dfw_sections = all_dfw_sections[0]['layer3RedirectSections']['section']
    else:
        l3r_dfw_sections = list()

    if type(l2_dfw_sections) is not list:
        keys_and_values = zip(dict.keys(l2_dfw_sections), dict.values(l2_dfw_sections))
        l2_dfw_sections = list()
        l2_dfw_sections.append(dict(keys_and_values))

    if type(l3_dfw_sections) is not list:
        keys_and_values = zip(dict.keys(l3_dfw_sections), dict.values(l3_dfw_sections))
        l3_dfw_sections = list()
        l3_dfw_sections.append(dict(keys_and_values))

    if type(l3r_dfw_sections) is not list:
        keys_and_values = zip(dict.keys(l3r_dfw_sections), dict.values(l3r_dfw_sections))
        l3r_dfw_sections = list()
        l3r_dfw_sections.append(dict(keys_and_values))

    l2_temp = list()
    l2_rule_list = list()
    if len(l2_dfw_sections) != 0:
        for i, val in enumerate(l2_dfw_sections):
            if 'rule' in val:
                l2_temp.append(l2_dfw_sections[i])
        l2_dfw_sections = l2_temp
        if len(l2_dfw_sections) > 0:
            if 'rule' in l2_dfw_sections[0]:
                rule_list = list()
                for sptr in l2_dfw_sections:
                    section_rules = client_session.normalize_list_return(sptr['rule'])
                    l2_rule_list = dfw_rule_list_helper(client_session, section_rules, rule_list)
        else:
            l2_rule_list = []

    l3_temp = list()
    l3_rule_list = list()
    if len(l3_dfw_sections) != 0:
        for i, val in enumerate(l3_dfw_sections):
            if 'rule' in val:
                l3_temp.append(l3_dfw_sections[i])
        l3_dfw_sections = l3_temp
        if len(l3_dfw_sections) > 0:
            if 'rule' in l3_dfw_sections[0]:
                rule_list = list()
                for sptr in l3_dfw_sections:
                    section_rules = client_session.normalize_list_return(sptr['rule'])
                    l3_rule_list = dfw_rule_list_helper(client_session, section_rules, rule_list)
        else:
            l3_rule_list = []

    l3r_temp = list()
    l3r_rule_list = list()
    if len(l3r_dfw_sections) != 0:
        for i, val in enumerate(l3r_dfw_sections):
            if 'rule' in val:
                l3r_temp.append(l3r_dfw_sections[i])
        l3r_dfw_sections = l3r_temp
        if len(l3r_dfw_sections) > 0:
            if 'rule' in l3r_dfw_sections[0]:
                rule_list = list()
                for sptr in l3r_dfw_sections:
                    section_rules = client_session.normalize_list_return(sptr['rule'])
                    l3r_rule_list = dfw_rule_list_helper(client_session, section_rules, rule_list)
        else:
            l3r_rule_list = []

    return l2_rule_list, l3_rule_list, l3r_rule_list

def dfw_rule_id_read(client_session, dfw_section_id, dfw_rule_name):
    """
    This function returns the rule(s) ID(s) given a section id and a rule name
    :param client_session: An instance of an NsxClient Session
    :param dfw_rule_name: The name ( case sensitive ) of the rule for which the ID is/are wanted. If rhe name includes
                      includes spaces, enclose it between ""
    :param dfw_section_id: The id of the section where the rule must be searched
    :return returns
            - A dictionary with the rule name as the key and a list as a value. The list contains all the matching
              rules id(s). For example {'RULE_ONE': [1013, 1012]}. If no matching rule exist, an empty dictionary is
              returned
    """

    l2_rule_list, l3_rule_list, l3r_rule_list = dfw_rule_list(client_session)

    list_names = list()
    list_ids = list()
    dfw_rule_name = str(dfw_rule_name)
    dfw_section_id = str(dfw_section_id)

    for i, val in enumerate(l2_rule_list):
        if (dfw_rule_name == val[1]) and (dfw_section_id == val[-1]):
            list_names.append(dfw_rule_name)
            list_ids.append(int(val[0]))

    for i, val in enumerate(l3_rule_list):
        if (dfw_rule_name == val[1]) and (dfw_section_id == val[-1]):
            list_names.append(dfw_rule_name)
            list_ids.append(int(val[0]))

    for i, val in enumerate(l3r_rule_list):
        if (dfw_rule_name == val[1]) and (dfw_section_id == val[-1]):
            list_names.append(dfw_rule_name)
            list_ids.append(int(val[0]))

    dfw_rule_id = dict.fromkeys(list_names, list_ids)
    return dfw_rule_id

def dfw_rule_read(client_session, rule_id):
    """
    This function retrieves details of a dfw rule given its id
    :param client_session: An instance of an NsxClient Session
    :param rule_id: The ID of the dfw rule to retrieve
    :return: returns
            - tabular view of the dfw rule
            - ( verbose option ) a list containing the dfw rule information: ID(Rule)- Name(Rule)- Source- Destination-
              Services- Action - Direction- Pktytpe- AppliedTo- ID(section)
    """
    rule_list = dfw_rule_list(client_session)
    rule = list()

    for sectionptr in rule_list:
        for ruleptr in sectionptr:
            if ruleptr[0] == str(rule_id):
                rule.append(ruleptr)
    return rule

def dfw_rule_delete(client_session, section_id, section_type, rule_id):
    """
    This function delete a dfw rule given its id
    :param client_session: An instance of an NsxClient Session
    :param section_id: The id of the section that includes the rule
    :param section_type The type of the section that include the rule
    :param rule_id: The id of the rule that must be deleted
    :return returns
            - A table containing these information: Return Code (True/False), Rule ID, Rule Name, Applied-To, Section ID
            - ( verbose option ) A list containing a single list which elements are Return Code (True/False),
              Rule ID, Rule Name, Applied-To, Section ID

            If there is no matching rule
                - Return Code is set to False
                - Rule ID is set to the value passed as input parameter
                - All other returned parameters are set to "---"
    """
    dfw_rule_id = str(rule_id)
    dfw_section_id = str(section_id)

    if section_type == 'L3':
        section = client_session.read('dfwL3SectionId', uri_parameters={'sectionId': section_id})
        etag = section.items()[-1][1]
        client_session.delete('dfwL3Rule', uri_parameters={'ruleId': dfw_rule_id, 'sectionId': dfw_section_id}, additional_headers={'If-match': etag})
        response = [dfw_rule_id, dfw_section_id, section_type]
        return True, response

    elif section_type == 'L2':
        section = client_session.read('dfwL2SectionId', uri_parameters={'sectionId': section_id})
        etag = section.items()[-1][1]
        client_session.delete('dfwL2Rule', uri_parameters={'ruleId': dfw_rule_id, 'sectionId': dfw_section_id}, additional_headers={'If-match': etag})
        response = [dfw_rule_id, dfw_section_id, section_type]
        return True, response

    elif section_type == 'L3R':
#        client_session.delete('rule', uri_parameters={'ruleID': dfw_rule_id, 'section': dfw_section_id})
#        response = [dfw_rule_id, dfw_section_id, dfw_section_type]
#        return True, response
        response = "Deletion of L3 redirection rule is not implemented yet."
        return False, response

    response = [dfw_rule_id, dfw_section_id, section_type]
    return False, response

def dfw_rule_create(client_session, section_id, section_type, rule_schema):

    if section_type == 'L3':
        # If DFW section is Layer3
        rule_type = 'dfwL3Rules'
        section_type = 'dfwL3SectionId'
    elif section_type == 'L2':
        # If DFW section is Layer2
        rule_type = 'dfwL2Rules'
        section_type = 'dfwL2SectionId'
    else:
        return False, "Section type does not match criteria: {}".format(section_type)

    section = client_session.read(section_type, uri_parameters={'sectionId': section_id})
    section_etag = section.items()[-1][1]

    try:
        rule = client_session.create(rule_type, uri_parameters={'sectionId': section_id}, request_body_dict=rule_schema,
                                 additional_headers={'If-match': section_etag})
        return True, rule

    except:
        print("")
        print 'Error: cannot create rule. It is possible that some of the parameters are not compatible. Please check' \
              'the following rules are obeyed:'
        print'(*) If the rule is applied to all edge gateways, then "inout" is the only allowed value for parameter -dir'
        print'(*) Allowed values for -pktype parameter are any/ipv6/ipv4'
        print'(*) For a L3 rules applied to all edge gateways "any" is the only allowed value for parameter -pktype'
        print'(*) For a L2 rule "any" is the only allowed value for parameter -pktype'
        print'(*) For a L3 rule allowed values for -action parameter are allow/block/reject'
        print'(*) For a L2 rule allowed values for -action parameter are allow/block'
        print("")
        print'Aborting. No action have been performed on the system'
        print("")
        print("Printing current DFW rule schema used in API call")
        print("-------------------------------------------------")
        print rule_schema

    return False, 'exited for error in REST-API rule creation call'

def dfw_rule_update(client_session, section_id, section_type, rule_id, rule_schema):

    if section_type == 'L3':
        # If DFW section is Layer3
        rule_type = 'dfwL3Rule'
        section_type = 'dfwL3SectionId'
    elif section_type == 'L2':
        # If DFW section is Layer2
        rule_type = 'dfwL2Rule'
        section_type = 'dfwL2SectionId'

    section = client_session.read(section_type, uri_parameters={'sectionId': section_id})
    section_etag = section.items()[-1][1]

    try:
        rule = client_session.update(rule_type, uri_parameters={'ruleId': rule_id, 'sectionId': section_id}, request_body_dict=rule_schema,
                                 additional_headers={'If-match': section_etag})
        return True, rule

    except:
        print("")
        print 'Error: cannot update rule. It is possible that some of the parameters are not compatible. Please check' \
              'the following rules are obeyed:'
        print'(*) If the rule is applied to all edge gateways, then "inout" is the only allowed value for parameter -dir'
        print'(*) Allowed values for -pktype parameter are any/ipv6/ipv4'
        print'(*) For a L3 rules applied to all edge gateways "any" is the only allowed value for parameter -pktype'
        print'(*) For a L2 rule "any" is the only allowed value for parameter -pktype'
        print'(*) For a L3 rule allowed values for -action parameter are allow/block/reject'
        print'(*) For a L2 rule allowed values for -action parameter are allow/block'
        print("")
        print'Aborting. No action have been performed on the system'
        print("")
        print("Printing current DFW rule schema used in API call")
        print("-------------------------------------------------")
        print rule_schema

    return False, 'exited for error in REST-API rule update call'

def dfw_rule_parse(client_session, mod_params, l2_section_list, l3r_section_list, l3_section_list):

    dfw_params = mod_params
    if dfw_params['src_any'] == 'true':
        dfw_params['sources'] = ''
    if dfw_params['dest_any'] == 'true':
        dfw_params['destinations'] = ''
    if dfw_params['service_any'] == 'true':
        dfw_params['services']  = ''
    dfw_params['note']  = ''
    dfw_params['tag']  = ''

    # check section type and existence of rule.
    for val in l2_section_list:
        if dfw_params['section'] in val:
            # Section with the same name already exist
            dfw_params['section_type'] = 'L2'
            dfw_params['section_id'] = str(val[1])
            dfw_rule_id_dict = dfw_rule_id_read(client_session, dfw_params['section_id'], dfw_params['name'])
            if len(dfw_rule_id_dict) == 0:
                dfw_params['rule_id'] = None
                break
            elif len(dfw_rule_id_dict) == 1 and len(dfw_rule_id_dict[dfw_params['name']]) == 1:
                dfw_params['rule_id'] = str(dfw_rule_id_dict[dfw_params['name']][0])
                break
            else:
                msg='Overlapped rule name exists in one section: L2.'
                return False, msg
    else:
        for val in l3_section_list:
            if dfw_params['section'] in val:
                # Section with the same name already exist
                dfw_params['section_type'] = 'L3'
                dfw_params['section_id'] = str(val[1])
                dfw_rule_id_dict = dfw_rule_id_read(client_session, dfw_params['section_id'], dfw_params['name'])
                if len(dfw_rule_id_dict) == 0:
                    dfw_params['rule_id'] = None
                    break
                elif len(dfw_rule_id_dict) == 1 and len(dfw_rule_id_dict[dfw_params['name']]) == 1:
                    dfw_params['rule_id'] = str(dfw_rule_id_dict[dfw_params['name']][0])
                    break
                else:
                    msg='Overlapped rule name exists in one section: L3.'
                    return False, msg
        else: 
            for val in l3r_section_list:
                if dfw_params['section'] in val:
                    # Section with the same name already exist
                    dfw_params['section_type'] = 'L3R'
                    dfw_params['section_id'] = str(val[1])
                    dfw_rule_id_dict = dfw_rule_id_read(client_session, dfw_params['section_id'], dfw_params['name'])
                    if len(dfw_rule_id_dict) == 0:
                        dfw_params['rule_id'] = None
                        break
                    elif len(dfw_rule_id_dict) == 1 and len(dfw_rule_id_dict[dfw_params['name']]) == 1:
                        dfw_params['rule_id'] = dfw_rule_id_dict[dfw_params['name']][0]
                        break
                    else:
                        msg='Overlapped rule name exists in one section: L3R.'
                        return False, msg
            else:
                if mod_params['state'] == 'absent':
#                    module.exit_json(changed=False, argument_spec=mod_params)
                    msg='section does not exist. Section must exist even when deleting rule from the non-existent section.'
                    return False, msg
#                else:
#                    msg='section does not exist.'
#                    return False, msg

    if 'present' in mod_params['state']:
        if dfw_params['section_type'] == 'L2':
            # If DFW section is Layer2
            if dfw_params['pkt_type'] != 'any':
                msg='For a L2 rule "any" is the only allowed value for parameter -pktype'
                return False, msg
            if dfw_params['action'] != 'allow' and dfw_params['action'] != 'block':
                msg='For a L2 rule "allow/block" are the only allowed value for parameter -action'
                return False, msg
            if dfw_params['applyto'] == 'any' or dfw_params['applyto'] == 'edgegw':
                msg='For a L2 rule "any" and "edgegw" are not allowed values for parameter applyto'
                return False, msg
            if dfw_params['src_any'] == 'false':
              for item in dfw_params['sources']:
                if item['type'] == 'ipset':
                  msg='For a L2 rule "ipset" is not an allowed value as source'
                  return False, msg
            if dfw_params['dest_any'] == 'false':
              for item in dfw_params['destinations']:
                if item['type'] == 'ipset':
                  msg='For a L2 rule "ipset" is not an allowed value as destination'
                  return False, msg
            if dfw_params['action'] == 'block':
                dfw_params['action'] = 'deny'

        elif dfw_params['section_type'] == 'L3':
            # If DFW section is Layer3
            if dfw_params['action'] == 'block':
                dfw_params['action'] = 'deny'

        else:
            # If DFW section is Layer3 Redirection
            msg='Error: L3 redirect rules are not supported in this version. Aborting. No action have been performed on the system'
            return False, msg

    return True, dfw_params

def dfw_rule_construct(client_session, params, vccontent=None):

    if params['section_type'] == 'L3':
        # If DFW section is Layer3
        params['rule_type'] = 'dfwL3Rules'
    elif params['section_type'] == 'L2':
        # If DFW section is Layer2
        params['rule_type'] = 'dfwL2Rules'

    if params['applyto'] == 'any':
        params['applyto'] = 'ANY'
    elif params['applyto'] == 'dfw':
        params['applyto'] = 'DISTRIBUTED_FIREWALL'
    elif params['applyto'] == 'edgegw':
        params['applyto'] = 'ALL_EDGES'

    if params['src_any'] == 'false':
        for item in params['sources']:
            if not 'name' in item:
                item.update({'name': ''})
            if not 'value' in item:
                item.update({'value': ''})

    if params['dest_any'] == 'false':
        for item in params['destinations']:
            if not 'name' in item:
                item.update({'name': ''})
            if not 'value' in item:
                item.update({'value': ''})

    if params['service_any'] == 'false':
        for item in params['services']:
            if not 'proto' in item:
                item.update({'proto': ''})
            if not 'destport' in item:
                item.update({'destport': ''})
            if not 'srcport' in item:
                item.update({'srcport': ''})
            if not 'name' in item:
                item.update({'name': ''})

    if not params['note']:
        params['note'] = ''

    if not params['tag']:
        params['tag'] = ''

    if not vccontent:
        vccontent = ''

    # TODO: complete the description

    API_TYPES = {'dc': 'Datacenter', 'ipset': 'IPSet', 'macset': 'MACSet', 'ls': 'VirtualWire',
                 'secgroup': 'SecurityGroup', 'host': 'HostSystem', 'vm':'VirtualMachine',
                 'cluster': 'ClusterComputeResource', 'dportgroup': 'DistributedVirtualPortgroup',
                 'portgroup': 'Network', 'respool': 'ResourcePool', 'vapp': 'ResourcePool', 'vnic': 'VirtualMachine',
                 'Ipv4Address': 'Ipv4Address'}

    # The schema for L2rules is the same as for L3rules
    rule_schema = client_session.extract_resource_body_example('dfwL3Rules', 'create')

    if params['rule_type'] != 'rules':
        # L3 or L2 rule
        # Mandatory values of a rule
        rule_schema['rule']['name'] = str(params['name'])
        # If appliedTo is 'ALL_EDGES' only inout is allowed
        rule_schema['rule']['direction'] = str(params['direction'])
        # If appliedTo is 'ALL_EDGES' only packetType any is allowed
        rule_schema['rule']['packetType'] = str(params['pkt_type'])
        rule_schema['rule']['@disabled'] = str(params['disabled'])
        rule_schema['rule']['action'] = str(params['action'])
        rule_schema['rule']['appliedToList']['appliedTo']['value'] = str(params['applyto'])

        # Optional values of a rule. I believe it's cleaner to set them anyway, even if to an empty value
        rule_schema['rule']['notes'] = str(params['note'])
        # If appliedTo is 'ALL_EDGES' no tags are allowed
        rule_schema['rule']['tag'] = str(params['tag'])
        rule_schema['rule']['@logged'] = params['logged']

        # Deleting all the three following sections will create the simplest any any any allow any rule
        #
        # If the source is "any" the section needs to be deleted
        if params['src_any'] == 'true':
            del rule_schema['rule']['sources']
        else:
          # Mandatory values of a source ( NB: source is an optional value )
          new_items = []
          for item in params['sources']:
            if item['value'] != '':
              new_items.append({"value": item['value'], "type": API_TYPES[item['type']] })
            # Optional values of a source ( if specified )
            elif item['name'] != '':
              # Code to map name to value
              rule_src_value = nametovalue(vccontent, client_session, item['name'], item['type'])
              if rule_src_value == '':
                msg=str('Matching Source Object ID not found - Abort - No operations have been performed on the system')
                return False, msg
              new_items.append({"value": rule_src_value, "type": API_TYPES[item['type']] })

          rule_schema['rule']['sources']['source'] = new_items
          # Optional values of a source ( if specified )
          if params['src_excluded'] != '':
            rule_schema['rule']['sources']['@excluded'] = params['src_excluded']

        # If the destination value is "any" the section needs to be deleted
        if params['dest_any'] == 'true':
            try:
                del rule_schema['rule']['destinations']
            except:
                pass
        else:
          # Mandatory values of a destination ( NB: destination is an optional value )
          new_items = []
          for item in params['destinations']:
            if item['value'] != '':
              new_items.append({"value": item['value'], "type": API_TYPES[item['type']]})
            # Optional values of a destination ( if specified )
            elif item['name'] != '':
              # Code to map name to value
              rule_dest_value = nametovalue(vccontent, client_session, item['name'], item['type'])
              if rule_dest_value == '':
                msg=str('Matching Destination Object ID not found - No operations have been performed on the system')
                return False, msg
              new_items.append({"value": rule_dest_value, "type": API_TYPES[item['type']]})

          rule_schema['rule'].update({'destinations':{'destination':new_items}})
          # Optional values of a destination ( if specified )
          if params['dest_excluded'] != '':
            rule_schema['rule']['destinations'].update({'@excluded':params['dest_excluded']})

        # If the service is "any" the section needs to be deleted
        if params['service_any'] == 'true':
            del rule_schema['rule']['services']
        else:
          new_items = []
          for item in params['services']:
            if item['proto'] != '' and item['destport'] != '' and item['name'] != '':
              msg=str('Service can be specified either via protocol/port or name')
              return False, msg

            new_item = {}
            if item['proto'] != '':
              # Mandatory values of a service specified via protocol ( NB: service is an optional value )
              new_item.update({"protocolName": item['proto']})
            if item['destport'] != '':
              new_item.update({"destinationPort": item['destport']})
            # Optional values of a service specified via protocol ( if specified )
            if item['srcport'] != '':
              new_item.update({"sourcePort": item['srcport']})

            if item['name'] != '':
              new_item.update({"value": ''})
              # Mandatory values of a service specified via application/application group (service is an optional value)
              services = client_session.read('servicesAppsScopeScope', uri_parameters={'scopeId': 'globalroot-0'})
              service = services.items()[1][1]['list']['application']
              for servicedict in service:
                if str(servicedict['name']) == item['name']:
                  new_item['value'] = str(servicedict['objectId'])
                  break
              if new_item['value'] == '':
                servicegroups = client_session.read('serviceGroups', uri_parameters={'scopeId': 'globalroot-0'})
                servicegrouplist = servicegroups.items()[1][1]['list']['applicationGroup']
                for servicegroupdict in servicegrouplist:
                  if str(servicegroupdict['name']) == item['name']:
                    new_item['value'] = str(servicegroupdict['objectId'])
                if new_item['value'] == '':
                  msg=str('Invalid service specified')
                  return False, msg
            new_items.append(new_item)

          rule_schema['rule']['services']['service'] = new_items

    return rule_schema

