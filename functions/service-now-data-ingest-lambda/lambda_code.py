import boto3
import requests
import json
import os
from urllib.parse import urlencode
from datetime import datetime


# Load config from file
with open("config.json") as f:
    CONFIG = json.load(f)

s3 = boto3.client("s3")

# 🔐 Get ServiceNow credentials + instance from Secrets Manager
def get_servicenow_creds(secret_name):
    client = boto3.client("secretsmanager")
    secret = client.get_secret_value(SecretId=secret_name)
    return json.loads(secret["SecretString"])

def upload_json_to_s3(data, config, table_name):
    timestamp = datetime.utcnow()
    key = f"{config['s3_prefix']}/{table_name}/{timestamp.year}/{timestamp.month}/{timestamp.day}/{timestamp.hour}/records.json"

    json_bytes = json.dumps(data, indent=2).encode('utf-8')

    s3.put_object(
        Bucket=config["s3_bucket"],
        Key=key,
        Body=json_bytes,
        ContentType="application/json"
    )
    print(f"✅ Uploaded JSON to s3://{config['s3_bucket']}/{key}")

# 🔧 Build query string
def build_query(config, offset):
    return urlencode({
        # "sysparm_query": config["query"],
        # "sysparm_fields": config["fields"],
        "sysparm_limit": config["limit"],
        "sysparm_offset": offset
    })

# 🔁 Fetch records from ServiceNow with pagination
def fetch_records(creds, config, table):
    all_records = []
    offset = 0

    while True:
        query = build_query(config, offset)
        url = f"https://{creds['instance']}.service-now.com/api/now/table/{table}?{query}"
        response = requests.get(url, auth=(creds["username"], creds["password"]), headers={"Accept": "application/json"})

        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            break

        batch = response.json().get("result", [])
        if not batch:
            break

        all_records.extend(batch)
        offset += config["limit"]

    return all_records

# 📎 Download and upload attachments to S3
def process_attachments(creds, table, record):
    record_sys_id = record["sys_id"]
    number = record.get("number", record_sys_id)
    instance = creds["instance"]

    # 1. Get list of attachments
    att_url = f"https://{instance}.service-now.com/api/now/table/sys_attachment?sysparm_query=table_sys_id={record_sys_id}"
    att_response = requests.get(att_url, auth=(creds["username"], creds["password"]), headers={"Accept": "application/json"})

    attachments = att_response.json().get("result", [])
    for att in attachments:
        file_url = f"https://{instance}.service-now.com/api/now/attachment/{att['sys_id']}/file"
        file_resp = requests.get(file_url, auth=(creds["username"], creds["password"]), stream=True)

        if file_resp.status_code == 200:
            timestamp = datetime.utcnow()
            file_path = f"{CONFIG['s3_prefix']}/{table}/{timestamp.year}/{timestamp.month}/{timestamp.day}/{timestamp.hour}/attachments/{number}/{att['file_name']}"
            print(f"Uploading {file_path} to S3...")

            s3.upload_fileobj(
                Fileobj=file_resp.raw,
                Bucket=CONFIG["s3_bucket"],
                Key=file_path
            )
        else:
            print(f"⚠️ Failed to download: {att['file_name']}")

# 🚀 Lambda entry
def lambda_handler(event, context):
    secret_name = os.environ["SERVICENOW_SECRET_NAME"]
    creds = get_servicenow_creds(secret_name)
    tables = CONFIG["tables"]
    for table in tables:
        records = fetch_records(creds, CONFIG, table)

        for record in records:
            print(f"📄 Fetched record: {record.get('number')}")
            process_attachments(creds, table, record)
        upload_json_to_s3(records, CONFIG, table)
    return {
        "statusCode": 200,
        "body": f"✅ Successfully fetched data from service-now"
    }