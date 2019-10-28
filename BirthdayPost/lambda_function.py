import logging
import boto3
import datetime
import uuid

logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)


def convert_event(event: dict) -> dict:
    """
    Converts event to dictionary of fields which will be saved to dynamodb.

    :param event: Event which triggered Lambda. Contains form fields.
    :return: Dictionary of fields.
    """
    # TODO: Check issues around leap year.
    date_object = datetime.datetime(2020, event['month'], event['day'],
                                    tzinfo=datetime.timezone(datetime.timedelta(hours=event['timezone'])))
    utc_time_tuple = date_object.utctimetuple()
    month, day = utc_time_tuple[1], utc_time_tuple[2]
    hour, minute = utc_time_tuple[3], utc_time_tuple[4]
    fields = {'FirstName': event['firstName'], 'LastName': event['lastName'], 'Email': event['email'],
              'Subtext': event['subtext'], 'UnsubscribeKey': uuid.uuid4().hex,
              'DateKey': '{:02d}-{:02d}'.format(month, day),
              'TimeName': '{:02d}:{:02d}-{} {}'.format(hour, minute, event['firstName'], event['lastName'])}
    return fields


def save_birthday_to_dynamodb(fields: dict) -> None:
    """
    Saves birthday to dynamodb, with proper time and an auto generated unsubscribe key.

    :param fields: Fields to be saved in dynamodb.
    :return: None.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('BirthdaysTable')
    table.put_item(Item=fields)


def lambda_handler(event, context):
    logger.info(str(event).replace("'", '"'))
    try:
        birthday_item = convert_event(event)
        save_birthday_to_dynamodb(birthday_item)
    except Exception:
        logger.exception("There was an exception")
        raise Exception("Malformed input")
    return {
        'message': 'Successful'
    }
