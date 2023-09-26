from __future__ import print_function
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime


# If modifying these scopes, delete the file token.json.
#SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
SCOPES = ['https://mail.google.com/']
CATEGORIES = ['CATEGORY_FORUMS']
BATCH_LIMIT=10
AFTER_DATE='2015/9/26'
BEFORE_DATE='2020/9/27'
QUERY="in:inbox  after:"+str(AFTER_DATE)+" before:"+str(BEFORE_DATE)
SEARCH_BY_DATE=True


INVALID_INPUT_TEXT = 'Invalid input! Try again'
MENU_TEXT = """
1. Run Standard Clean Only
2. Run Standard Clean and Inbox Clean by Date
3. Run Inbox Clean by Date only
4. Exit

WARNING: All messages will be deleted permanently (not moved to Trash).
"""



def credentialMechanics():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def getMessages(creds):
        nextPageToken=None
        MessagesToDelete=[]
        stop=False
        service = build('gmail', 'v1', credentials=creds)
        while stop==False:
            results = service.users().messages().list(userId='me',labelIds=CATEGORIES, pageToken=nextPageToken).execute()
            if 'messages' in results:
                MessagesToDelete.extend(results['messages'])
            if 'nextPageToken' in results:
                nextPageToken=results['nextPageToken']
            else:
                stop=True
        
        if SEARCH_BY_DATE==True:
            nextPageToken=None
            stop=False
            while stop==False:
                results = service.users().messages().list(userId='me',pageToken=nextPageToken,q=QUERY).execute()
                if 'messages' in results:
                    MessagesToDelete.extend(results['messages'])

                if 'nextPageToken' in results:
                    nextPageToken=results['nextPageToken']
                else:
                    stop=True
        
        if len(MessagesToDelete)==0:
            raise Exception("There is nothing to be deleted at this time!")
        else:
            return MessagesToDelete, service



def parseMessagesToDelete(MessagesToDelete):
    chunks = [MessagesToDelete[x:x+BATCH_LIMIT] for x in range(0, len(MessagesToDelete), BATCH_LIMIT)]
    return chunks


def DeleteMessages(service,chunks):
    i=1
    for chunk in chunks:
        msg_ids=[]
        for id in chunk:
            msg_ids.append(id['id'])
        service.users().messages().batchDelete(userId='me', body={"ids": msg_ids}).execute()
        print('Deleted Batch'+str(i)+' of '+str(len(chunks)))
        i=i+1


def main():
    try:
        creds=credentialMechanics()
        MessagesToDelete, service = getMessages(creds)
        chunks=parseMessagesToDelete(MessagesToDelete)
        DeleteMessages(service,chunks)
        print("Process Finished Succesfully at "+str(datetime.now()))
    except Exception as error:
        print(f'An error occurred: {error}')






