import boto3
import xml.etree.ElementTree as ET
import os

from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
AWS_S3_USE_SSL = int(os.getenv('AWS_S3_USE_SSL', default=0))
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')


bucket_name = 'upload-media'

s3_client = boto3.client(
    's3',
    region_name=AWS_S3_REGION_NAME,
    use_ssl=AWS_S3_USE_SSL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=AWS_S3_ENDPOINT_URL
)


def create_cors_xml(cors_rules):
    root = ET.Element('CORSConfiguration')
    for rule in cors_rules['CORSRules']:
        cors_rule = ET.SubElement(root, 'CORSRule')
        for key, values in rule.items():
            if isinstance(values, list):
                for value in values:
                    sub_element = ET.SubElement(cors_rule, key)
                    sub_element.text = str(value)
            else:
                sub_element = ET.SubElement(cors_rule, key)
                sub_element.text = str(value)
    return ET.tostring(root, encoding='unicode')


try:
    cors_configuration = s3_client.get_bucket_cors(Bucket=bucket_name)
    print(cors_configuration)
    cors_xml = create_cors_xml(cors_configuration)
    print(cors_xml)
except Exception as e:
    print(f"Произошла ошибка: {e}")
