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


import json
import logging
import os
import time
import yaml
import base64
import requests
import argparse

from datetime import datetime
from dnacentersdk import DNACenterAPI
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth  # for Basic Auth

load_dotenv('environment.env')

CC_URL = os.getenv('CC_URL')
CC_USER = os.getenv('CC_USER')
CC_PASS = os.getenv('CC_PASS')

os.environ['TZ'] = 'America/Los_Angeles'  # define the timezone for PST
time.tzset()  # adjust the timezone, more info https://help.pythonanywhere.com/pages/SettingTheTimezone/


def main():
    """
    This application add a device to the inventory. It will use the Catalyst Center credentials already configured.
    :param device_ip_address: the device IP address that will be used by Catalyst Center to manage the device
    :return:
    """

    # logging basic
    logging.basicConfig(level=logging.INFO)

    current_time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logging.info('  App "add_device.py" run start, ' + current_time)

    # parse the input argument
    parser = argparse.ArgumentParser(description="A script that accepts one argument.")
    parser.add_argument("device_ip_address", help="The device management IP address")

    args = parser.parse_args()
    device_ip_address = args.device_ip_address

    # create a DNACenterAPI "Connection Object" to use the Python SDK
    catalyst_center_api = DNACenterAPI(username=CC_USER, password=CC_PASS, base_url=CC_URL, version='2.3.7.6',
                            verify=False)

    # verify if device already managed by Catalyst Center
    response = catalyst_center_api.devices.get_device_list(management_ip_address=device_ip_address)
    if response['response'] != []:
        logging.info('  The device is already managed by Catalyst Center')
        return

    # add device to inventory
    logging.info('  The device is not managed by Catalyst Center. Add device process started')
    payload = {
        "cliTransport": "ssh",
        "compute_device": False,
        "httpPassword": "HTTPuser123!",
        "httpPort": "443",
        "httpSecure": False,
        "httpUserName": "httpuser",
        "ipAddress": [
            "10.93.141.22"
        ],
        "netconfPort": "830",
        "password": "apiuser123!",
        "enable_password": "apiuser123!",
        "snmpROCommunity": "r3@d",
        "snmpRWCommunity": "wr!t3",
        "snmpRetry": 3,
        "snmpTimeout": 5,
        "snmpVersion": "v2",
        "type": "NETWORK_DEVICE",
        "userName": "catcenter"
    }

    response = catalyst_center_api.devices.add_device(payload=payload)
    task_id = response['response']['taskId']
    logging.info('  The add device task id is:' + task_id)

    # check task completion
    time.sleep(5)
    status = 'PENDING'
    while status == 'PENDING':
        response = catalyst_center_api.task.get_tasks_by_id(id=task_id)
        status = response['response']['status']
        time.sleep(5)

    result_location = CC_URL + response['response']['resultLocation']
    logging.info('  The add device task completed: ' + status)
    logging.info('  Details may be found here: ' + result_location)

    date_time = str(datetime.now().replace(microsecond=0))
    logging.info('  App "add_device.py" run end: ' + date_time)
    return


if __name__ == '__main__':
    main()
