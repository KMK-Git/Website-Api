import logging
import boto3
import json
import base64

logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)


def convert_obj_to_b64_string(python_obj: object) -> str:
    json_string = json.dumps(python_obj)  # Convert to JSON string.
    json_bytes = bytes(json_string, 'utf-8')  # Convert string to bytes.
    b64_bytes = base64.b64encode(json_bytes)  # Encode bytes to base64.
    b64_string = b64_bytes.decode('utf-8')  # Convert bytes to string.
    return b64_string


def convert_b64_string_to_obj(b64_string: str) -> object:
    json_bytes = base64.b64decode(b64_string)  # Decode base64 string to bytes.
    json_string = json_bytes.decode('utf-8')  # Convert bytes to string.
    python_obj = json.loads(json_string)  # Convert json string to python object.
    return python_obj


def get_birthdays(token: str = None) -> dict:
    """
    Gets list of all birthdays from DynamoDB. Uses pagination, results are limited to 20 per single call.

    :param token: Token supplied for pagination. Use None if token not found.
    :return: Dictionary result.
             Key 'birthdays' is a list of birthdays.
             Key 'token' indicates more birthdays are available and can be used for pagination.
    """
    result = {}
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('BirthdaysTable')
    if token is not None:
        decoded_token = convert_b64_string_to_obj(token)
        scan_result = table.scan(Limit=20, ExclusiveStartKey=decoded_token)
    else:
        scan_result = table.scan(Limit=20)
    result['birthdays'] = scan_result['Items']
    if 'LastEvaluatedKey' in scan_result:
        result['token'] = convert_obj_to_b64_string(scan_result['LastEvaluatedKey'])
    return result


def lambda_handler(event, context):
    logger.info(str(event).replace("'", '"'))
    try:
        token = None
        if 'token' in event:
            token = event['token']
        return get_birthdays(token)
    except Exception:
        logger.exception("There was an exception")
        raise Exception("Malformed input")
