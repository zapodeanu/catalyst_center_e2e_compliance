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

import requests
import urllib3
import json
import os
import time
import warnings
import chromadb

from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth  # for Basic Auth
from urllib3.exceptions import InsecureRequestWarning  # for insecure https warnings

# noinspection PyProtectedMember
from langchain._api import LangChainDeprecationWarning
from langchain.chains.question_answering import load_qa_chain
from langchain_community.vectorstores.chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings

urllib3.disable_warnings(InsecureRequestWarning)  # disable insecure https warnings
warnings.simplefilter("ignore", category=LangChainDeprecationWarning)  # to disable LangChain warnings

load_dotenv('environment.env')

# database server details
DB_SERVER = os.getenv('DB_SERVER')
DB_PORT = int(os.getenv('DB_PORT'))
DB_COLLECTION = os.getenv('DB_COLLECTION')

# OpenAI key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

MODEL_NAME = 'all-MiniLM-L6-v2'
OPENAI_MODEL = 'gpt-4o'

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Jenkins server details
JENKINS_SERVER = os.getenv('JENKINS_SERVER')
AI_TOKEN = os.getenv('AI_TOKEN')
JENKINS_USER = os.getenv('JENKINS_USER')

# OpenAI key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

os.environ['TZ'] = 'America/Los_Angeles'  # define the timezone for PST
time.tzset()  # adjust the timezone, more info https://help.pythonanywhere.com/pages/SettingTheTimezone/

JENKINS_AUTH = HTTPBasicAuth(JENKINS_USER, AI_TOKEN)


def provision_network_device(arguments):
    """
    This function will call REST APIs to trigger Jenkins pipeline to provision the network device with {hostname} to
    site with the hierarchy {site_hierarchy}
    :param arguments: Required arguments as dictionary: {'hostname': 'PDX-RN', 'site_hierarchy': 'Global/OR/PDX/Floor-2'}
    :return: task status
    """

    url = JENKINS_SERVER + '/job/Provision%20Device/buildWithParameters'
    response = requests.post(url, params=arguments, auth=JENKINS_AUTH, verify=False)
    if response.status_code == 201:
        response_status = 'Device provisioning started, see status here: https://10.93.141.47:8443/job/Provision%20Device/'
    else:
        response_status = 'Pipeline not started, something went wrong'
    return response_status, response.status_code


def software_distribution(arguments):
    """
    This function will call REST APIs to trigger Jenkins pipeline to start a software image distribution for
    the network device with {hostname}. The golden image for the device and site will be uploaded to device
    :param arguments: Required arguments as dictionary: {'hostname': 'PDX-RN'}
    :return: task status
    """

    url = JENKINS_SERVER + '/job/Software%20Distribution/buildWithParameters'
    response = requests.post(url, params=arguments, auth=JENKINS_AUTH, verify=False)
    if response.status_code == 201:
        response_status = 'Device provisioning started, see status here: https://10.93.141.47:8443/job/Software%20Distribution/'
    else:
        response_status = 'Pipeline not started, something went wrong'
    return response_status, response.status_code


def add_device(arguments):
    """
        This function will call REST APIs to trigger Jenkins pipeline to add a new network device with
        {management_ip_address} to Catalyst Center
        :param arguments: Required arguments as dictionary: {'management_ip_address': '10.93.141.23'}
        :return: task status, and status code
        """

    url = JENKINS_SERVER + '/job/Add%20Device/buildWithParameters'
    response = requests.post(url, params=arguments, auth=JENKINS_AUTH, verify=False)
    if response.status_code == 201:
        response_status = 'Add new device to inventory started, see status here: https://10.93.141.47:8443/job/Add%20Device/'
    else:
        response_status = 'Pipeline not started, something went wrong'
    return response_status, response.status_code


def chatbot():
    """
    This chatbot will expect user input for network configuration workflows using Catalyst Center REST APIs.
    The workflow would be a pipeline executed on Jenkins, and providing parameters may be required.
    The Jenkins pipelines will pull code from GitHub and run Python, Ansible playbooks or Terraform plans.
    The expected user input will be provided using natural language and OpenAI ill identify the function expected to
    be called to trigger the pipeline build.
    """

    current_time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print(' Application "catalyst_center_genai_config_tools.py" Start, ' + current_time)

    time.sleep(1)

    # function calling list with all supported ops

    functions = [
        {
            "name": "add_device",
            "description": "Add a new network device, switch our router to Catalyst Center. Call this function when "
                           "user asks to add a network device, device, node, host, to the inventory or Catalyst"
                           "Center while providing an IP address of device. The device must be up and"
                           "reachable by Catalyst Center, and Catalyst Center will use the provided IP address"
                           "to manage the device. For example: an user asks for 'add device'",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_ip_address": {
                        "type": "string",
                        "description": "This is the device IP address that will be used to manage the device"
                    }
                },
                "required": ["device_ip_address"],
                "additionalProperties": False
            }
        },
        {
            "name": "provision_network_device",
            "description": "Provision a device to a site. Call this whenever you need to provision a device, "
                           "or network device, to a location, for example: an user asks "
                           "'Provision a network device to a site'",
            "parameters": {
                "type": "object",
                "properties": {
                    "hostname": {
                        "type": "string",
                        "description": "This is the device name or hostname, or the network device name or hostname"
                    },
                    "siteHierarchy": {
                        "type": "string",
                        "description": "The site hierarchy, or site name, where the device will be provisioned"
                    }
                },
                "required": ["hostname", "siteHierarchy"],
                "additionalProperties": False
            }
        },
        {
            "name": "software_distribution",
            "description": "Start a new software upgrade to a device. Call this whenever you need to start a "
                           "software upgrade or image distribution to a device or network device, to a location, "
                           "for example: an user asks for 'software distribution'",
            "parameters": {
                "type": "object",
                "properties": {
                    "hostname": {
                        "type": "string",
                        "description": "This is the device name or hostname, or the network device name or hostname"
                    }
                },
                "required": ["hostname"],
                "additionalProperties": False
            }
        }
    ]

    # loop to keep the chatbot running
    while True:
        # Get user input
        user_input = input(
            '\n I am a network assistant running network automation workflows. What can I help you with? ')

        user_input = user_input.strip()  # remove unnecessary spaces
        if user_input == '':  # check if empty entry and continue, no need to use AI
            continue

        # Check if the user wants to exit
        if user_input.lower() in ['exit', 'quit', 'q']:
            print('Exiting chatbot...')
            break

        # We first check if the user input will trigger a function call

        # Start a chat that identifies and triggers the function
        messages = [
            {"role": "system", "content": "I am a network assistant running network automation workflows like devices "
                                          "provisioning, device onboarding, software upgrades, device configuration, ..."},
            {"role": "user",
             "content": user_input}
        ]

        # Make a request function calling to OpenAI, providing the query and the function list
        response = client.chat.completions.create(model="gpt-4o", messages=messages, functions=functions,
                                                  function_call="auto")
        # print('\n\n Chat completion response: ' + str(response))

        # Check if the assistant decided to make a function call
        if response.choices[0].finish_reason == 'function_call':
            function_call = response.choices[0].message.function_call  # Access the function call details

            function_name = function_call.name  # Get the function name
            arguments = json.loads(function_call.arguments)  # Load the arguments as a JSON object
            print('\n Workflow name: ' + function_name)
            print(' Params identified: \n      ' + json.dumps(arguments))
            validation_input = input('\n Do you want to continue or not (y/n)? ')

            # If provided workflow and params are correct, continue with the execution.
            # Call the Jenkins API to trigger the identified pipeline
            if validation_input == 'y' or validation_input == 'Y':
                workflow_response = globals()[function_name](arguments)
                if workflow_response[1] == 201:
                    # Return the status to user
                    print('\n Network Assistant: Happy to help, ' + workflow_response[0])

        else:
            # There was not a function call identified
            # We will now use RAG to find out the answer for the query

            # Chroma DB server details
            chroma_db_server = chromadb.HttpClient(host=DB_SERVER, port=DB_PORT)

            # define the model for creating embeddings for the query
            embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)

            # define the Chroma DB connection to server and collection
            chroma_db = Chroma(
                client=chroma_db_server,
                collection_name=DB_COLLECTION,
                embedding_function=embeddings
            )

            # define the LLM used - OpenAI, model 'gpt-4o'
            llm = ChatOpenAI(model_name=OPENAI_MODEL, temperature=1)
            chain = load_qa_chain(llm, chain_type="stuff", verbose=False)


            # search for the similarity matches from the Chroma DB server/collection
            matching_docs = chroma_db.similarity_search(user_input, k=6)

            # The similarity search result and query will be used to generate the answer using the LLM
            answer = chain.invoke({'input_documents': matching_docs, 'question': user_input})
            print(answer['output_text'])

    date_time = str(datetime.now().replace(microsecond=0))
    print(' End of Application "catalyst_center_genai_config_tools.py" Run: ' + date_time)

    return


if __name__ == '__main__':
    chatbot()
