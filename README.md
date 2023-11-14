# personalized-travel-itinerary-planner


This solution contains two major components. At first, we will extract the user’s information like Name, location, hobbies, interests and Favourite food etc along with their upcoming travel booking details. With this information we will stitch a user prompt together and pass it to Amazon Bedrock/Anthropic Claude LLM to obtain a personalized travel itinerary that the Customers can use. Below architecture diagram provides us a high level overview of the workflow and the components involved in this architecture. 

<img src="docs/Architecture_Diagram.jpg" alt="Architecture Diagram" width="400"/>

We will obtain the user ID from the chatbot interface, which will be sent to the Prompt engineering module. User’s information like Name, Location, hobbies, interests and favorite food is extracted from the Redshift database along with their upcoming travel booking details like travel city, check In and check out dates. 

## Deploy this solution

Step 1: Ensure the account and the region where the solution is being deployed has access to Bedrock Base models. 

On the AWS Console go to Bedrock Page > Model Access > Manage Model Access > Select Anthropic Claude and Click Save Changes. This might take a few minutes after which we should see Access Granted 

<img src="docs/Bedrock_Access.jpg" alt="Bedrock Access" width="400"/>
 
Step 2: Launch the AWS CloudFormation template

Launch the following AWS CloudFormation template to deploy Amazon Redshift Serverless cluster along with all the related components, including the EC2 instance to host the webapp. Provide a Stack Name and an SSH Keypair and Deploy the Cloudformation template. 


<a href="https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=travelplanner&templateURL=https://redshift-blogs.s3.amazonaws.com/genai-prompt-engineering/genai-redshift-prompt-engineering.yaml"> <img src="docs/LaunchStack.png" alt="Bedrock Access" width="100"/> </a>


Step 3: Copy the Redshift Database Workgroup Name, Secret ARN in a notepad from the Outputs tab of the Cloudformation Stack. 
 
<img src="docs/CF_Output.jpg" alt="CFN Output" width="400"/>

Step 4: Connect to the EC2 instance that was created using SSH Connect from the AWS Console

Step 5: Update the configuration file “data_feed_config.ini” with the Region, Workgroup Name and Secret ARN that was copied in Step2.  

<img src="docs/CONFIG_INI.jpg" alt="Config Update" width="400"/>
 
Step 6: Run the below commands to Create DDL and Launch the Web service. 

python3 ~/personalized_travel_itinerary_planner/core/redshift_ddl.py

streamlit run ~/personalized_travel_itinerary_planner/core/chatbot_app.py --server.port=8080 &

Step 7: Copy the External URL from the Output of the above command and launch the URL in a browser

Step 8: Enter the User ID: 1028169


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

