import configparser
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Google client info
SERVICE_ACCOUNT_FILE = config['google_drive']['service_account_file']
SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_ID = config['google_drive']['folder_id']

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

def list_files_in_folder(folder_id):
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

def get_file_content(file_id):
    """Retrieve the content of a specific file from Google Drive."""
    try:
        # Get the file metadata to determine the MIME type
        file_metadata = drive_service.files().get(fileId=file_id, fields='name, mimeType').execute()
        file_name = file_metadata['name']
        mime_type = file_metadata['mimeType']
        
        # Retrieve the file content
        request = drive_service.files().get_media(fileId=file_id)
        file_content = request.execute()
        
        # Decode content if it's text-based
        if mime_type.startswith('text/') or mime_type == 'application/json':
            file_content = file_content.decode('utf-8')
        
        print(f"Successfully retrieved content of file: {file_name}")
        return file_content
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def main():
    
    # STEP 1: get a list of existing files from the Drive
    files = list_files_in_folder(FOLDER_ID)

    file_content = get_file_content(files[0]['id'])
    print(file_content)

    # STEP 2: grab the metadata files (recipients/sending_config & recently_sent_files)

    # STEP 3: grab the data from the metadata files
    recipients = []
    nb_saved_old_files = 30
    ignore_files = []

    # STEP 4: Grab a random file from the existin files on the Drive (ignore if in ignore_files)

    # STEP 5: Process the random file

    # STEP 6: Send the file content via email

    # STEP 7: Update the ignore_files folder and save it to the drive 

if __name__ == '__main__':
    main()