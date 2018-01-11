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
                    dnatMatchSourceAddress, snatMatchAddress, protocol, icmpType, originalPort,
                    translatedPort, dnatMatchSourcePort, snatMatchDestinationPort):
    """
    :param enabled: Enable rule. Boolean. Default is true.
    :param loggingEnabled: Enable logging. Default is false.
    :param action: Type of NAT. Values can be 'snat' or 'dnat'
    :param vnic: Interface on which the translation is applied.
    :param originalAddress: Original address or range. Default is 'any'
    :param translatedAddress: Translated address or range. Default is 'any'.
    :param dnatMatchSourceAddress: Source address to match in DNAT rules. Default is 'any'.
    :param snatMatchDestinationAddress: Destination address to match in SNAT address. Default is 'any'.
    :param protocol: Protocol. Default is 'any'.
    :param icmpType: ICMP type. Only supported when protocol == 'icmp'. Default is 'any'.
    ;param originalPort: Source port for SNAT, destination port for DNAT. Default is 'any'.
    :param translatedPort: Translated port. Default is 'any'.
    :param dnatMatchSourcePort: Source port in DNAT rules. Not valid in SNAT rules. Default is 'any'.
    :param snatMatchDestinationPort: Destination port in SNAT rules. Not valid in DNAT fules. Default is 'any'.
    """
    edge_id, edge_params = get_edge(client_session, edge_name)

    if action == 'snat':
        nat_rule_dict = {'enabled': nat_enabled,
                         'loggingEnabled': loggingEnabled,
                         'action': action,
                         'vnic': vnic,
                         'originalAddress': originalAddress,
                         'translatedAddress': translatedAddress,
                         'snatMatchDestinationAddress': snatMatchDestinationAddress,
                         'protocol': protocol,
                         'originalPort': originalPort,
                         'translatedPort': translatedPort,
                         'snatMatchDestinationPort': snatMatchDestinationPort
                        }
        if protocol == 'icmp':
            nat_rule_dict['icmpType'] = icmpType
    elif action == 'dnat':
        nat_rule_dict = {'enabled': nat_enabled,
                         'loggingEnabled': loggingEnabled,
                         'action': action,
                         'vnic': vnic,
                         'originalAddress': originalAddress,
                         'translatedAddress': translatedAddress,
                         'dnatMatchSourceAddress': dnatMatchSourceAddress,
                         'protocol': protocol,
                         'originalPort': originalPort,
                         'translatedPort': translatedPort,
                         'dnatMatchSourcePort': dnatMatchSourcePort
                        }
        if protocol == 'icmp':
            nat_rule_dict['icmpType'] = icmpType

    cfg_result = client_session.create('nat', uri_parameters={'edgeId': edge_id}, request_body_dict={'natRule': nat_rule_dict})

    if cfg_result['status'] == 204:
        return True
    else:
        return False

def main():
    module = AnsibleModule(
            argument_spec=dict(
                state=dict(default='present', choices=['present', 'absent']),
                nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
                edge_name=dict(required=True),
                nat_enabled=dict(default=True),
                loggingEnabled=dict(default=False),
                action=dict(required=True, choices=['dnat', 'snat']),
                vnic=dict(),
                originalAddress=dict(default='any'),
                translatedAddress=dict(default='any'),
                dnatMatchSourceAddress=dict(default='any'),
                snatMatchDestinationAddress=dict(default='any'),
                procotol=dict(default='any'),
                icmpType=dict(default='any'),
                originalPort=dict(default='any'),
                translatedPort=dict(default='any'),
                dnatMatchSourcePort=dict(default='any'),
                snatMatchDestinationPort=dict(default='any')
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
    
    if changed:
        module.exit_json(changed=True)
    else:
        module.exit_json(changed=False)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
