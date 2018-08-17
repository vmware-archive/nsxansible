#!/usr/bin/env python
#coding=utf-8


__author__  = "matt.pinizzotto@wwt.com"

def get_ftp_config(session):
    if session.read('applianceMgrBackupSettings')['body'] is not None:
        response = session.read('applianceMgrBackupSettings')['body']
        return response['backupRestoreSettings']['ftpSettings']
    else:
        return None

def get_schedule_config(session):
    if session.read('applianceMgrBackupSettings')['body'] is not None:
        response = session.read('applianceMgrBackupSettings')['body']
        try:
            return response['backupRestoreSettings']['backupFrequency']
        except:
            return None
    else:
        return None
        
        
def get_exclude_config(session):
    if session.read('applianceMgrBackupSettings')['body'] is not None:
        response = session.read('applianceMgrBackupSettings')['body']
        try:
            return response['backupRestoreSettings']['excludeTables']['excludeTable']
        except:
            return None
    else:
        return None

def update_ftp_config(session, module):
    ftp_create_body = {'ftpSettings':
	                      {'userName': module.params['name'],
						   'passiveMode': 'true',
						   'useEPSV': 'true',
						   'password': module.params['password'],
						   'passPhrase': module.params['pass_phrase'],
						   'transferProtocol': module.params['transfer_protocol'],
						   'hostNameIPAddress': module.params['ip_addr'],
						   'backupDirectory': module.params['backup_directory'],
						   'filenamePrefix': module.params['file_name_prefix'],
						   'useEPRT': 'false',
						   'port': module.params['port']}
                      }
    return session.update('applianceMgrBackupSettingsFtp',
                           request_body_dict=ftp_create_body)['status'], ftp_create_body


def update_schedule_config(session, schedule):
    schedule_create_body = {'backupFrequency': schedule }
    return session.update('applianceMgrBackupSettingsSchedule',
                           request_body_dict=schedule_create_body)['status']

                           
def update_exclude_config(session, module):
    exclude_create_body = {'excludeTables': { 'excludeTable': module.params['exclude_list'] }}
    session.update('applianceMgrBackupSettingsExclude',
                           request_body_dict=exclude_create_body)['status']
                           
                           

def normalize_schedule(backup_schedule):

    if backup_schedule is not None:
        for item in backup_schedule:
            if not isinstance(item, dict):
                print 'schedule List {} is not a valid dictionary'.format(item)

            if item.get('frequency') == None:
                print  'Schedule List Entry {} in your list is missing the'\
                'mandatory \"frequency\" parameter'.format(item.get('frequency', None))

            else:
                item['frequency'] = str(item['frequency'])

            if item['frequency'] != item['frequency'].isupper():
                item['frequency'] = item['frequency'].upper()

            if item['frequency'] == 'HOURLY':
                if item.get('minuteOfHour', 'missing') == 'missing':
                        item['minuteOfHour'] = '0'
                else:
                    item['minuteOfHour'] = str(item['minuteOfHour'])

                schedule = { 'frequency': item['frequency'],
    		           'minuteOfHour': item['minuteOfHour'] }

            if item['frequency'] == 'DAILY':
                if item.get('hourOfDay', 'missing') == 'missing':
                    item['hourOfDay'] = '0'
                else:
                    item['hourOfDay'] = str(item['hourOfDay'])

                if item.get('minuteOfHour', 'missing') == 'missing':
                    item['minuteOfHour'] = '0'
                else:
                    item['minuteOfHour'] = str(item['minuteOfHour'])

                schedule = { 'frequency': item['frequency'],
    		           'minuteOfHour': item['minuteOfHour'],
    			 'hourOfDay': item['hourOfDay'] }

            if item['frequency'] == 'WEEKLY':
                if item.get('dayOfWeek', 'missing') == 'missing':
                    item['dayOfWeek'] = 'SUNDAY'
                else:
                    if item.get('dayOfWeek') != item.get('dayOfWeek').isupper():
                        item['dayOfWeek'] = str(item['dayOfWeek']).upper()

                if item.get('hourOfDay', 'missing') == 'missing':
                    item['hourOfDay'] = '0'
                else:
                    item['hourOfDay'] = str(item['hourOfDay'])

                if item.get('minuteOfHour', 'missing') == 'missing':
                    item['minuteOfHour'] = '0'
                else:
                    item['minuteOfHour'] = str(item['minuteOfHour'])

                schedule = { 'frequency': item['frequency'],
    		           'minuteOfHour': item['minuteOfHour'],
    			 'hourOfDay': item['hourOfDay'],
    			 'dayOfWeek': item['dayOfWeek'] }

        return True, None, schedule

def check_ftp(ftp_config, module):
    
    changed = False
    if ftp_config['userName'] != module.params['name']:
        changed = True     
        
    elif ftp_config['transferProtocol'] != module.params['transfer_protocol']:
        changed = True
        
    elif ftp_config['hostNameIPAddress'] != module.params['ip_addr']:
        changed = True
        
    elif ftp_config['backupDirectory'] != module.params['backup_directory']:
        changed = True

    elif ftp_config['filenamePrefix'] != module.params['file_name_prefix']:
        changed = True

    #TODO: update password/passphrase this to check if module params exist
    elif module.params['password'] is not None:
        changed = True
     
    elif module.params['pass_phrase'] is not None:
        changed = True
    
    else:
        changed = False
     
    return changed

def check_schedule(schedule_config, schedule):
    changed = False
    
    if cmp(schedule_config, schedule) is not 0:
        changed = True
        return changed
    else:
        return changed
        
def check_exclude(exclude_config, module):
    changed = False
    
    if cmp(exclude_config, module.params['exclude_list']) is not 0:
        changed = True
        return changed
    else:
        return changed


def delete_config(session):
    return session.delete('applianceMgrBackupSettings')
	
def delete_schedule(session):
    return session.delete('applianceMgrBackupSettingsSchedule')
    
def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            name=dict(required=True, type='str'),
            password=dict(required=True, no_log=True, type='str'),
            transfer_protocol=dict(default='FTP', choices=['FTP', 'SFTP']),
            ip_addr=dict(required=True, type='str'),
            port=dict(default='21', type='str'),
            backup_directory=dict(required=True, type='str'),
            file_name_prefix=dict(type='str'),
            pass_phrase=dict(required=True, no_log=True, type='str'),
            backup_schedule=dict(required=True, type='list'),
            exclude_list=dict(type='list'),
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    import time

    session = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                  module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'])
	
		
    ftp_changed = False
    schedule_changed = False
    exclude_changed = False

    ftp_config = get_ftp_config(session)
    schedule_config = get_schedule_config(session)
    exclude_config = get_exclude_config(session)

    if ftp_config and module.params['state'] == 'absent':
        delete_config(session)
        module.exit_json(changed=True, ftp_config=ftp_config, schedule_config=schedule_config)

    if ftp_config == None and module.params['state'] == 'absent':
        module.exit_json(changed=False, ftp_config=ftp_config, schedule_config=schedule_config)

    if not ftp_config and module.params['state'] == 'present':
        ftp = update_ftp_config(session, module)
        ftp_changed = True
     
    if not schedule_config and module.params['state'] == 'present':
        valid, msg, schedule = normalize_schedule(module.params['backup_schedule']) 
        if not valid:
            module.fail_json(msg=msg) 
        update_schedule_config(session, schedule)
        schedule_changed = True
    
    if module.params['exclude_list']:    
        if not exclude_config and module.params['state'] == 'present':
            exclude = update_exclude_config(session, module)
            exclude_changed = True

    if ftp_config is not None:
        ftp_settings_changed = check_ftp(ftp_config, module) 
        if ftp_settings_changed == True:
            ftp = update_ftp_config(session, module)
            ftp_changed = True


    if schedule_config is not None:
        valid, msg, schedule = normalize_schedule(module.params['backup_schedule']) 
        if not valid:
            module.fail_json(msg=msg)
        schedule_settings_changed = check_schedule(schedule_config, schedule) 
        if schedule_settings_changed == True:
            delete_schedule(session)        
            update_schedule_config(session, schedule)
            schedule_changed = True
    
    if module.params['exclude_list']:    
        if exclude_config is not None:
            exclude_settings_changed = check_exclude(exclude_config, module) 
            if exclude_settings_changed == True:
                exclude = update_exclude_config(session, module)
                exclude_changed = True

    if ftp_changed or schedule_changed or exclude_changed:
        module.exit_json(changed=True, ftp_config=ftp, schedule_config=schedule_config)
    else:
        module.exit_json(changed=False, ftp_config=ftp_config, schedule_config=schedule_config)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()



