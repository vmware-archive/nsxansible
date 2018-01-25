#!/usr/bin/env python
# coding=utf-8

__author__ = 'virtualelephant'

# From the vmware/nsxansible/nsx_edge_router.py Ansible library
def get_edge(client_session, edge_name):
    """
    :param client session: An instance of an NsxClient Session
    :param edge_name: The name of the edge searched
    :return: A tuple, with the first item being the edge or dlr id as string of the first Scope found with the
             right name and the second item being a dictionary of the logical parameters as return by the NSX API
    """
    all_edge = client_session.read_all_pages('nsxEdges', 'read')

    try:
        edge_params = [scope for scope in all_edge if scope['name'] == edge_name][0]
        edge_id = edge_params['objectId']
    except IndexError:
        return None, None

    return edge_id, edge_params


def create_nat_rule(client_session, edge_name, nat_enabled, loggingEnabled, action, vnic, originalAddress, translatedAddress,
                    matchAddress, protocol, icmpType, originalPort, translatedPort, matchPort, ruleTag, description):
    """
    :param enabled: Enable rule. Boolean. Default is true.
    :param loggingEnabled: Enable logging. Default is false.
    :param action: Type of NAT. Values can be 'snat' or 'dnat'
    :param vnic: Interface on which the translation is applied.
    :param originalAddress: Original address or range. Default is 'any'
    :param translatedAddress: Translated address or range. Default is 'any'.
    :param matchAddress: Either dnatMatchSourceAddress or snatMatchDestinationAddress. Default is 'any'.
    :param protocol: Protocol. Default is 'any'.
    :param icmpType: ICMP type. Only supported when protocol == 'icmp'. Default is 'any'.
    ;param originalPort: Source port for SNAT, destination port for DNAT. Default is 'any'.
    :param translatedPort: Translated port. Default is 'any'.
    :param matchPort: Either dnatMatchSourcePort or snatMatchDestinationPort. Default is 'any'
    :param ruleTag: This can be used to specify user-controlled ruleId. Must be between 65537-131072.
    :param description: user-generated description field
    :return: Returns true or false.
    """
    edge_id, edge_params = get_edge(client_session, edge_name)

    if action == 'snat':
        nat_rule_dict = { 'natRule': {'action': action, 'vnic': vnic, 'originalAddress': originalAddress, 'translatedAddress': translatedAddress, 'loggingEnabled': loggingEnabled, 'enabled': nat_enabled, 'protocol': protocol, 'originalPort': originalPort, 'translatedPort': translatedPort, 'snatMatchDestinationAddress': matchAddress, 'snatMatchDestinationPort': matchPort, 'description': description}}

    elif action == 'dnat':
        nat_rule_dict = { 'natRule': {'action': action, 'vnic': vnic, 'originalAddress': originalAddress, 'translatedAddress': translatedAddress, 'loggingEnabled': loggingEnabled, 'enabled': nat_enabled, 'protocol': protocol, 'originalPort': originalPort, 'translatedPort': translatedPort, 'dnatMatchSourceAddress': matchAddress, 'dnatMatchSourcePort': matchPort, 'description': description}}

    if protocol == 'icmp':
        nat_rule_dict['natRule']['icmpType'] = icmpType
    if ruleTag is not None:
        nat_rule_dict['natRule']['ruleTag'] = ruleTag

    cfg_result = client_session.create('edgeNatRules', uri_parameters={'edgeId': edge_id}, request_body_dict={'natRules': nat_rule_dict})

    if cfg_result['status'] == 204:
        return True
    else:
        return False

def delete_nat_rule(client_session, edge_name, ruleId):
    """
    :param client_session:
    :param edge_name: Name of the Edge to modify
    :param ruleId: Specific ruleId to delete
    :return: Returns true or false
    """
    edge_id, edge_params = get_edge(client_session, edge_name)

    cfg_result = client_session.delete('edgeNatRule', uri_parameters={'edgeId': edge_id, 'ruleID': ruleId})

    if cfg_result['status'] == 204:
        return True
    else:
        return False

def main():
    module = AnsibleModule(
            argument_spec=dict(
                state=dict(default='present', choices=['present', 'absent']),
                nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
                name=dict(required=True),
                mode=dict(required=True, choices=['create', 'delete']),
                nat_enabled=dict(default='true'),
                loggingEnabled=dict(default='false'),
                rule_type=dict(choices=['dnat', 'snat']),
                description=dict(default=None),
                vnic=dict(),
                originalAddress=dict(default='any'),
                translatedAddress=dict(default='any'),
                dnatMatchSourceAddress=dict(default='any'),
                snatMatchDestinationAddress=dict(default='any'),
                protocol=dict(default='any'),
                icmpType=dict(default='any'),
                originalPort=dict(default='any'),
                translatedPort=dict(default='any'),
                dnatMatchSourcePort=dict(default='any'),
                snatMatchDestinationPort=dict(default='any'),
                ruleTag=dict(default=None),
                ruleId=dict()
            ),
            supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    client_session = NsxClient(module.params['nsxmanager_spec']['raml_file'],
                               module.params['nsxmanager_spec']['host'],
                               module.params['nsxmanager_spec']['user'],
                               module.params['nsxmanager_spec']['password'])

    changed = False
    edge_id, edge_params = get_edge(client_session, module.params['name'])

    if module.params['mode'] == 'create':
        if module.params['rule_type'] == 'snat':
            changed = create_nat_rule(client_session, module.params['name'], module.params['nat_enabled'],
                                      module.params['loggingEnabled'], module.params['rule_type'], module.params['vnic'],
                                      module.params['originalAddress'], module.params['translatedAddress'],
                                      module.params['snatMatchDestinationAddress'], module.params['protocol'],
                                      module.params['icmpType'], module.params['originalPort'], module.params['translatedPort'],
                                      module.params['snatMatchDestinationPort'], module.params['ruleTag'],
                                      module.params['description']
                                     )
        if module.params['rule_type'] == 'dnat':
            changed = create_nat_rule(client_session, module.params['name'], module.params['nat_enabled'],
                                      module.params['loggingEnabled'], module.params['rule_type'], module.params['vnic'],
                                      module.params['originalAddress'], module.params['translatedAddress'],
                                      module.params['dnatMatchSourceAddress'], module.params['protocol'],
                                      module.params['icmpType'], module.params['originalPort'], module.params['translatedPort'],
                                      module.params['dnatMatchSourcePort'], module.params['ruleTag'],
                                      module.params['description']
                                     )
    elif module.params['mode'] == 'delete':
        changed = delete_nat_rule(client_session, module.params['name'], module.params['ruleId'])
    else:
        changed = False
    
    if changed:
        module.exit_json(changed=True)
    else:
        module.exit_json(changed=False)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
