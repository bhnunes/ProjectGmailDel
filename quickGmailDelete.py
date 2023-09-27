from __future__ import print_function
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
import re


# If modifying these scopes, delete the file token.json.
#SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
SCOPES = ['https://mail.google.com/']
CATEGORIES = ['CATEGORY_SOCIAL','TRASH','CATEGORY_FORUMS','CATEGORY_UPDATES','CATEGORY_PROMOTIONS']
BATCH_LIMIT=1000
DATE_FORMAT_PATTERN = r'^\d{4}/(0[1-9]|1[0-2])/(0[1-9]|[1-2][0-9]|3[0-1])$'
INVALID_INPUT_TEXT = '   Invalid input! Understand your error and re-run the script!'
MENU_TEXT = """
1. Run Standard Clean Only
2. Run Standard Clean and Inbox Clean by Date
3. Run Inbox Clean by Date only
4. Exit

WARNING: All messages will be deleted permanently (not moved to Trash).
"""

folder_path = os.path.dirname(os.path.abspath(__file__))

CREDENTIAL_PATH=folder_path+'\\'+"credentials.json"
TOKEN_PATH=folder_path+'\\'+"token.json"



def StartandValidate():
    query=None
    print(MENU_TEXT)
    try:
        choice=int(input('   Choose an option:'))
        if choice==4:
            print('   Process Exited')
            exit()
        elif (choice==2 or choice==3):
            after_date = str(input("   Please provide the After Date, in the format yyyy/mm/dd :"))
            validateDate(after_date)
            before_date = str(input("   Please provide the Before Date, in the format yyyy/mm/dd :"))
            validateDate(before_date)
            query="in:inbox  after:"+str(after_date)+" before:"+str(before_date)
        elif choice==1:
            pass
        else:
            print(INVALID_INPUT_TEXT)
            exit()            
    except Exception as error:
        print(str(error)+" - "+INVALID_INPUT_TEXT)
        exit()
    return choice, query



def validateDate(date_string):
    if re.match(DATE_FORMAT_PATTERN, date_string):
        pass
    else:
        raise Exception("   The Format date provided is not in the expected pattern yyyy/mm/dd")



def credentialMechanics():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIAL_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds


def getMessages(creds,choice,query):
        MessagesToDelete=[]
        service = build('gmail', 'v1', credentials=creds)
        if (choice==1 or choice==2):
            for category in CATEGORIES:
                nextPageToken=None
                stop=False
                while stop==False:
                    results = service.users().messages().list(userId='me',labelIds=category, pageToken=nextPageToken).execute()
                    if 'messages' in results:
                        MessagesToDelete.extend(results['messages'])
                    if 'nextPageToken' in results:
                        nextPageToken=results['nextPageToken']
                    else:
                        stop=True
        if query!=None:
            nextPageToken=None
            stop=False
            while stop==False:
                results = service.users().messages().list(userId='me',pageToken=nextPageToken,q=query).execute()
                if 'messages' in results:
                    MessagesToDelete.extend(results['messages'])

                if 'nextPageToken' in results:
                    nextPageToken=results['nextPageToken']
                else:
                    stop=True
        
        if len(MessagesToDelete)==0:
            raise Exception("   There is nothing to be deleted at this time!")
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
        print('   Deleted Batch '+str(i)+' of '+str(len(chunks)))
        i=i+1




def main():
    choice,query = StartandValidate()
    try:
        creds=credentialMechanics()
        MessagesToDelete, service = getMessages(creds,choice,query)
        chunks=parseMessagesToDelete(MessagesToDelete)
        DeleteMessages(service,chunks)
        print("   Process Finished Succesfully at "+str(datetime.datetime.now()))
    except Exception as error:
        print(f'   An error occurred: {str(error)}')




if __name__ == '__main__': 
     main()






