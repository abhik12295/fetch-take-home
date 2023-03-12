import hashlib
from datetime import datetime
import boto3
import json
import psycopg2

# connect to database

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

    if "app_version" in flattened_data:
        app_version = flattened_data['app_version']
        flattened_data['app_version'] = int(app_version.split(".")[0])

    # add create_date field in format MM-DD-YYYY
    flattened_data['create_date'] = datetime.now().strftime('%m-%d-%Y')

    # append the transformed date to the list of records
    records.append(flattened_data)

    # sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])
print(records)

if records:
    keys = records[0].keys()
    values = [[record[k] for k in keys] for record in records]
    print('values',values)
    insert_query = f"INSERT INTO user_logins ({','.join(keys)}) VALUES ({','.join(['%s'] * len(keys))}) ON CONFLICT " \
                   f"DO NOTHING"
    cur = conn.cursor()
    cur.executemany(insert_query, values)
    conn.commit()

conn.close()

#
# # Extract the relevant data from the message
# if 'Messages' in response:
#     message = response['Messages'][0]
#     message_id = message['MessageId']
#     receipt_handle = message['ReceiptHandle']
#     body = message['Body']
#
#     # Convert the 'body' field to a JSON object
#     body_json = json.loads(body)
#
#     # Mask the PII data in 'device_id' and 'ip'
#     body_json['device_id'] = 'DEVICE_ID'
#     body_json['ip'] = 'IP_ADDRESS'
#
#     # Update the 'body' field with the masked JSON
#     body = json.dumps(body_json)
#
#     # Store the data in a dictionary
#     data = {
#         # "message_id": message_id,
#         # "receipt_handle": receipt_handle,
#         "body": body
#     }
#
#     print(data)
# else:
#     print("No messages found in the queue.")
