from helper import *
# import mysql.connector
import random
import os
logger = logging.getLogger()
from fastapi import FastAPI, status, Query, Depends

app = FastAPI()

SCENARIOS = [
    "trello",
]
async def validate_credentials(
        api_key: str = Query(..., description="The API key for the selected scenario"),
        api_token: str = Query(..., description="The API token for the associated application")
):
    """Here the necessary validation of the provided credentials will be made and 
       if the user information fails to validate, the appropriate exception will be generated. 
       If it runs successfully, it will return true"""
    
    os.environ["TRELLO_API_KEY"] = api_key
    os.environ["TRELLO_TOKEN"] = api_token
    
    return True


@app.post("/trello_interaction/", status_code=status.HTTP_200_OK)
async def handle_interaction(
    scenario: str = Query(..., description="The selected scenario"),
    validated_credentials: bool = Depends(validate_credentials),
    query: str = Query(..., description="The query related to the scenario")
):
    config = yaml.load(open("config.yaml", "r"), Loader=yaml.FullLoader)
    os.environ["OPENAI_API_KEY"] = config["openai_api_key"]

    logging.basicConfig(
        format="%(message)s",
        handlers=[logging.StreamHandler(ColorPrint())],
    )
    logger.setLevel(logging.INFO)


    if scenario not in SCENARIOS:
        # raise ValueError(f"Unsupported scenario: {scenario}")
        return {"error": "Invalid scenario"}

    api_spec, headers = None, None

    api_spec, headers = process_spec_file(
        file_path="specs/trello_oas.json", 
        token=os.environ["TRELLO_TOKEN"], 
        key=os.environ["TRELLO_API_KEY"]
    )

    query_example = "Create a new board with name 'abc_board'"
    
    replace_api_credentials(
        model="api_selector", 
        scenario=scenario, 
        actual_key=os.environ["TRELLO_API_KEY"],
        actual_token=os.environ["TRELLO_TOKEN"]
    )
    replace_api_credentials(
        model="planner", 
        scenario=scenario, 
        actual_key=os.environ["TRELLO_API_KEY"],
        actual_token=os.environ["TRELLO_TOKEN"]
    )

    populate_api_selector_icl_examples(scenario=scenario)
    populate_planner_icl_examples(scenario=scenario)
    
    requests_wrapper = Requests(headers=headers)
    
    llm = OpenAI(model_name="gpt-4", temperature=0.0, max_tokens=700)
    api_llm = ApiLLM(
        llm,
        api_spec=api_spec,
        scenario=scenario,
        requests_wrapper=requests_wrapper,
        simple_parser=False,
    )

    print(f"Example instruction: {query_example}")
    
    if not query:
        query = query_example

    logger.info(f"Query: {query}")

    start_time = time.time()
    result = api_llm.run(query)
    # print(f"RESULT: {result}")
    logger.info(f"Execution Time: {time.time() - start_time}")

    response = {
        "scenario": scenario,
        "query": query,
        "model_response": f"Model result: '{result}'"
    }

    return response
