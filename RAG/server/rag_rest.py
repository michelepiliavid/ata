import psycopg

import os
   
from rag_config import *


from flask import Flask, request,jsonify        # pip install flask
from flask_restful import Resource, Api #pip install flask-restful
import sys
import threading #pip install threading
import requests
import logging

import json
from flask_cors import CORS
from rag_chat import *
import rag_globals

import time


class rest_get_server_shutdown(Resource):
    def get(self):
        os._exit(0)
        raise RuntimeError("Server going down")


#receives the ?prompt= and ?session=session_id if session is to be followed, ?user=user id
#returns answer and updates session info in database with question and answer i json as answer:text
#example: https://server:port?prompt=ciao&session=1234&user=5678
class rest_get_simple_answer(Resource):
    def get(self):  #simple request, passing query string in prompt parameter in URL
        prompt = request.args['prompt'] if 'prompt' in request.args else ''
        session_id = request.args['session'] if 'session' in request.args else ''
        user_id = request.args['user'] if 'user' in request.args else ''

        try:    
            conn = psycopg.connect(dbname=rag_globals.config_values['dbname'], user=rag_globals.config_values['dbuser'], password=rag_globals.config_values['dbpassword'], host=rag_globals.config_values['dbhost'], autocommit=True)
        except:
            logging.critical("Cannot connect to DB")
            return "Exception: Cannot connect to DB", 500
            
        #let's retrieve conversation using session id
        l_conversation=[]
        if session_id!='':
            try:        
                rs=conn.execute('SELECT json_session FROM sessions WHERE id=%s',(session_id,)).fetchall()
                if len(rs) >0:
                    l_conversation=rs[0][0]
            except:
                logging.critical(f"Cannot retrieve session {session_id}")
                return "Exception: Cannot retrieve the session", 400
        logging.debug(l_conversation)
        
        #TBD extract tags using user_id?
        
        try:
            resp=chat_query(rag_globals.config_values, conn, user_values={"Use_RAG":True}, prompt=prompt, conversation=l_conversation)
        except:
            logging.critical(f"chat_query failed")
            return "Exception: chat_query failed", 500
        
        #let's keep tracking of all conversations
        #conn.execute('INSERT INTO sessions (text_session) VALUES (%s)',(json.dumps(resp),))
        
        #let's join cexisting conversation with new one and write it backend
        if session_id!='':
            c=[]
#            c.extend(json.loads(s_conversation))
            c.extend(l_conversation)
            c.extend(resp)
            try:
                conn.execute('UPDATE sessions SET json_session=%s WHERE id=%s',(json.dumps(c),session_id))
#            conn.execute('UPDATE sessions SET json_session=%s WHERE id=%s',(c,session_id))
            except:
                logging.critical(f"Cannot update session")
                return "Exception: Cannot update session", 500
                
        try:
            conn.close()
        except:
            logging.critical("Cannot close DB connector")

        return resp[1], 200
        


class rest_put_generate_embeddings_for_file(Resource):
    def put(self): 

        filename = request.headers.get("X-Filename", "")
        if filename == "":
            filename = request.headers.get("Filename", "")
        if filename == "":
            filename = "upload.bin"
        #print (request.base_url)

        if not request.data:
            return {"error": "No binary data received"}, 400

        # Save the binary file
        try:
            UPLOAD_FOLDER = "./uploads"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the upload directory exists
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(file_path, "wb") as f:
                f.write(request.data)
            embed_file(os.path.normpath(file_path))
        except Exception as e:
            os.remove(os.path.normpath(file_path))
            raise Exception(e)
        finally:
            os.remove(os.path.normpath(file_path))
        
        
        return {"message": f"File '{filename}' uploaded successfully!", "path": file_path}, 200
        


def flaskThread():
    try:
        logging.info("REST server started")
        flask_app.run(host="0.0.0.0", port=int(rag_globals.config_values['rest_port']))
    except Exception as e:
        logging.critical("Exception ", e)
        pass
      




def start_flask():
    global flask_app 
    flask_app = Flask(__name__)
    flask_api = Api(flask_app)
    #flask_app.debug = True #config_values['debug_mode']
    # enable CORS
    CORS(flask_app, resources={r'/*': {'origins': '*'}})
    flask_api.add_resource(rest_get_server_shutdown, rag_globals.config_values['rest_get_server_shutdown'])
    flask_api.add_resource(rest_get_simple_answer, rag_globals.config_values['rest_get_simple_answer'])
    flask_api.add_resource(rest_put_generate_embeddings_for_file, rag_globals.config_values['rest_put_generate_embeddings_for_file'])

    logging.info("Starting REST server")
    t1 = threading.Thread(target=flaskThread)
    t1.daemon = True #thread dies if main dies
    t1.start()

