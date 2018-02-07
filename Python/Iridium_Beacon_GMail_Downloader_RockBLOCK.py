# Iridium SBD GMail Downloader using the GMail API

# Logs into GMail using the API, checks for Iridium Beacon SBD messages every minute,
# saves the attachment to file, and moves it to the SBD folder.
# You will need to create the SBD folder in GMail if it doesn't already exist.

# Follow these instructions to create your credentials:
# https://developers.google.com/gmail/api/quickstart/python

from __future__ import print_function
import httplib2
import os
import base64
import email
import datetime
import time

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient import errors

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
#SCOPES = 'https://www.googleapis.com/auth/gmail.readonly' # Read only
SCOPES = 'https://www.googleapis.com/auth/gmail.modify' # Everything except delete
#SCOPES = 'https://mail.google.com/' # Full permissions
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,'gmail-python-quickstart.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

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

def SaveMessageBody(service, user_id, msg_id):
    """Save the body from Message with given id.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        msg_id: ID of Message.
    """
    message = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()
    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
    mime_msg = email.message_from_string(msg_str)
    messageMainType = mime_msg.get_content_maintype()
    file_data = ''
    #print(messageMainType)
    if messageMainType == 'multipart':
        for part in mime_msg.get_payload():
            partType = part.get_content_maintype()
            #print('...'+partType)
            if partType == 'multipart':
                for multipart in part.get_payload():
                    multipartType = multipart.get_content_maintype()
                    #print('......'+multipartType)
                    if multipartType == 'text':
                        file_data += multipart.get_payload()
                        break # Only get the first text payload
            elif partType == 'text':
                file_data += part.get_payload()
    elif messageMainType == 'text':
        file_data += mime_msg.get_payload()

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
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

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
            for i in range(60):
                time.sleep(1) # Sleep
    except KeyboardInterrupt:
        print('Ctrl-C received!')
