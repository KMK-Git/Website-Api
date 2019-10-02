import logging
import boto3

logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)


def delete_birthday_from_dynamodb(key: str) -> None:
    """
    Deletes birthday from dynamodb, with given unsubscribe key.

    :param key: Unsubscribe key identifier.
    :return: None.
    """
    dynamodb_client = boto3.client('dynamodb')
    results = dynamodb_client.query(
        IndexName='UnsubscribeKeyIndex',
        ExpressionAttributeValues={
            ':keyValue': {
                'S': key,
            },
        },
        KeyConditionExpression='UnsubscribeKey = :keyValue',
        TableName='BirthdaysTable',
    )
    birthday = results['Items'][0]
    dynamodb_client.delete_item(
        Key={
            'DateKey': {
                'S': birthday['DateKey']['S'],
            },
            'TimeName': {
                'S': birthday['TimeName']['S'],
            },
        },
        TableName='BirthdaysTable',
    )


def lambda_handler(event, context):
    logger.info(str(event).replace("'", '"'))
    try:
        delete_birthday_from_dynamodb(event['key'])
    except Exception:
        logger.exception("There was an exception while deleting the item")
        raise Exception("Malformed input")
    return {
        'message': 'Successful'
    }
