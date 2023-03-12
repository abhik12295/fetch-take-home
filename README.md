Fetch Take Home Assessment:


This application reads user_logins data from an AWS SQS queue, masks certain fields for privacy, and writes the transformed data to a Postgres database.

Prerequisites

    Docker
    AWS CLI (if not using localstack)
    Postgres client (if not using Docker container for Postgres)

Getting Started

    Clone the repository
    Run docker-compose up to start the application and dependencies
    If not using localstack, configure AWS credentials for the AWS CLI
    Run the application to process the data and write to the Postgres database

Reading Messages from the AWS SQS Queue

To read messages from the AWS SQS queue, you can use the AWS CLI or a third-party library for your programming language.

Here's an example AWS CLI command to receive a single message from the queue:

    awslocal sqs receive-message --queue-url http://localhost:4566/000000000000/login-queue

Reading Data and Data structure: 

For reading JSON data from the SQS queue and transforming it before writing it to the Postgres database, you could use a combination of built-in and custom data structures. Here are some possible options:

    JSON: Since the data is in JSON format, you could use a JSON library or built-in support in your programming language to parse the JSON data into a dictionary or object that can be manipulated and transformed as needed.

    Built-in data structures: For certain transformations, built-in data structures such as dictionaries or lists may be sufficient. For example, if you need to remove or replace specific fields in the JSON data, you could use a dictionary to map the original field names to the new field names or values.
    
    
 Flattening and Masking the data by taking care of duplicates:
 
       To store masked values and identify potential duplicates, one can use a cryptographic hash function such as SHA-256 to 
       convert the raw values into a fixed-length secure hash value. This hash value can be stored in a secure hash table alongside the raw value, 
       enabling easy identification of potential duplicates and facilitating analysis.

        It's important to note that while hashing is a one-way function, it is not unique and can result in false positives. 
        Therefore, it's essential to consider collision parameters to avoid potential inaccuracies in the results

 
 
      # flatten the data

    def flatten_dict(d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    items.extend(flatten_dict(item, f"{new_key}{sep}{i}", sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


    flattened_data = flatten_dict(data)

    # mask the device_id and ip fields
    if "device_id" in flattened_data:
        device_id = flattened_data["device_id"]
        masked_device_id = hashlib.sha256(device_id.encode()).hexdigest()
        flattened_data["masked_device_id"] = masked_device_id
        del flattened_data["device_id"]

    if "ip" in flattened_data:
        ip = flattened_data["ip"]
        masked_ip = hashlib.sha256(ip.encode()).hexdigest()
        flattened_data["masked_ip"] = masked_ip
        del flattened_data["ip"]
        
        
        
● What will be your strategy for connecting and writing to Postgres?

     To connect to a Postgres database and write data using Python, we can use a variety of libraries that provide a high-level interface to the database, such as Psycopg2:

    Install the Psycopg2 library using pip: pip install psycopg2-binary

      Import the library in your Python code:

      import psycopg2
      
      conn = psycopg2.connect(host='localhost', database='postgres', user='postgres', password='postgres')

    TABLE_SCHEMA = """
    CREATE TABLE IF NOT EXISTS user_logins(
    user_id varchar(128),
    device_type varchar(32),
    masked_ip varchar(256),
    masked_device_id varchar(256),
    locale varchar(32),
    app_version integer,
    create_date date
    )
    """
    cur = conn.cursor()
    cur.execute(TABLE_SCHEMA)
    conn.commit()

    # Create a client for SQS
    sqs = boto3.client("sqs", region_name='us-east-1', endpoint_url="http://localhost:4566")

    # Set the queue URL
    queue_url = "http://localhost:4566/000000000000/login-queue"

    # Receive a message from the queue
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=5
    )

    records = []
    print(response)
    for message in response["Messages"]:
        print(message)
        data = json.loads(message["Body"])
        
        
 Where and how will your application run?
 
             For now I have run this on local system:

             by configuring docker, AWSCLI and psql:
             1: first logging in to docker:
                  sudo docker pull fetchdocker/data-takehome-postgres
                  #sudo docker run --name stuart_abhi -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d fetchdocker/data-takehome-postgres
                  sudo docker start stuart_abhi
                  sudo docker exec -it stuart_abhi bash
                  psql -U postgres
                  select * from user_logins
             2: secondly connect with awscli to get data from api:
                  docker pull fetchdocker/data-takehome-localstack
                  sudo docker start s_abhi
                  awslocal sqs receive-message --queue-url http://localhost:4566/000000000000/login-queue
             3: Run the fetch.py file on local system directly and then look for the update postgres on docker stuart_abhi using step 1: from above
      
 Once AWS and postgres started working: 
            we can run the fetch.py file remotely on the local machine.
            It will generate the masked value and store it in postgres.
 
 Apart from that there was issue while putting the data in app_version column as it was INT type:
          #stored the highest value of app_version: say 3.0.1 -> stored 3 in column
          # to store the whole value of app_version we can store it by converting data type to varchar or other
         if "app_version" in flattened_data:
            app_version = flattened_data['app_version']
            flattened_data['app_version'] = int(app_version.split(".")[0])

      `Tried to put app on docker`
        I tried to put my application on docker using Dockerfile and with having some configuration to run it, but there was limitation of time, 
        it was not done completely.
        FROM python:3.8

        WORKDIR /app

        COPY requirements.txt requirements.txt
        RUN pip install psycopg2-binary
        RUN pip install -r requirements.txt

        COPY . .

        CMD ["python", "fetch.py"]
        
        
        
        
● How would you deploy this application in production?
      Deploying an application like this in production would involve a number of steps and considerations, including:

        Configuring and deploying infrastructure: You would need to set up and configure the infrastructure required to run the application, 
        including servers, load balancers, and databases. You might use a cloud provider like AWS, or a container orchestration platform like Kubernetes.

        Creating and configuring resources: Once you have the infrastructure in place, you would need to create and configure resources like the SQS queue, 
        Postgres database, and any other resources required by the application.

        Packaging and deploying the application: You would need to package the application code and dependencies into a deployable artifact, 
        such as a Docker container or a deployment package for a cloud provider. You would then deploy the application to your production environment 
        using an appropriate deployment strategy, such as rolling updates or blue-green deployments.

        Configuring monitoring and alerts: You would need to configure monitoring and alerting for the application and infrastructure to ensure that you can 
        quickly identify and respond to any issues that arise. This might include monitoring for application errors, performance metrics, and infrastructure 
        health.

        Implementing security measures: You would need to implement appropriate security measures to protect the application and infrastructure from threats, 
        such as network security measures, encryption of sensitive data, and access control for resources.

        Testing and validation: Before deploying the application to production, you would need to thoroughly test and validate it to ensure that it is 
        functioning correctly and performing well. This might include functional testing, load testing, and performance testing.

        Continuous improvement: Once the application is deployed, you would need to continuously monitor and improve it over time, 
        including making updates to the code, infrastructure, and configuration to address issues and optimize performance.

    Overall, deploying an application like this in production requires careful planning, attention to detail, and 
    ongoing maintenance and improvement to ensure that it is secure, reliable, and performant.

● What other components would you want to add to make this production ready?
    
      To make this application production-ready, there are several additional components that could be added, depending on the specific requirements and use case. 
      Some possible components include:

    API gateway: Adding an API gateway would allow for more secure and controlled access to the application, as well as enabling features like rate limiting and 
    request throttling.

    Authentication and authorization: Adding authentication and authorization would enable secure access control to the application, ensuring that only authorized 
    users and systems can interact with it.

    Error logging and monitoring: Adding error logging and monitoring would allow for better visibility into errors and issues that occur within the application, 
    making it easier to identify and fix problems quickly.

    Performance monitoring and optimization: Adding performance monitoring and optimization would enable better visibility into the performance of the application 
    and help to identify and address any bottlenecks or other performance issues.

    Backup and recovery: Adding backup and recovery capabilities would enable the application to recover from data loss or system failures, ensuring that critical 
    data is not lost and the application can quickly recover from any disruptions.

● How can this application scale with a growing dataset.
      As the dataset grows, the application will need to be able to handle increasing amounts of data and processing load. There are several strategies that can be used to scale the application:

    Vertical scaling: One approach is to scale the application vertically, by adding more resources to the existing servers, such as increasing CPU or memory 
    capacity. This can be a quick and simple way to increase capacity, but may have limits based on the capabilities of the underlying hardware.

    Horizontal scaling: Another approach is to scale the application horizontally, by adding more servers to handle the increased load. 
    This can be done through load balancing, which distributes incoming traffic across multiple servers. This approach can be more scalable than vertical scaling, 
    but requires more complex infrastructure and configuration.

    Database scaling: As the dataset grows, the database may become a bottleneck, in which case database scaling may be necessary. 
    This can be done through techniques like sharding, which involves splitting the database into multiple shards or partitions to handle increased load.

    Caching: To improve performance and reduce load on the database, caching can be used to store frequently accessed data in memory. 
    This can be done using technologies like Redis or Memcached.

     
● How can PII be recovered later on?
    If PII data has been masked in the database, it can be recovered later on using various techniques depending on how the masking was implemented.

    One approach to recover masked data is to use a reversible masking technique. For example, instead of completely obfuscating the PII data, 
    it could be encrypted or hashed with a key or algorithm that can be reversed later on. This allows the original data to be recovered later on if necessary.

    Another approach is to maintain a separate mapping table that links the original PII data with the masked or obfuscated values. 
    This table would contain the original data alongside the masked data, allowing the original values to be looked up and recovered if needed.


● What are the assumptions you made?
      
      here are some assumptions that I made:

    The JSON data containing user login behavior is in a consistent format, with no missing or unexpected fields. (although i faced issue with version_id column)

    The masking requirements specified in the prompt (i.e. masking device_id and ip while preserving their uniqueness) are sufficient for the organization's privacy and security needs.

    The Postgres database is running on a stable and secure infrastructure, with appropriate access controls and backups in place.

    The application is running in a secure and isolated environment, with appropriate access controls and monitoring in place to prevent unauthorized access or modifications to the system.

    The workload and data volume being processed by the application is within the limits of the system's resources and infrastructure.

    The application is being run by a user or process with appropriate permissions to access the SQS queue and Postgres database.

    The data being processed by the application is not subject to any legal or regulatory restrictions that would prohibit its processing or storage in this manner.
   
Here is the database with masked_ip and masked_device_id through docker terminal bash:

![1](https://user-images.githubusercontent.com/17993648/224561563-14cc9fd9-d03c-4292-9b1d-e093b5056c0c.png)

