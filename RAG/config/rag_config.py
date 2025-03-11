import os
import logging
import configparser #pip install configparser

def create_config(filename='ragdb.ini'):  #returns the vocabulary of key value pairs
    
    #default empty config values
    config_values = {
        'debug_mode': False,
        'log_level': 'ERROR',
        'log_logfile': 'rag.log',
        'dbname': '#DBNAME#',
        'dbhost': '#DBHOST#',
        'dbuser': '#DBUSER#',
        'dbpassword': '#DBPASSWORD#',
        'rag_number_of_vector_matches': "5",
        'openai_api_key': "#OPENAI_API_KEY#",
        'openai_model': 'gpt-4o-mini',
        'openai_embedding_model': 'text-embedding-3-small',
        'openai_maxtokens': '1000',
        'openai_temperature': '1',
        'openai_vector_length': '1536',  
        'rest_port': '5000',
        'rest_get_server_shutdown': 'rest/server/shutdown', #server definitive shutdown
        'rest_put_generate_embeddings_for_file': '/rest/embeddings/put_generate_emb_for_file', #PUT passing filename field and content field the binary file content, returns embeddings list and chunks
        'rest_get_simple_answer': '/rest/conversation/get_simple_answer',         #GET passing prompt parameters in url. Answers with OPENAI answer
        'rest_post_complex_conversation': '/rest/conversation/post_complex_conversation'        #POST passing datafields: prompt, tags, old conversation(session). Retuns answer
        
 }

    # Write the configuration to a file if not exists
    if not os.path.isfile(filename):
        write_config(config_values)
    
    return config_values

def read_config(filename='rag.ini'):
    # Create a ConfigParser object
    config = configparser.ConfigParser()

    config_values=create_config() #creates empty standard config
    
    # Read the configuration file
    config.read(filename)


    #need to iterate on standard config keys and retrieve them from config read
    for key in config_values.keys():
        try:
            config_values[key]=config.get('SETTINGS', key)
        except:
            pass
    return config_values
    
def write_config(config_values, filename='rag.ini'):
    # Create a ConfigParser object
    config = configparser.ConfigParser()

    # Add sections and key-value pairs
    config['SETTINGS']=config_values
    
    with open(filename, 'w') as configfile:
        config.write(configfile)
