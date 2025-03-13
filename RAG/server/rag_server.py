import psycopg
import time
import openai
from openai import OpenAI
import os
from pgvector.psycopg import register_vector
import tiktoken

import pandas as pd
import numpy as np

import rag_globals    
from rag_config import *
from rag_openai import *
from rag_readers import *
from rag_chat import *
from rag_embed import *


import sys
#import threading #pip install threading
from urllib.parse import urljoin
import requests
import logging
import traceback
from logging.handlers import RotatingFileHandler
import json
import hashlib
import ast
#from flask_cors import CORS
from rag_rest import start_flask

def get_doc_links_from_base_url(base_url):
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    links = [urljoin(base_url, a.get('href')) for a in soup.find_all('a')]
    pdf_links=[]
    for link in links:
        if link.endswith(".pdf"):
            pdf_links.append(link)
    return pdf_links
    
def download_file_into(file_url, target_folder="."):
#IT does NOT WORK WITH AVID KNOWLEDGEBASE. HTML is retrieved, probably javascript needed to process it

    try:
        target_file=target_folder+"/"+os.path.basename(file_url)
#       response = requests.get(file_url, stream=True)
        response = requests.get(file_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.find('iframe'):
            iframe = soup.find('iframe')
            url = iframe['src']
            filename = urllib.parse.unquote(url)
            filename = filename.rsplit('/', 1)[-1]
            logging.debug("real filename is "+filename)
            response = requests.get(filename)
        with open(target_file, mode="wb") as file:
            file.write(response.content)
#            for chunk in response.iter_content(chunk_size=10 * 1024):
#                file.write(chunk)
    except Exception as e:
        logging.critical(f"Exception : {e} on file {file_url}")
    
def concatena_stringhe_sovrapposte(str1, str2):
    """
    Concatena due stringhe rimuovendo la parte sovrapposta.

    Args:
        str1: La prima stringa.
        str2: La seconda stringa.

    Returns:
        La stringa concatenata senza la parte sovrapposta.
    """

    for i in range(min(len(str1), len(str2)), 0, -1):
        if str1[-i:] == str2[:i]:
            return str1 + str2[i:]
    return str1 + str2



def chat():
    global use_RAG

    global use_RAG_source
    global use_prompt
    global use_prompt_emb
    global if_skip_already_processed
    global if_keep_session

    system_message = f"""You are a friendly chatbot. You respond in a concise, technically credible tone. Please use context information as source for information. Please do not invent information and do not provide generic answers. If you do not know the precise answer - please answer that you don't know. At the end of answer please show the list of sources used from the context. """
    delimiter = "```"
    # We use a delimiter to help the model understand the where the user_input starts and ends
    messages_init = [ {"role": "developer", "content": system_message} ]    
    messages = []
    messages.extend(messages_init)
    
    while True:
        print("\n\nInsert number or prompt:")
        print("1 - Toggle RAG, currently it is:", use_RAG,",  RAG_source=", use_RAG_source)

       
        print("3 - Index(encode) PDF/TXT/HTM/HTML/DOCX/XLSX/PPTX in PDF folder")
        print("31 - Toggle whether skip already processed files, now is:",if_skip_already_processed)

        print("4 - Show indexed items in the database")
        print("5 - Choose already encoded prompt to reuse, now it is: ",use_prompt)
        print("60 - Toggle session alive keeper (remember previuos answers), now is:", if_keep_session)
        print("62 - Print current messages sequence")

        print("9 - Exit")
        
        if os.isatty(sys.stdin.fileno())==True:
            prompt = input("Prompt (press Enter to use chosen prompt):\n\n")
        else:
            while True:
                time.sleep(1000)
        print("\n")
        match prompt:
            case "1":
                use_RAG=not(use_RAG)
                if use_RAG==True:
                    use_RAG_source=input("Insert RAG reference to use (filename) or Enter to use entire database (maybe less precise): ")

            case "3":
                    #for each *.txt *.pdf file in folder delete first from database then split refine and embed it
                    #means convert content of any file in text then refine then embed
                    files=[]
                    files+=glob.glob("PDF/*.pdf")
                    files+=glob.glob("PDF/*.txt")
                    files+=glob.glob("PDF/*.htm*")
                    files+=glob.glob("PDF/*.docx")
                    files+=glob.glob("PDF/*.xlsx")
                    files+=glob.glob("PDF/*.pptx")
                    
                    for file in files:
                        if if_skip_already_processed==True:
                            rs=conn.execute('SELECT count(*) FROM emb WHERE source_ref=%s',(file,)).fetchall()
                            if rs[0][0]>0:
                                print("Skipping: "+file)
                                continue
                        embed_file(file)
            case "31":
                if_skip_already_processed=not(if_skip_already_processed)
                    
            case "4":
                rs=conn.execute('SELECT source_ref, count(*) FROM emb GROUP BY source_ref ORDER BY source_ref ASC').fetchall()
                for a in rs:
                    print(a)
            case "5":
                rs=conn.execute("SELECT id, content FROM emb WHERE source_ref='prompt' ORDER BY id ASC ").fetchall()
                for a in rs:
                    print(a[0], "-", a[1])
                id=input("Select id or 0 to drop default prompt: ")
                if id=="0":
                    use_prompt=""
                else:
                    rs=conn.execute('SELECT content, embedding FROM emb WHERE id='+id).fetchall()
                    use_prompt=rs[0][0]
                    use_prompt_emb=rs[0][1]
            case "60":
                if_keep_session=not(if_keep_session)
                if if_keep_session==False:
                    messages = []
                    messages.extend(messages_init)
                    print("History cleared up")
#                print(messages)
            case "62":
                print("\n"+str(messages)+"\n")

            case "9":
                os._exit(0)
            case  _:
                resp=chat_query(rag_globals.config_values, conn, user_values={"Use_RAG":use_RAG}, prompt=prompt, conversation="")
#                resp=get_keywords_from_prompt(config_values=config_values, prompt=prompt)

                print("\nAnswer:")
                print("------------------------------------")
                print(resp[1]['content'])
                print("------------------------------------")


try:
    
#    create_config("rag.ini") #creates config if not exists
    rag_globals.config_values=read_config("rag.ini")

    logging.basicConfig(
        level=rag_globals.config_values['log_level'],
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        encoding='utf-8',
        handlers=[
#            logging.FileHandler(config_values['log_logfile']),
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler(rag_globals.config_values['log_logfile'], maxBytes=(1048576*5), backupCount=7)
        ]
    )

    logging.info('Config loaded and log started')

    start_flask()    
  
    N_DIM = 1536
    use_RAG=False
 
    
    use_RAG_source=""
    if_record_prompt_embeddings=False
    use_prompt=""
    use_prompt_emb=""
    if_skip_already_processed=True
    if_keep_session=True

    conn = psycopg.connect(dbname=rag_globals.config_values['dbname'], user=rag_globals.config_values['dbuser'], password=rag_globals.config_values['dbpassword'], host=rag_globals.config_values['dbhost'], autocommit=True)

    #conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
    #register_vector(conn)
    #conn.execute('DROP TABLE IF EXISTS emb')
    #conn.execute('CREATE TABLE IF NOT EXISTS emb (id bigserial PRIMARY KEY, source_ref text, content text, embedding vector(1536))')
    #conn.execute('CREATE INDEX IF NOT EXISTS idx_emb ON emb USING hnsw (embedding vector_l2_ops)')

    #conn.execute('CREATE EXTENSION IF NOT EXISTS pg_search')
    #conn.execute("CREATE INDEX IF NOT EXISTS bm25_idx ON emb USING bm25 (id, content) WITH (key_field='id')"
    chat()
except Exception as e :
    logging.critical("exception", e)
    logging.critical(traceback.format_exc())
    logging.critical("exiting main thread")
    os._exit(0)

    