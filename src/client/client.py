import os
import datetime
import time

from fireworks.client import Fireworks
from client.keys import FW_API_KEYS
from config import LLM_QUERY_TRY_LIMIT_PER_KEY, LLM_DEFAULT_MODEL
from utils.io_utils import save_data_to_json, load_json_data
from utils.tokens_utils import count_tokens

def make_fw_client(api_key: str):
    return Fireworks(api_key=api_key)

def save_query(system_prompt, user_prompt, model, grammar, chat_completion, generation_time):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    query_path = os.path.join(BASE_DIR, "queries", f"query_{now}.json")
    query = {
        "time" : now,
        "system_prompt" : system_prompt,
        "user_prompt" : user_prompt,
        "model" : model,
        "grammar" : grammar,
        "content" : chat_completion.choices[0].message.content, 
        "generation_time": generation_time,
        "prompt_tokens" : chat_completion.usage.prompt_tokens, 
        "completion_tokens" : chat_completion.usage.completion_tokens, 
        "total_tokens" : chat_completion.usage.total_tokens
    }

    token_consumption_path = os.path.join(BASE_DIR, f"token_consumption.json")
    token_consumption = load_json_data(token_consumption_path)
    token_consumption.append((chat_completion.usage.prompt_tokens, chat_completion.usage.completion_tokens, chat_completion.usage.total_tokens))

    save_data_to_json(token_consumption, token_consumption_path)
    save_data_to_json(query, query_path)

def llm_query(system_prompt, user_prompt, model = LLM_DEFAULT_MODEL, grammar = None):
    for api_key in FW_API_KEYS:
        for i in range(LLM_QUERY_TRY_LIMIT_PER_KEY):
            try:
                start_time = time.time()
                client = make_fw_client(api_key)
                if grammar is not None:
                    chat_completion = client.chat.completions.create(
                        model=model,
                        response_format={"type": "grammar", "grammar": grammar},
                        messages=[
                            {"role": "system", "content": system_prompt,},
                            {"role": "user", "content": user_prompt},
                        ], 
                        temperature = 0
                    )
                else:
                    chat_completion = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt,},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature = 0
                    )

                # system_prompt_tokens = count_tokens(system_prompt)
                # user_prompt_tokens = count_tokens(user_prompt)
                # prompt_tokens_pred = system_prompt_tokens+user_prompt_tokens
                # prompt_tokens_gt = chat_completion.usage.prompt_tokens
                # print(prompt_tokens_pred+8, prompt_tokens_gt)

                # completion_tokens_pred = count_tokens(chat_completion.choices[0].message.content)
                # completion_tokens_gt = chat_completion.usage.completion_tokens
                # print(completion_tokens_pred+4, completion_tokens_gt)
                # print()
                    
                save_query(system_prompt, user_prompt, model, grammar, chat_completion, time.time() - start_time)
                return chat_completion
            except Exception as e:
                print(type(e), e)
                time.sleep(3)
    return None