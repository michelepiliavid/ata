import psycopg
import os
import tiktoken
import rag_globals    
from  rag_readers import *
import sys
import logging
import json
import hashlib


def generate_embeddings(config_values, text_chunks):
    embeddings = []
    i=0
    for chunk in text_chunks:
        logging.debug("\r"+str(i)+" of "+str(len(text_chunks)), end="")
        i+=1
        embeddings.append(openai_generate_embedding(config_values, chunk))
    
    return embeddings
    
def insert_embeddings(conn, id_documents, source_ref, text_chunks, embeddings):
    for chunk, embedding in zip(text_chunks, embeddings):
        conn.execute('INSERT INTO emb (id_documents, source_ref, content, embedding) VALUES (%s, %s, %s, %s)', (id_documents, source_ref, chunk, embedding))

# Calculate number of tokens for a string
def num_tokens_from_string(string: str, encoding_name = "cl100k_base"):
    if not string:
        return 0
    # Returns the number of tokens in a text string
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def get_file_hash(file):

    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!

    md5 = hashlib.md5()
    with open(file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()
    


def embed_file(conn, file):
#first read a file into text, it depends on file type
#now refine and dehyphenate it
    text=""
    file_hash=get_file_hash(file)
    logging.debug("MD5: "+file_hash)

    try:
        match os.path.splitext(file)[1].lower():
            case ".pdf":
                text=readers.read_pdf(file)
            case ".txt":
                text=readers.read_txt(file)
            case ".xlsx":
                text=readers.read_xls(file)
            case ".docx":
                text=readers.read_docx(file)
            case ".htm":
                text=readers.read_html(file)
            case ".html":
                text=readers.read_html(file)
            case ".pptx":
                text=readers.read_pptx(file)

        #here we can print embedding cost and ask for confirmation
        # Assumes we're using the text-embedding-ada-002 model
        # See https://openai.com/pricing
        if text!="" :
            cost=num_tokens_from_string(text)/1000*0.0001
            text_chunks=readers.split_text(text)
            #remove from database
            logging.debug("                                      "+file,end=" ")
            embeddings=generate_embeddings(conn, text_chunks)
            #need to verify whether document is already present and delete it before inserting 
            logging.debug("delete embeddings, hash=",file_hash)
            conn.execute('DELETE FROM emb WHERE emb.id_documents = (SELECT documents.id FROM documents WHERE documents.hash=%s)', (file_hash,))

            logging.debug("delete doc, hash=",file_hash)
            conn.execute('DELETE FROM documents WHERE documents.hash=%s', (file_hash,))
            #now create document and use its new ID 
            logging.debug("insert doc")

            conn.execute('INSERT INTO documents (document_name, hash) VALUES (%s, %s)', (file, file_hash))
 
            logging.debug("retrieving document id")
 
            ids=conn.execute("SELECT id FROM documents WHERE hash=%s", (file_hash, )).fetchall()

            logging.debug("id= "+str(ids[0][0]))
            insert_embeddings(conn, id_documents=ids[0][0], source_ref=file, text_chunks=text_chunks, embeddings=embeddings)
            logging.info(" .Processed, cost=$"+str(round(cost,5)))  
    except Exception as e:
        logging.critical(f"Exception : {e} on file {file}")
            


