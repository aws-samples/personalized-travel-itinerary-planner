import boto3
import time
from io import StringIO
from configparser import ConfigParser
import json
import os
import boto3
from langchain.chains import ConversationChain
from langchain.llms.bedrock import Bedrock
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

def get_bedrock():
    
    bconfig = ConfigParser()
    bconfig.read(os.path.join(os.path.dirname(__file__), 'data_feed_config.ini'))
    region = bconfig["GLOBAL"]["region"]
    
    bedrock = boto3.client(service_name='bedrock-runtime', region_name = region)

    return bedrock

def get_redshift_client(region): 
    
    client = boto3.client('redshift-data', region_name = region)

    return client

def get_user_data(user_id):
    config = ConfigParser()

    config.read(os.path.join(os.path.dirname(__file__), 'data_feed_config.ini'))
    
    db_user = config["GLOBAL"]["db_user"]
    workgroup = config["GLOBAL"]["workgroup"]
    secarn = config["GLOBAL"]["secret_arn"]
    database = config["GLOBAL"]["database_name"]
    region = config["GLOBAL"]["region"]
    
    client = get_redshift_client(region)


    query = f"""
    select u.u_full_name as full_name, u.u_first_name as first_name, 
    u.u_age as age, u.u_city as home_city, u.u_country as home_country, u.u_interest as hobbies_interest, u.u_fav_food as favorite_food,
    b.b_city as travel_city, b.b_country as travel_country, b.b_checkin as from_date, b.b_checkout as to_date
    from transactions.user_profile u
    left outer join transactions.hotel_booking b on b.b_user_id = u.u_user_id
    where u.u_user_id = {user_id}
    ORDER BY b.b_checkin;
    """
    print(query)

    execution_id = client.execute_statement(
        Database=database,
        Sql=query,
        SecretArn=secarn,
        WorkgroupName=workgroup,
        )['Id']
    print(f'Execution started with ID {execution_id}')

    
    status = client.describe_statement(Id=execution_id)['Status']
    while status not in ['FINISHED','ABORTED','FAILED']:
        time.sleep(10)
        status = client.describe_statement(Id=execution_id)['Status']
    print(f'Schema Query Execution {execution_id} finished with status {status}')
    
    
    if status == 'FINISHED':
        columns = [c['label'] for c in client.get_statement_result(Id=execution_id)['ColumnMetadata']]
        records = client.get_statement_result(Id=execution_id)['Records']
        print(f'Schema Query SUCCESS. Found {len(records)} records')
    else:
        print(f'Schema Query Failed with Error: {client.describe_statement(Id=execution_id)["Error"]}')
    
    if len(records) > 0:
        user_full_name = records[0][0]["stringValue"]
        user_first_name = records[0][1]["stringValue"]
        user_age = records[0][2]["longValue"]
        user_home_city = records[0][3]["stringValue"]
        user_home_country = records[0][4]["stringValue"]
        user_interests = records[0][5]["stringValue"]
        user_fav_food = records[0][6]["stringValue"]

    travel_itinerary = ''
    
    for rec in records: 
        travel_city = rec[7]["stringValue"]
        travel_country = rec[8]["stringValue"]
        from_date = rec[9]["stringValue"]
        to_date = rec[10]["stringValue"]
        travel_string = travel_city + ", " + travel_country + " from " + from_date + " to " + to_date + " \\n"
        travel_itinerary = travel_itinerary + travel_string

    prompt_initial_text = "You are a Personalized travel agent bot who can answer questions about user\'s upcoming travel that is already planned or you will help plan. You will take into account the  user\'s personal data like home city, age, hobbies, interests and favorite food while answering questions. Date format is YYYY-MM-DD. If you do not know the answer you response should be 'Sorry I'm Unsure of that. Is there something else I can help you with?'. \\n"
    
    if len(records) > 0:
        user_intro_text = str(user_full_name) + " who is of age " + str(user_age) + " , lives in " + str(user_home_city) + ", " + str(user_home_country) + " has hobbies or is interested in " + str(user_interests) +". " + str(user_first_name) + "\'s favorite food is " + str(user_fav_food) + ".\\n"
    else: 
        user_intro_text = "This is a new user in our system and we do not have any information about this user"
    
    if len(records) > 0:
        if travel_itinerary:
            travel_itinerary_text = "Below are the list of cities " + str(user_first_name) + " will be travelling to. \\n" + str(travel_itinerary)
        else:
            travel_itinerary_text = str(user_first_name) + " does not have any upcoming travel that we know of."
    else: 
        travel_itinerary_text = ' '

    if len(records) > 0:
        addtl_instructions = "Can you answer the question mentioned above, considering "+str(user_first_name)+ "'s hobbies, interests, favorite food and travel plans mentioned above? Do not repeat the cities and countries that "+ str(user_first_name)+" is already travelling to. Start your response with Hello "+str(user_first_name) 
    else: 
        addtl_instructions = "Can you answer the question mentioned above? Start your response with Hello "

    prompt_text = prompt_initial_text+user_intro_text+travel_itinerary_text
    
    prompt_text = prompt_text.replace('"', '\\"')

    prompt_format =    """
    Current conversation:
    {history}

    Human: {input}
    AI:
    """

    prompt_template = prompt_text + prompt_format + addtl_instructions
    
    return prompt_template

def get_bedrock_chain(user_id):
    profile = "default"

    bedrock = get_bedrock()

    modelId = 'anthropic.claude-v2'
    accept = 'application/json'
    #accept  = "*/*"
    contentType = 'application/json'

    claude_llm = Bedrock(
        model_id=modelId, client=bedrock, credentials_profile_name=profile
    )
    claude_llm.model_kwargs = {"temperature": 0.5, "max_tokens_to_sample": 4096}

    prompt_template = get_user_data(user_id)

    pt = PromptTemplate(
        input_variables=["history", "input"], template=prompt_template
    )

    memory = ConversationBufferMemory(human_prefix="Human", ai_prefix="AI")
    conversation = ConversationChain(
        prompt=pt,
        llm=claude_llm,
        verbose=True,
        memory=memory,
    )

    return conversation

def exec_chain(ch, pt):
    token_ct = ch.llm.get_num_tokens(pt)
    return ch({"input": pt}), token_ct
