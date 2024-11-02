import configparser
import json
import random
import smtplib
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
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
    
    print(f"Number of files in the Google Drive folder: {len(files)}")
    return files

def get_file_gdrive(drive_service, file_id):
    """Retrieve the content of a specific file from Google Drive."""
    file = {}
    try:
        # Get the file metadata to determine the MIME type
        file_metadata = drive_service.files().get(fileId=file_id, fields='name, mimeType').execute()
        file_name = file_metadata['name']
        file_title = file_metadata['name'].split('.')[0]
        file_extension = file_metadata['name'].split('.')[1]
        mime_type = file_metadata['mimeType']
        
        
        # Retrieve the file content
        request = drive_service.files().get_media(fileId=file_id)
        file_content = request.execute()
        
        # Decode content if it's text-based
        if mime_type.startswith('text/') or mime_type == 'application/json':
            file_content = file_content.decode('utf-8')
        
        print(f"Successfully retrieved content of file: {file_name}")
        file = {'file_name':file_name, 'file_title': file_title, 'mime_type':mime_type, 'file_content':file_content, 'file_extension': file_extension, 'id':file_id}
        return file
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def find_file_from_list(files, file_name):
    """Find a file in the list of Google Drive files based on the name. """

    for file in files:
        if file['name'] == file_name:
            return file
        
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

def update_recently_sent_file_json(sending_config, sent_file):
    """ Updates the recently sent files part of the sending_config.json file"""

    sending_config_content = json.loads(sending_config['file_content'])
    recently_sent_files = sending_config_content['recently_sent_files']
    file_number_limit = sending_config_content['file_number_limit']

    if (len(recently_sent_files) > file_number_limit):
        recently_sent_files.pop()
    
    if sent_file not in recently_sent_files:
        recently_sent_files.append(sent_file)

    sending_config_content['recently_sent_files'] = recently_sent_files

    sending_config['file_content'] = sending_config_content

    return sending_config

def update_file_from_memory_to_gdrive(drive_service, folder_id, file):
    """ Uploads a file to Google Drive from in-memory data. """
    file_name = file['file_name']

    file_metadata = {'name': file_name}

    file_content = file['file_content']

    if isinstance(file_content, str):
        file_content = file_content.encode('utf-8')
    elif isinstance(file_content, dict):
        file_content = json.dumps(file_content).encode('utf-8')

    media = MediaInMemoryUpload(file_content, mimetype=file['mime_type'], resumable=True)
    print(file)
    try:
        if file['id']:
             uploaded_file = drive_service.files().update(
                fileId=file['id'],
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, parents'
            ).execute()
             print(f"Updated file '{file_name}' with ID: {uploaded_file['id']}")
        else:
            # Specify the folder to upload to, if provided
            if folder_id:
                file_metadata['parents'] = [folder_id]
            # Upload the file
            uploaded_file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, parents'
            ).execute()
        
            print(f"Uploaded file '{file_name}' with ID: {uploaded_file['id']}")
    
    except Exception as e:
        print(f"An error occurred while uploading the file: {e}")

def grab_random_file_from_gdrive(drive_service, file_list, ignore_files):
    """ Selects a random file from file_list excluding those in ignore_files and retrieves its content. """

    # Filter out ignored files from the list
    filtered_files = [file for file in file_list if file['name'] not in ignore_files]

    if not filtered_files:
        print("No files available after ignoring specified files.")
        return None

    # Select a random file from the filtered list
    selected_file = random.choice(filtered_files)

    return get_file_gdrive(drive_service, selected_file['id'])
    

def main():
    # Load configuration from config.ini
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Google info
    SERVICE_ACCOUNT_FILE = config['google_drive']['service_account_file']
    FOLDER_ID = config['google_drive']['folder_id']

    # not a secure way to send email (used just for local testing)
    GMAIL_USERNAME = config['gmail']['gmail_username']
    GMAIL_PASSWORD = config['gmail']['gmail_password']

    SENDING_CONFIG_NAME = config["drive_files"]["sending_config"]

    SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/gmail.send']
    
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)

    SENDING_CONFIG_NAME = config["drive_files"]["sending_config"]

    # STEP 1: get a list of existing files from the Drive
    gdrive_files = list_files_gdrive_folder(drive_service, FOLDER_ID)

    # STEP 2: grab the metadata files (recipients/sending_config & recently_sent_files)
    sending_config_file = get_file_gdrive(drive_service, find_file_from_list(gdrive_files, SENDING_CONFIG_NAME)['id'])
    
    # STEP 3: grab the data from the metadata files
    sending_config = json.loads(sending_config_file["file_content"])
    recipients = sending_config['recipients']
    ignore_files = sending_config['ignore_files']
    recently_sent_files = sending_config['recently_sent_files']

    # STEP 4: Grab a random file from the existin files on the Drive (ignore if in ignore_files)
    #file = get_file_gdrive(drive_service, gdrive_files[3]['id'])
    random_file = grab_random_file_from_gdrive(drive_service, gdrive_files, ignore_files+recently_sent_files)

    # STEP 5: Process the random file

    # STEP 6: Send the file content via email
    if random_file and len(recipients)>0:
        subject = f"{random_file['file_title']}"
        send_email_smtp(GMAIL_USERNAME, GMAIL_PASSWORD, recipients, subject, random_file['file_content'])

    # STEP 7: Update the ignore_files folder and save it to the drive 
    new_sending_config_file = update_recently_sent_file_json(sending_config_file, random_file['file_name'])

    update_file_from_memory_to_gdrive(drive_service, FOLDER_ID, new_sending_config_file)


if __name__ == '__main__':
    main()