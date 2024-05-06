import boto3
import time
from io import StringIO
#import pandas as pd
from configparser import ConfigParser
import json
import os

config = ConfigParser()
    
config.read(os.path.join(os.path.dirname(__file__), 'data_feed_config.ini'))
db_user = config["GLOBAL"]["db_user"]
workgroup = config["GLOBAL"]["workgroup"]
secarn = config["GLOBAL"]["secret_arn"]
database = config["GLOBAL"]["database_name"]
region_name = config["GLOBAL"]["region"]
iam_role = config["GLOBAL"]["iam_role_arn"]

client = boto3.client('redshift-data', region_name = region_name)


def execute_query(query):
    execution_id = client.execute_statement(
        Database=database,
        WorkgroupName=workgroup,
        SecretArn=secarn,
        Sql=query
    )['Id']
    print(f'Execution started with ID {execution_id}')
    status = client.describe_statement(Id=execution_id)['Status']
    while status not in ['FINISHED','ABORTED','FAILED']:
      time.sleep(10)
      status = client.describe_statement(Id=execution_id)['Status']
    print(f'Query Execution {execution_id} finished with status {status}')
    return status

schema_query = """
create schema transactions authorization awsuser
"""

user_query = """
CREATE TABLE transactions.user_profile 
(
  u_user_id     VARCHAR(50) NOT NULL,
  u_full_name       VARCHAR(50) NOT NULL,
  u_first_name        VARCHAR(30),
  u_last_name    VARCHAR(30) ,
  u_city      VARCHAR(30) ,
  u_country       VARCHAR(20) ,
  u_age            INTEGER,
  u_interest        VARCHAR(200) ,
  u_fav_food        VARCHAR(200)
)
"""
booking_query = """
CREATE TABLE transactions.hotel_booking 
(
  b_user_id     INTEGER NOT NULL,
  b_checkin       DATE NOT NULL,
  b_checkout        DATE,
  b_device_class    VARCHAR(30) ,
  b_affiliate_id      VARCHAR(20) ,
  b_utrip_id       VARCHAR(20) ,
  b_city_id        VARCHAR(20) ,
  b_city        VARCHAR(30),
  b_country     VARCHAR(30)
)
"""

load_user_data = f"""
copy transactions.user_profile  from 's3://redshift-blogs/genai-prompt-engineering/travel-data/user_profile/' 
IAM_ROLE '{iam_role}'
FORMAT AS PARQUET
"""

load_booking_data = f"""
copy transactions.hotel_booking  from 's3://redshift-blogs/genai-prompt-engineering/travel-data/hotel_booking/' 
IAM_ROLE '{iam_role}'
FORMAT AS PARQUET
"""

schema_query_status = execute_query(schema_query)

if schema_query_status == 'FINISHED':
    user_query_status = execute_query(user_query)
    booking_query_status = execute_query(booking_query)
    if user_query_status == 'FINISHED':
       load_user_status = execute_query(load_user_data)
       if load_user_status == 'FINISHED':
          print('User profile data was successfully loaded')
    if booking_query_status == 'FINISHED':
       load_booking_status = execute_query(load_booking_data)
       if load_booking_status == 'FINISHED':
          print('Hotel booking data was successfully loaded')

