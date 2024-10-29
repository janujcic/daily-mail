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


def main():
    
    # STEP 1: get a list of existing files from the Drive
    list_files_in_folder(FOLDER_ID)

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