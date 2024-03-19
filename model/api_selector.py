from typing import Any, Dict, List, Optional, Tuple
import re
import logging

from langchain.chains.base import Chain
from langchain.chains.llm import LLMChain
from langchain.prompts.base import BasePromptTemplate
from langchain.prompts.prompt import PromptTemplate
from langchain.llms.base import BaseLLM

from utils import ReducedOpenAPISpec, get_matched_endpoint

logger = logging.getLogger(__name__)

icl_examples = {}

# Thought: I am finished executing the plan and have the information the user asked for or the data the used asked to create
# Final Answer: the final output from executing the plan. If the user's query contains filter conditions, you need to filter the results as well. For example, if the user query is "Search for the first person whose name is 'Tom Hanks'", you should filter the results and only output the first person whose name is 'Tom Hanks'.
API_SELECTOR_PROMPT = """You are a planner that plans a sequence of RESTful API calls to assist with user queries against an API.
Another API caller will receive your plan call the corresponding APIs and finally give you the result in natural language.
When you receive the data from the API call, you should always display the data as it is from the response.
The API caller also has filtering, sorting functions to post-process the response of APIs. Therefore, if you think the API response should be post-processed, just tell the API caller to do so.
If you think you have got the final answer, do not make other API calls and just output the answer immediately. For example, the query is search for a person, you should just return the id and name of the person.

----

Here are name and description of available APIs.
Do not use APIs that are not listed here. If the API path contains "{{}}", it means that it is a variable and you should replace it with the appropriate value. For example, if the path is "/users/{{user_id}}/tweets", you should replace "{{user_id}}" with the user id. "{{" and "}}" cannot appear in the url. Must replace the variables with the actual value when calling the api.

{endpoints}

----

Starting below, you should follow this format:

Background: background information which you can use to execute the plan, e.g., the id of a person, the id of tracks by Faye Wong. In most cases, you must use the background information instead of requesting these information again. For example, if the query is "get the poster for any other movie directed by Wong Kar-Wai (12453)", and the background includes the movies directed by Wong Kar-Wai, you should use the background information instead of requesting the movies directed by Wong Kar-Wai again.
User query: the query a User wants help with related to the API
API calling 1: the first api call you want to make. Note the API calling can contain conditions such as filtering, sorting, etc. For example, "GET /movie/18329/credits to get the director of the movie Happy Together", "GET /movie/popular to get the top-1 most popular movie". If user query contains some filter condition, such as the latest, the most popular, the highest rated, then the API calling plan should also contain the filter condition. If you think there is no need to call an API, output "No API call needed." and then output the final answer according to the user query and background information.
API response: the response of API calling 1
Instruction: Another model will evaluate whether the user query has been fulfilled. If the instruction contains "continue", then you should make another API call following this instruction.
... (this API calling n and API response can repeat N times, but most queries can be solved in 1-2 step)


{icl_examples}

You should use the values of paramters if specified in the available examples.
If you are getting the string with the description of how you will perform the specific task, you have to use those details as a parameter for calling desired API. For example if plan is to createa an event for date 12th december 2023, ending at 13th december 2023, you will replace these values with appropriate parameter variables while calling the API. If the task is to create a sheet with title "Gym Workout", pass the title in parameters of API call.


Begin!

Background: {background}
User query: {plan}
API calling 1: {agent_scratchpad}"""


class APISelector(Chain):
    llm: BaseLLM
    api_spec: ReducedOpenAPISpec
    scenario: str
    api_selector_prompt: BasePromptTemplate
    output_key: str = "result"

    def __init__(self, llm: BaseLLM, scenario: str, api_spec: ReducedOpenAPISpec) -> None:
        api_name_desc = [
            f"{endpoint[0]} {endpoint[1].split('.')[0] if endpoint[1] is not None else ''}" for endpoint in api_spec.endpoints]
        api_name_desc = '\n'.join(api_name_desc)
        api_selector_prompt = PromptTemplate(
            template=API_SELECTOR_PROMPT,
            partial_variables={"endpoints": api_name_desc,
                               "icl_examples": icl_examples[scenario]},
            input_variables=["plan", "background", "agent_scratchpad"],
        )
        super().__init__(llm=llm, api_spec=api_spec, scenario=scenario,
                         api_selector_prompt=api_selector_prompt)

    @property
    def _chain_type(self) -> str:
        return "ApiLLM API Selector"

    @property
    def input_keys(self) -> List[str]:
        return ["plan", "background"]

    @property
    def output_keys(self) -> List[str]:
        return [self.output_key]

    @property
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""
        return "API response: "

    @property
    def llm_prefix(self) -> str:
        """Prefix to append the llm call with."""
        return "API calling {}: "

    @property
    def _stop(self) -> List[str]:
        return [
            f"\n{self.observation_prefix.rstrip()}",
            f"\n\t{self.observation_prefix.rstrip()}",
        ]

    def _construct_scratchpad(
        self, history: List[Tuple[str, str]], instruction: str
    ) -> str:
        if len(history) == 0:
            return ""
        scratchpad = ""
        for i, (plan, api_plan, execution_res) in enumerate(history):
            if i != 0:
                scratchpad += "Instruction: " + plan + "\n"
            scratchpad += self.llm_prefix.format(i + 1) + api_plan + "\n"
            scratchpad += self.observation_prefix + execution_res + "\n"
        scratchpad += "Instruction: " + instruction + "\n"
        return scratchpad

    def _call(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        # inputs: background, plan, (optional) history, instruction
        if 'history' in inputs:
            scratchpad = self._construct_scratchpad(
                inputs['history'], inputs['instruction'])
        else:
            scratchpad = ""
        api_selector_chain = LLMChain(
            llm=self.llm, prompt=self.api_selector_prompt)
        api_selector_chain_output = api_selector_chain.run(
            plan=inputs['plan'], background=inputs['background'], agent_scratchpad=scratchpad, stop=self._stop)

        api_plan = re.sub(r"API calling \d+: ", "",
                          api_selector_chain_output).strip()

        logger.info(f"API Selector: {api_plan}")

        finish = re.match(r"No API call needed.(.*)", api_plan)
        if finish is not None:
            return {"result": api_plan}

        while get_matched_endpoint(self.api_spec, api_plan) is None:
            logger.info(
                "API Selector: The API you called is not in the list of available APIs. Please use another API.")
            scratchpad += api_selector_chain_output + \
                "\nThe API you called is not in the list of available APIs. Please use another API.\n"
            api_selector_chain_output = api_selector_chain.run(
                plan=inputs['plan'], background=inputs['background'], agent_scratchpad=scratchpad, stop=self._stop)
            api_plan = re.sub(r"API calling \d+: ", "",
                              api_selector_chain_output).strip()
            logger.info(f"API Selector: {api_plan}")

        return {"result": api_plan}
