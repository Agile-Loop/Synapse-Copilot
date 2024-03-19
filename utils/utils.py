import os
import re
import json
import logging
from logging.handlers import BaseRotatingHandler
from colorama import Fore

from langchain.agents.agent_toolkits.openapi.spec import ReducedOpenAPISpec


class ColorPrint:
    def __init__(self):
        self.color_mapping = {
            "Planner": Fore.RED,
            "API Selector": Fore.YELLOW,
            "Caller": Fore.BLUE,
            "Parser": Fore.GREEN,
            "Code": Fore.WHITE,
        }

    def write(self, data):
        module = data.split(':')[0]
        if module not in self.color_mapping:
            print(data, end="")
        else:
            print(self.color_mapping[module] + data + Fore.RESET, end="")


def get_matched_endpoint(api_spec: ReducedOpenAPISpec, plan: str):
    if "https" not in plan:
        pattern = r"\b(GET|POST|PATCH|DELETE|PUT)\s+(/\S+)*"
    else:
        pattern = r"\b(GET|POST|PATCH|DELETE|PUT)\s+https?://\S+?(/\S+)"
    matches = re.findall(pattern, plan)
    print(f"UTILS: PLAN 27: {plan}")
    print(f"UTILS: MATCHES 29: {matches}")
    routes = [route for method, route in matches]
    print(f"RAW routes: {routes}")
    plan_endpoints = [f"{method} {route.split('?')[0]}" for method, route in matches]
    # plan_endpoints = [
    #     f"{method} {route.split("?")[0]}"
    #     # "{method} {route}".format(method=method, route=route.split("?")[0])
    #     for method, route in matches
    # ]
    spec_endpoints = [item[0] for item in api_spec.endpoints]

    matched_endpoints = []
    
    print("UTILS: PLAN ENDPOINTS 32:")
    print(plan_endpoints)
    print("\n\n")
    
    print("UTILS: SPEC ENDPOINTS 36:")
    print(spec_endpoints)
    print("\n\n")

    for plan_endpoint in plan_endpoints:
        if plan_endpoint in spec_endpoints:
            matched_endpoints.append(plan_endpoint)
            continue
        for name in spec_endpoints:
            arg_list = re.findall(r"[{](.*?)[}]", name)
            pattern = name.format(**{arg: r"[^/]+" for arg in arg_list}) + '$'
            if re.match(pattern, plan_endpoint):
                matched_endpoints.append(name)
                break

    if len(matched_endpoints) == 0:
        return None
        # matched_endpoints = ['GET /api/v2/team/9008245063/space', 'Non Genuine']
        # return ['GET /api/v2/team/9008245063/space']
        # raise ValueError(f"Endpoint {plan_endpoint} not found in API spec.")
    
    print("UTILS: MATCHED ENDPOINTS 57:")
    print(matched_endpoints)
    print("\n\n")

    return matched_endpoints


def simplify_json(raw_json: dict):
    if isinstance(raw_json, dict):
        for key in raw_json.keys():
            raw_json[key] = simplify_json(raw_json[key])
        return raw_json
    elif isinstance(raw_json, list):
        if len(raw_json) == 0:
            return raw_json
        elif len(raw_json) == 1:
            return [simplify_json(raw_json[0])]
        else:
            return [simplify_json(raw_json[0]), simplify_json(raw_json[1])]
    else:
        return raw_json


def fix_json_error(data: str, return_str=True):
    data = data.strip().strip('"').strip(",").strip("`")
    try:
        json.loads(data)
        return data
    except json.decoder.JSONDecodeError:
        data = data.split("\n")
        data = [line.strip() for line in data]
        for i in range(len(data)):
            line = data[i]
            if line in ['[', ']', '{', '}']:
                continue
            if line.endswith(('[', ']', '{', '}')):
                continue
            if not line.endswith(',') and data[i + 1] not in [']', '}', '],', '},']:
                data[i] += ','
            if data[i + 1] in [']', '}', '],', '},'] and line.endswith(','):
                data[i] = line[:-1]
        data = " ".join(data)
        
        if not return_str:
            data = json.loads(data)
        return data
