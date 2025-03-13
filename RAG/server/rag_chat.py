import psycopg
import openai
from openai import OpenAI
import tiktoken
from rag_openai import *
import logging
import json
from rag_embed import *




'''
REST stateless function that receives:
- config_values:    backend configuration 
- conn: DB connection to the DB (not only to server)
- user_values: user settings TBD, such as tags that user has access to
- conversation: if session is to be contunued the JSON containing USER/ASSISTANT SEQUENCE ref. OPENAI documentation at  
   https://platform.openai.com/docs/guides/text-generation#messages-and-roles
- returns plain text for the answer
- it does not update DB not updates the session. It is stateless and expects caller to keep info saved
'''
def chat_query(config_values, conn, user_values={}, prompt="", conversation=[]):
    system_message = f"""You are a friendly chatbot. You respond in a concise, technically credible tone. \
    Please use context information as source for information. Please do not invent information and do not provide generic answers. \
    If you do not know the precise answer - reply that you don't know. At the end of answer please show the list of sources used. \
    Once the answer is generated please analyze it agains the prompt and provide the answer goodness in therange from 0 to 1000, \
    printing is as Answer Reliability Rate / 1000"""
    delimiter = "```"
    # We use a delimiter to help the model understand the where the user_input starts and ends
    messages_init = [ {"role": "developer", "content": system_message} ]    
    messages = []
    messages.extend(messages_init)

    if conversation != "": #there is an old conversation to add first to messages
        messages.extend(conversation)

    emb=""
    assist_info=""
    
    logging.debug("get embedding for prompt..")
    emb=openai_generate_embedding(config_values, text=prompt)
            
    #here a lot of work extecped to improve the Retrieval phase, starting from BM25
                
 
    #here i need to filter the query basing on TAGS TBD
    if user_values.get("Use_RAG", False)==True:
        #debug print("now search for neighbors")
        neighbors=conn.execute(f"SELECT id FROM emb ORDER BY embedding <=> '{emb}' LIMIT {config_values['rag_number_of_vector_matches']}").fetchall()

    docs_id_set=set() #non repeatable set of IDs to retrieve content for

    
    if user_values.get("Use_RAG", False)==True:
        for neighbor in neighbors:
            docs_id_set.add(neighbor[0])

    extended_docs_list=sorted(docs_id_set)
    logging.debug(f"Extended docs list: {extended_docs_list}")

    
    docs_ids=str(extended_docs_list).replace('[','(').replace(']',')')

    logging.debug(f"Documents retrieved and extended: {extended_docs_list}")
    
    if docs_ids != "()":
        docs=conn.execute(f"SELECT id, source_ref, content FROM emb where id in {docs_ids}").fetchall()

        assist_info="\nPlease use the following data set as information for the query:\n"
        for doc in docs:    
            assist_info+=f"Source: '{doc[1]}', data: {doc[2]} \n"
        
        
    logging.debug("Prepare query to OpenAI")

    # Prepare messages to pass to model
    # We use a delimiter to help the model understand the where the user_input starts and ends
    
    prompt=[{"role": "user", "content": f"{delimiter}{prompt}{delimiter}{assist_info}"} ]
    messages.extend(prompt)
    logging.debug(f"Send the query: {str(messages)}")
    logging.info(f"Query length in tokens: {num_tokens_from_string(str(messages))}")
    
    resp=openai_get_completion_from_messages(config_values, messages)
    logging.debug(f"Answer: {str(resp)}")

    response=[]
    response.extend(prompt)
    response.extend([{"role": "assistant", "content": resp }])
   
    
    return response
    
'''
gets the prompt and returns list of keywords
'''
def get_keywords_from_prompt(config_values, prompt=""):
    system_message = f"""Please extract up to ten non repeatable most important keywords from the prompt, answering with keywords separated by comma without adding anything else. Consider that these keywords will be used to search the relevant material in the texts. Consider unknown words and acronyms as keywords."""
    delimiter = "```"
    # We use a delimiter to help the model understand the where the user_input starts and ends
    messages_init = [ {"role": "developer", "content": system_message} ]    
    messages = []
    messages.extend(messages_init)

    logging.debug("Prepare keywords query to OpenAI")

    prompt=[{"role": "user", "content": f"{delimiter}{prompt}{delimiter}"} ]
    messages.extend(prompt)
    logging.debug(f"Send the query: {str(messages)}")

    resp=openai_get_completion_from_messages(ragdb_globals.config_values, messages)
    logging.debug(f"Answer: {str(resp)}")
    if len(resp.strip())==0:
        return []
    else:    
        return resp.split(",")



