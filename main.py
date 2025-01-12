import os
import requests
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import re

# Define the scopes your app needs
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def authenticate_google_drive():
    """Authenticate the user and save credentials for reuse."""
    creds = None
    # Check if token.pickle exists (stored credentials)
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If credentials are not available or expired, log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for reuse
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)


def extract_file_id(drive_url):
    """Extract the file ID from a Google Drive URL."""
    match = re.search(r'/d/([a-zA-Z0-9_-]+)|id=([a-zA-Z0-9_-]+)', drive_url)
    if match:
        return match.group(1) or match.group(2)
    else:
        raise ValueError("Invalid Google Drive URL.")


def get_file_name(service, file_id):
    """Fetch and return the file name using the file ID."""
    try:
        file = service.files().get(fileId=file_id, fields="name").execute()
        return file['name']
    except Exception as e:
        return f"Error: {e}"


def download_file_with_progress(file_id, output_file, progress_callback):
    """Download file using requests and update the progress bar."""
    file_url = f"https://drive.google.com/uc?id={file_id}"
    response = requests.get(file_url, stream=True)

    # Get the total file size from the response headers
    total_size = int(response.headers.get('Content-Length', 0))

    # Open the output file to write the downloaded content
    with open(output_file, 'wb') as f:
        downloaded = 0
        for data in response.iter_content(chunk_size=1024):
            downloaded += len(data)
            f.write(data)
            progress_callback(downloaded, total_size)
    QMessageBox.information(windows, "End download", f"Downloaded: {output_file}")


def update_progress(downloaded, total_size):
    """Update the progress bar based on the download progress."""
    # Calculate the percentage of download completed
    progress_percent = (downloaded / total_size) * 100
    # Set the value of the progress bar (cast it to an integer)
    windows.bar1.setValue(int(progress_percent))


def main(drive_url):
    """Main function to authenticate and process the file."""
    # Authenticate and get the Google Drive service
    service = authenticate_google_drive()

    try:
        # Extract file ID and get the file name
        file_id = extract_file_id(drive_url)
        file_name = get_file_name(service, file_id)

        if "Error" in file_name:
            print(file_name)
            return None  # Return None if there is an error
        else:
            print(f"File Name: {file_name}")
            return file_name  # Return the file name

    except ValueError as ve:
        print(ve)
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def Download_click():
    urll = windows.url.text()  # Get URL from the input field
    windows.bar1.setValue(0)  # Reset progress bar before starting a new download
    file_name = main(urll)  # Call main and get the file name

    if file_name:
        windows.gr.setText(f"File Name: {file_name}")  # Update label with file name
        download_file_with_progress(extract_file_id(urll), file_name, update_progress)  # Start download
    else:
        windows.gr.setText("Error: Unable to retrieve file name.")  # Error message if file name is None


def add_click():
    pass


app = QApplication([])
windows = loadUi("GUI.ui")
windows.setWindowIcon(QIcon("drive.ico"))
windows.show()

# Connect the buttons to their respective functions
windows.Download.clicked.connect(Download_click)
windows.add.clicked.connect(add_click)

app.exec_()
