import configparser
import json
import smtplib
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def list_files_gdrive_folder(drive_service, folder_id):
    """List all files in a specified Google Drive folder."""
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents",
        spaces='drive',
        fields="files(id, name)"
    ).execute()
    files = results.get('files', [])
    for file in files:
        print(f"File ID: {file['id']} - Name: {file['name']}")
    return files

def get_file_gdrive(drive_service, file_id):
    """Retrieve the content of a specific file from Google Drive."""
    file = {}
    try:
        # Get the file metadata to determine the MIME type
        file_metadata = drive_service.files().get(fileId=file_id, fields='name, mimeType').execute()
        file_name = file_metadata['name'].split('.')[0]
        mime_type = file_metadata['mimeType']
        
        # Retrieve the file content
        request = drive_service.files().get_media(fileId=file_id)
        file_content = request.execute()
        
        # Decode content if it's text-based
        if mime_type.startswith('text/') or mime_type == 'application/json':
            file_content = file_content.decode('utf-8')
        
        print(f"Successfully retrieved content of file: {file_name}")
        file = {'file_name':file_name, 'mime_type':mime_type, 'file_content':file_content}
        return file
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def send_email_smtp(gmail_username, gmail_password, recipient_emails, subject, message_text):
    """Send an email using Gmail's SMTP server."""
    try:
        # Create the email
        message = MIMEMultipart()
        message['From'] = gmail_username
        message['To'] = ', '.join(recipient_emails)
        message['Subject'] = subject

        # Attach the message text
        message.attach(MIMEText(message_text, 'plain'))

        # Connect to Gmail's SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_username, gmail_password)
            server.sendmail(gmail_username, recipient_emails, message.as_string())
            print(f"Email sent to {', '.join(recipient_emails)}")
    
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    # Load configuration from config.ini
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Google info
    SERVICE_ACCOUNT_FILE = config['google_drive']['service_account_file']
    GMAIL_USERNAME = config['gmail']['gmail_username']
    GMAIL_PASSWORD = config['gmail']['gmail_password']
    SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/gmail.send']
    FOLDER_ID = config['google_drive']['folder_id']

    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)

    with open('sending_config.json') as f:
        sending_config = json.load(f)

    recipients = sending_config['recipients']

    # STEP 1: get a list of existing files from the Drive
    files = list_files_gdrive_folder(drive_service, FOLDER_ID)

    file = get_file_gdrive(drive_service, files[0]['id'])
    print(file)

    # STEP 2: grab the metadata files (recipients/sending_config & recently_sent_files)

    # STEP 3: grab the data from the metadata files
    nb_saved_old_files = 30
    ignore_files = []

    # STEP 4: Grab a random file from the existin files on the Drive (ignore if in ignore_files)

    # STEP 5: Process the random file

    # STEP 6: Send the file content via email
    if file:
        subject = f"{file['file_name']}"
        send_email_smtp(GMAIL_USERNAME, GMAIL_PASSWORD, recipients, subject, file['file_content'])

    # STEP 7: Update the ignore_files folder and save it to the drive 

if __name__ == '__main__':
    main()