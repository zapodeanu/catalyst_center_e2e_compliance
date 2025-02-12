#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

__author__ = "Gabriel Zapodeanu TME, ENB"
__email__ = "gzapodea@cisco.com"
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"


import base64
import json
import logging
import os
import time
from datetime import datetime

import yaml
from dnacentersdk import DNACenterAPI
from dotenv import load_dotenv
from github import Github

load_dotenv('environment.env')

CC_URL = os.getenv('CC_URL')
CC_USER = os.getenv('CC_USER')
CC_PASS = os.getenv('CC_PASS')
GITHUB_USERNAME = 'zapodeanu'
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
DATA_FOLDER = 'inventory'

GITHUB_REPO = 'catalyst_center_as_code_data'

os.environ['TZ'] = 'America/Los_Angeles'  # define the timezone for PST
time.tzset()  # adjust the timezone, more info https://help.pythonanywhere.com/pages/SettingTheTimezone/


def github_push(filename, message, content, update=False):
    """
    This function will create or update a file in a GitHub repo
    :param filename: local filename
    :param message: commit message
    :param content: file content
    :param update: True if file update, False if create new file
    :return:
    """
    # authenticate to github
    g = Github(GITHUB_USERNAME, GITHUB_TOKEN)

    # searching for my repository
    repo = g.get_repo(GITHUB_USERNAME + '/' + GITHUB_REPO)

    if update:
        # retrieve existing file to get the sha
        contents = repo.get_contents(filename, ref="main")
        # commit file
        repo.update_file(contents.path, message, content, contents.sha, branch="main")
    else:
        # create new file
        repo.create_file(filename, message, content, branch="main")


def main():
    """
    This application will collect the inventory using the Cisco Catalyst Center REST APIs.
    It will collect all devices managed by Catalyst Center and create inventory files for all devices, all APs,
    non-compliant security advisories and image.
    App workflow:
        - create device inventory - hostname, device management IP address, device UUID, software version,
            device family, role, site, site UUID
        - create access point inventory - hostname, device management IP address, device UUID, software version,
            device family, role, site, site UUID
        - identify device image compliance state and create image non-compliant inventories
        - create a report for security advisories non-compliant devices
        - save all files to local folder, formatted using JSON and YAML
        - push the inventory files to GitHub repo
    :param:
    :return:
    """

    # logging basic
    logging.basicConfig(level=logging.INFO)

    current_time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logging.info('  App "device_inventory.py" run start, ' + current_time)

    # check if inventory folder exists
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

    # create a DNACenterAPI "Connection Object" to use the Python SDK
    catalyst_center_api = DNACenterAPI(username=CC_USER, password=CC_PASS, base_url=CC_URL, version='2.3.7.6',
                                       verify=False)

    # get the device count
    response = catalyst_center_api.devices.get_device_count()
    device_count = response['response']
    logging.info('  Number of devices managed by Catalyst Center: ' + str(device_count))

    # get the device info list
    offset = 1
    limit = 500
    device_list = []
    while offset <= device_count:
        response = catalyst_center_api.devices.get_device_list(offset=offset)
        offset += limit
        device_list.extend(response['response'])
    logging.info('  Collected the device list from Catalyst Center')

    # create device inventory [{"hostname": "", "device_ip": "","device_id": "", "version": "", "device_family": "",
    #  "role": "", "site": "", "site_id": ""},...]
    device_inventory = []
    ap_inventory = []
    for device in device_list:
        # select which inventory to add the device to
        if device.family != "Unified AP":
            device_details = {'hostname': device['hostname']}
            device_details.update({'device_ip': device['managementIpAddress']})
            device_details.update({'device_id': device['id']})
            device_details.update({'version': device['softwareVersion']})
            device_details.update({'device_family': device['type']})
            device_details.update({'role': device['role']})

            # get the device site hierarchy
            response = catalyst_center_api.devices.get_device_detail(identifier='uuid', search_by=device['id'])
            site = response['response']['location']
            device_details.update({'site': site})

            # get the site id
            if site != '':
                response = catalyst_center_api.sites.get_site(name=site)
                site_id = response['response'][0]['id']
                device_details.update({'site_id': site_id})
                device_inventory.append(device_details)
            else:
                device_details.update({'site_id': ''})
        else:
            device_details = {'hostname': device['hostname']}
            device_details.update({'device_ip': device['managementIpAddress']})
            device_details.update({'device_id': device['id']})
            device_details.update({'version': device['softwareVersion']})
            device_details.update({'device_family': device['type']})
            device_details.update({'role': device['role']})

            # get the device site hierarchy
            response = catalyst_center_api.devices.get_device_detail(identifier='uuid', search_by=device['id'])
            site = response['response']['location']
            device_details.update({'site': site})

            # get the site id
            # get the site id
            if site != '':
                response = catalyst_center_api.sites.get_site(name=site)
                site_id = response['response'][0]['id']
                device_details.update({'site_id': site_id})
                ap_inventory.append(device_details)
            else:
                ap_inventory.append(device_details)

    logging.info('  Collected the device inventory from Catalyst Center')

    # save device inventory to json and yaml formatted files
    with open('inventory/device_inventory.json', 'w') as f:
        f.write(json.dumps(device_inventory, indent=4))
    logging.info('  Saved the device inventory to file "device_inventory.json"')

    with open('inventory/device_inventory.yaml', 'w') as f:
        f.write('device inventory, managed by Catalyst Center:\n' + yaml.dump(device_inventory, sort_keys=False))
    logging.info('  Saved the device inventory to file "device_inventory.yaml"')

    # save ap inventory to json and yaml formatted files
    with open('inventory/ap_inventory.json', 'w') as f:
        f.write(json.dumps(ap_inventory, indent=4))
    logging.info('  Saved the device inventory to file "ap_inventory.json"')

    with open('inventory/ap_inventory.yaml', 'w') as f:
        f.write('ap_inventory:\n' + yaml.dump(ap_inventory, sort_keys=False))
    logging.info('  Saved the device inventory to file "ap_inventory.yaml"')

    # retrieve the device image compliance state
    image_non_compliant_devices = []
    response = catalyst_center_api.compliance.get_compliance_detail(compliance_type='IMAGE', compliance_status='NON_COMPLIANT')
    image_non_compliant_list = response['response']
    for device in image_non_compliant_list:
        device_id = device['deviceUuid']
        for item_device in device_inventory:
            if device_id == item_device['device_id']:
                image_non_compliant_devices.append(item_device)
    logging.info('  Number of devices software image non-compliant: ' + str(len(image_non_compliant_devices)))
    logging.info('  Software image non-compliant devices: ')
    for device in image_non_compliant_devices:
        logging.info('      ' + device['hostname'] + ', Site Hierarchy: ' + device['site'])

    # save image non-compliant devices to json and yaml formatted files
    with open('inventory/image_non_compliant_devices.json', 'w') as f:
        f.write(json.dumps(image_non_compliant_devices, indent=4))
    logging.info('  Saved the software image non-compliant device inventory to file "image_non_compliant_devices.json"')

    with open('inventory/image_non_compliant_devices.yaml', 'w') as f:
        f.write('software image non-compliant:\n' + yaml.dump(image_non_compliant_devices, sort_keys=False))
    logging.info('  Saved the software image non-compliant device inventory to file "image_non_compliant_devices.yaml"')

    # retrieve the PSIRTS compliance state
    psirts_non_compliant_devices = []
    response = catalyst_center_api.compliance.get_compliance_detail(compliance_type='PSIRT',
                                                                    compliance_status='NON_COMPLIANT')
    psirts_non_compliant_list = response['response']
    for device in psirts_non_compliant_list:
        device_id = device['deviceUuid']
        for item_device in device_inventory:
            if device_id == item_device['device_id']:
                psirts_non_compliant_devices.append(item_device)
    logging.info('  Number of devices security advisories non-compliant: ' + str(len(psirts_non_compliant_devices)))
    logging.info('  Security advisories non-compliant devices: ')
    for device in psirts_non_compliant_devices:
        logging.info('      ' + device['hostname'] + ', Site Hierarchy: ' + device['site'])

    # save PSIRTS non-compliant devices to json and yaml formatted files
    with open('inventory/psirts_non_compliant_devices.json', 'w') as f:
        f.write(json.dumps(psirts_non_compliant_devices, indent=4))
    logging.info('  Saved the security advisories non-compliant device inventory to file "psirts_non_compliant_devices.json"')

    with open('inventory/psirts_non_compliant_devices.yaml', 'w') as f:
        f.write('security advisories non-compliant:\n' + yaml.dump(psirts_non_compliant_devices, sort_keys=False))
    logging.info('  Saved the security advisories non-compliant device inventory to file "psirts_non_compliant_devices.yaml"')

    # push all files to GitHub repo

    os.chdir('inventory')
    files_list = os.listdir()

    # authenticate to GitHub
    g = Github(GITHUB_USERNAME, GITHUB_TOKEN)

    # searching for my repository
    repo = g.search_repositories(GITHUB_REPO)[0]

    # update inventory files

    for filename in files_list:
        try:
            contents = repo.get_contents(filename)
            update = True
        except:
            update = False  # file does not exist

        with open(filename) as f:
            file_content = f.read()
        file_bytes = file_content.encode('ascii')
        base64_bytes = base64.b64encode(file_bytes)
        logging.info('  GitHub push for file: ' + filename + ', file existing: ' + str(update))

        # create or push the file
        github_push(filename=filename, message="committed by Jenkins - Device Inventory build", content=file_content, update=update)

    date_time = str(datetime.now().replace(microsecond=0))
    logging.info('  App "device_inventory.py" run end: ' + date_time)
    return


if __name__ == '__main__':
    main()
