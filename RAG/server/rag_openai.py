import openai
from openai import OpenAI
import logging
#from ragb_config import *


def openai_generate_embedding(config_values, text):
    try:
        logging.debug(f"OPENAI Generate embedding called for: {text}")
        client = OpenAI(api_key=config_values['openai_api_key'])
        response = client.embeddings.create(input=text, model=config_values['openai_embedding_model'])
        return response.data[0].embedding
    except ValueError as ex:
        ex.add_note('openai_generate_embedding exception')
        logging.critical(ex)
        raise 
    

def openai_get_completion_from_messages(config_values, messages):
    try:
        client = OpenAI(api_key=config_values['openai_api_key'])
        response = client.chat.completions.create(
            model=config_values['openai_model'],
            messages=messages,
            temperature=float(config_values['openai_temperature']),
            max_tokens=int(config_values['openai_maxtokens'])
        )
        logging.debug(f"OPENAI get completion: {response.choices[0].message.content}")
        return response.choices[0].message.content
    except ValueError as ex:
        ex.add_note('openai_get_completion_from_messages exception')
        logging.critical(ex)
        raise 