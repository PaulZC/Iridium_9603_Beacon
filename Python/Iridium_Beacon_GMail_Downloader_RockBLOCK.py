# Iridium SBD GMail Downloader using the GMail API

# Written by: Paul Clark (PaulZC)

# Updated: 8th March 2020
# Now uses the updated oauthlib authentication

# Licence: MIT

# This code logs into your GMail account using the API and checks for new Tracker SBD
# messages every 15 seconds. If a new message is found, the code saves the attachment
# to file, and then moves the message to the SBD folder (to free up your inbox).

# You will need to create an SBD folder in GMail if it doesn't already exist.

# The code assumes your messages are being delivered by the Rock7 RockBLOCK gateway
# and that the message subject contains the words "Message" "from RockBLOCK".

# Follow these instructions to create your credentials for the API:
# https://developers.google.com/gmail/api/quickstart/python

# If modifying these scopes, delete the file token.pickle.
#SCOPES = ['https://www.googleapis.com/auth/gmail.readonly'] # Read only
SCOPES = ['https://www.googleapis.com/auth/gmail.modify'] # Everything except delete
#SCOPES = ['https://mail.google.com/'] # Full permissions

import base64
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from time import sleep

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the oauthlib flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time. You will need to delete it if you change the SCOPES.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def ListMessagesMatchingQuery(service, user_id, query=''):
    """List all Messages of the user's mailbox matching the query.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        query: String used to filter messages returned.
        Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

    Returns:
        List of Messages that match the criteria of the query. Note that the
        returned list contains Message IDs, you must use get with the
        appropriate ID to get the details of a Message.
    """
    response = service.users().messages().list(userId=user_id,q=query).execute()
    messages = []
    if 'messages' in response:
        messages.extend(response['messages'])

    while 'nextPageToken' in response:
        page_token = response['nextPageToken']
        response = service.users().messages().list(userId=user_id, q=query,pageToken=page_token).execute()
        messages.extend(response['messages'])

    return messages

def SaveAttachments(service, user_id, msg_id):
    """Get and store attachment from Message with given id.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        msg_id: ID of Message containing attachment.
    """
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()

    #local_date = datetime.datetime.fromtimestamp(float(message['internalDate'])/1000.)
    #date_str = local_date.strftime("%y-%m-%d_%H-%M-%S_")

    for part in message['payload']['parts']:
        if part['filename']:
            if 'data' in part['body']:
                data=part['body']['data']
            else:
                att_id=part['body']['attachmentId']
                att=service.users().messages().attachments().get(userId=user_id, messageId=msg_id,id=att_id).execute()
                data=att['data']
            file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
            #path = date_str+part['filename']
            path = part['filename']

            with open(path, 'wb') as f:
                f.write(file_data)
                f.close()

def GetMessageBody(contents):
    """Save the message body.

    Assumes plaintext message body.

    Gratefully plagiarised from:
    https://github.com/rtklibexplorer/GMail_RTKLIB/blob/master/email_utils.py
    """
    for part in contents['payload']['parts']:
        if part['mimeType'] == 'text/plain':
            body = part['body']['data']
            return base64.urlsafe_b64decode(body.encode('UTF-8')).decode('UTF-8')
        elif 'parts' in part:
            # go two levels if necessary
            for sub_part in part['parts']:
                if sub_part['mimeType'] == 'text/plain':
                    body = sub_part['body']['data']
                    return base64.urlsafe_b64decode(body.encode('UTF-8')).decode('UTF-8')

def SaveMessageBody(service, user_id, msg_id):
    """Save the body from Message with given id.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        msg_id: ID of Message.
    """
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    file_data = GetMessageBody(message)

    #local_date = datetime.datetime.fromtimestamp(float(message['internalDate'])/1000.)
    #date_str = local_date.strftime("%y-%m-%d_%H-%M-%S_")
    
    subject = GetSubject(service, user_id, msg_id);
    for c in r' []/\;,><&*:%=+@!#^()|?^': # substitute any invalid characters
        subject = subject.replace(c,'_')
 
    #path = date_str+subject+".txt"
    path = subject+".txt"

    with open(path, 'w') as f:
        f.write(file_data)
        f.close()

def GetSubject(service, user_id, msg_id):
    """Returns the subject of the message with given id.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        msg_id: ID of Message.
    """
    subject = ''
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    payload = message["payload"]
    headers = payload["headers"]
    for header in headers:
        if header["name"] == "Subject":
            subject = header["value"]
            break
    return subject

def MarkAsRead(service, user_id, msg_id):
    """Marks the message with given id as read.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        msg_id: ID of Message.
    """
    service.users().messages().modify(userId=user_id, id=msg_id, body={ 'removeLabelIds': ['UNREAD']}).execute()

def MoveToLabel(service, user_id, msg_id, dest):
    """Changes the labels of the message with given id to 'move' it.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        msg_id: ID of Message.
        dest: destination label
    """
    # Find Label_ID of destination label
    results = service.users().labels().list(userId=user_id).execute()
    labels = results.get('labels', [])
    for label in labels:
        if label['name'] == dest: dest_id = label['id']

    service.users().messages().modify(userId=user_id, id=msg_id, body={ 'addLabelIds': [dest_id]}).execute()
    service.users().messages().modify(userId=user_id, id=msg_id, body={ 'removeLabelIds': ['INBOX']}).execute()

def main():
    """Creates a Gmail API service object.
    Searches for unread messages, with attachments, with "Message" "from RockBLOCK" in the subject.
    Saves the attachment to disk.
    Marks the message as read.
    Moves it to the SBD folder.
    You will need to create the SBD folder in GMail if it doesn't already exist.
    """
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)

    # Include your RockBLOCK IMEI in the subject search if required
    messages = ListMessagesMatchingQuery(service, 'me', 'subject:(Message \"from RockBLOCK\") is:unread has:attachment')
    if messages:
        for message in messages:
            print('Processing: '+GetSubject(service, 'me', message["id"]))
            #SaveMessageBody(service, 'me', message["id"])
            SaveAttachments(service, 'me', message["id"])
            MarkAsRead(service, 'me', message["id"])
            MoveToLabel(service, 'me', message["id"], 'SBD')
    #else:
        #print('No messages found!')

if __name__ == '__main__':
    print('Iridium Beacon GMail API Downloader for RockBLOCK')
    print('Press Ctrl-C to quit')
    try:
        while True:
            #print('Checking for messages...')
            main()
            for i in range(15):
                sleep(1) # Sleep
    except KeyboardInterrupt:
        print('Ctrl-C received!')
