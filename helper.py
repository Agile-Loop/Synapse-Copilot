import os
import json
import logging
import datetime
import time
import yaml
from base64 import b64encode
import spotipy
from langchain.requests import Requests
from langchain import OpenAI

from utils import reduce_openapi_spec, ColorPrint
from model import ApiLLM

from model.api_selector import icl_examples as api_selector_icl
from model.planner import icl_examples as planner_icl
from requests.auth import HTTPBasicAuth


def process_spec_file(file_path: str = None, token: str = None, key: str = None, username: str = None):
    with open(file_path) as f:
        raw_api_spec = json.load(f)

    api_spec = reduce_openapi_spec(raw_api_spec, only_required=False)

    if "trello" in file_path:
        params = {
            "key": key,
            "token": token
        }
        return api_spec, params

    if "jira" in file_path:
        credentials = f'{username}:{token}'
        encoded_credentials = b64encode(credentials.encode('utf-8')).decode('utf-8')
        headers = {
            'Authorization': f'Basic {encoded_credentials}'
        }
        return api_spec, headers

    if "salesforce" in file_path:
        headers = {
            'Authorization': f'Bearer {token}'
        }
        return api_spec, headers

    if "spotify" in file_path:
        scopes = list(raw_api_spec['components']['securitySchemes']
                      ['oauth_2_0']['flows']['authorizationCode']['scopes'].keys())
        access_token = spotipy.util.prompt_for_user_token(
            scope=','.join(scopes))
    else:
        access_token = token

    if "upclick" in file_path:
        headers = {
            'Authorization': access_token
        }
    else:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

    return api_spec, headers


def populate_api_selector_icl_examples(scenario: str = None):
    with open(f"./icl_examples/api_selector/{scenario}.txt", 'r') as f:
        examples = f.read()
    api_selector_icl[scenario] = f"""{examples}
    """


def populate_planner_icl_examples(scenario: str = None):
    with open(f"./icl_examples/planner/{scenario}.txt", 'r') as f:
        examples = f.read()
    planner_icl[scenario] = f"""{examples}
    """


def replace_api_credentials(model, scenario, actual_key, actual_token):
    # Open the file and read the contents
    with open(f"./icl_examples/{model}/{scenario}_base.txt", 'r') as file:
        content = file.readlines()

    # Replace placeholders with actual key and token
    updated_content = [line.replace(r"{key}", actual_key).replace(r"{token}", actual_token) for line in content]

    # Write the updated content back to the file
    with open(f"./icl_examples/{model}/{scenario}.txt", 'w') as file:
        file.writelines(updated_content)


def replace_api_credentials_in_json(scenario, actual_key, actual_token):
    # Open the JSON file and load the content
    with open(f"./specs/{scenario}_base.json", 'r') as json_file:
        content = json.load(json_file)

    def replace_values(d, actual_key, actual_token):
        for key, value in d.items():
            if isinstance(value, dict):
                replace_values(value, actual_key, actual_token)
            elif isinstance(value, str):
                d[key] = value.replace(r"{key}", actual_key).replace(r"{token}", actual_token)

    def process_list_of_dicts(lst, actual_key, actual_token):
        for item in lst:
            if isinstance(item, dict):
                replace_values(item, actual_key, actual_token)

    # Function to recursively update placeholders in a nested dictionary
    def update_placeholders(obj):
        if isinstance(obj, list):
            process_list_of_dicts(lst=obj, actual_key=actual_key, actual_token=actual_token)
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    update_placeholders(value)

    # Replace placeholders with actual key and token
    update_placeholders(content)

    # Write the updated content back to the file
    with open(f"./specs/{scenario}_oas.json", 'w') as json_file:
        json.dump(content, json_file, indent=2)
        print("Contents updated!")


def replace_api_credentials_in_jira_json(scenario, actual_token, actual_host, actual_username):
    # Open the JSON file and load the content
    with open(f"./specs/{scenario}_base.json", 'r') as json_file:
        content = json.load(json_file)

    def replace_values(d, actual_token, actual_host, actual_username, actual_basepath=""):
        for key, value in d.items():
            if isinstance(value, dict):
                replace_values(value, actual_token, actual_host, actual_username)
            elif isinstance(value, str):
                # d[key] = value.replace(r"{{username}}", actual_username).replace(r"{{apiToken}}", actual_token).replace(r"{{host}}", actual_host).replace(r"{{basePath}}", actual_basepath)
                d[key] = value.replace(r"{{host}}", actual_host).replace(r"{{basePath}}", actual_basepath)
            elif isinstance(value, list):
                try:
                    d[key] = [item.replace(r"{{username}}", actual_username).replace(r"{{apiToken}}", actual_token) for
                              item in value]
                except Exception as e:
                    print(f"Following exception occured: {e}")

    def process_list_of_dicts(lst, actual_token, actual_host, actual_username):
        for item in lst:
            if isinstance(item, dict):
                replace_values(d=item, actual_token=actual_token, actual_host=actual_host,
                               actual_username=actual_username)

    # Function to recursively update placeholders in a nested dictionary
    def update_placeholders(obj):
        if isinstance(obj, list):
            try:
                obj = [item.replace(r"{{username}}", actual_username).replace(r"{{apiToken}}", actual_token).replace(
                    r"{{host}}", actual_host).replace(r"{{basePath}}", "") for item in obj]
            except Exception as e:
                # pass
                print(f"Following exception occured: {e}")
            process_list_of_dicts(
                lst=obj,
                actual_token=actual_token,
                actual_host=actual_host,
                actual_username=actual_username,

            )
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    update_placeholders(value)

    # Replace placeholders with actual key and token
    update_placeholders(content)

    # Write the updated content back to the file
    with open(f"./specs/{scenario}_oas.json", 'w') as json_file:
        json.dump(content, json_file, indent=2)
        print("Contents updated!")


def replace_credentials_salesforce_json(scenario, actual_domain, actual_version, actual_client_id, actual_client_secret,
                                        actual_access_token):
    # Open the JSON file and load the content
    with open(f"./specs/{scenario}_base.json", 'r') as json_file:
        content = json.load(json_file)

    def replace_values(d):
        for key, value in d.items():
            if isinstance(value, dict):
                replace_values(value)
            elif isinstance(value, str):
                d[key] = value.replace(r"{{base_url}}", actual_domain)
            elif isinstance(value, list):
                try:
                    # d[key] = [item.replace(r"{{username}}", actual_username).replace(r"{{apiToken}}", actual_token) for
                    #           item in value]
                    pass
                except Exception as e:
                    print(f"Following exception occured: {e}")

    def process_list_of_dicts(lst):
        for item in lst:
            if isinstance(item, dict):
                replace_values(d=item)

    def update_placeholders(obj):
        if isinstance(obj, list):
            try:
                # obj = [item.replace(r"{{username}}", actual_username).replace(r"{{apiToken}}", actual_token).replace(r"{{host}}", actual_host).replace(r"{{basePath}}", "") for item in obj]
                pass
            except Exception as e:
                # pass
                print(f"Following exception occured: {e}")
            process_list_of_dicts(lst=obj)
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    update_placeholders(value)

    # Replace placeholders with actual key and token
    update_placeholders(content)

    # Write the updated content back to the file
    with open(f"./specs/{scenario}_oas.json", 'w') as json_file:
        json.dump(content, json_file, indent=2)
        print(f"{scenario} Contents updated!")
