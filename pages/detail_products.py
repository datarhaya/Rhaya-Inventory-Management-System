import streamlit as st
import streamlit.components.v1 as components

import pandas as pd
import plotly.express as px 

import requests
from io import BytesIO
from PIL import Image

import os
import re
import json
import requests
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]

json_data = {"token": "ya29.a0AXeO80Qc7xkJ4csPlRY40nlv4QhP1L5Foaea7G7PSOBrLJajhChWuR5r6Jqm70LMfUHHazqELTP14BHjOBs3F0Lu3SoE_ORSJa-LI5I0SzwiW5DhuveWaHa2Iud-RxUjc8P6jlRo8ddH7kahI7ItR9y2tx0qLqxEZzZ0JzaHaCgYKAc4SARMSFQHGX2MiEXQOi6mJADhIYL3iyNMJcw0175", "refresh_token": "1//0gBIL6bBS-pjECgYIARAAGBASNwF-L9IrG2CRU7_VMSOZQCuS06l6haxaOMiZ0q6fFoqOnFQR8LQ8zEKOfnW1qsOUtt0B8w46Hk0", "token_uri": "https://oauth2.googleapis.com/token", "client_id": "524126803000-ihcg0d6m1q72a17b7sa04hcq7kljdq31.apps.googleusercontent.com", "client_secret": "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", "scopes": ["https://www.googleapis.com/auth/drive"], "universe_domain": "googleapis.com", "account": "", "expiry": "2025-01-25T19:50:11.401224Z"}

IMAGE_FOLDER = "downloaded_images"

def get_drive_service():
    creds = None
    token_path = "token.json"
    json_path = "token.json"
    with open(json_path, "w") as json_file:
        json.dump(json_data, json_file)

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("cred.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)

def extract_folder_id(drive_url):
    match = re.search(r"drive\.google\.com/drive/folders/([a-zA-Z0-9_-]+)", drive_url)
    return match.group(1) if match else None

def list_images_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    return results.get("files", [])

def download_images(service, images, save_dir=IMAGE_FOLDER):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    downloaded_files = []
    for image in images:
        image_id = image["id"]
        image_name = image["name"]
        image_path = os.path.join(save_dir, image_name)

        request = service.files().get_media(fileId=image_id)
        with open(image_path, "wb") as f:
            f.write(request.execute())

        downloaded_files.append(image_path)

    return downloaded_files

# Streamlit App
st.title("Google Drive Image Downloader")

if st.button("back"):
    st.switch_page("pages/dashboard.py")

st.write(st.session_state.selected_item["Nomor Asset"])

drive_url = st.session_state.selected_item["Dokumentasi_url"]
st.write(drive_url)

if st.button("Fetch & Download Images"):
    if drive_url:
        service = get_drive_service()
        folder_id = extract_folder_id(drive_url)

        if folder_id:
            images = list_images_in_folder(service, folder_id)
            if images:
                st.success(f"Found {len(images)} images. Downloading...")
                downloaded_images = download_images(service, images)

                # Save paths in session state
                st.session_state.pathsImages = downloaded_images
                st.session_state.counter = 0
                st.success("Download complete! Click 'Show next pic' to view images.")
            else:
                st.warning("No images found in the folder.")
        else:
            st.error("Invalid Google Drive URL.")
    else:
        st.warning("Please enter a valid Google Drive folder URL.")

# Display Images
col1, col2 = st.columns(2)

if "pathsImages" in st.session_state and st.session_state.pathsImages:
    col1.subheader("List of images in folder")
    col1.write(st.session_state.pathsImages)

    def showPhoto():
        if "counter" in st.session_state and st.session_state.pathsImages:
            photo = st.session_state.pathsImages[st.session_state.counter]
            col2.image(photo, caption=os.path.basename(photo))
            col1.write(f"Index: {st.session_state.counter}")

            # Increment counter
            st.session_state.counter += 1
            if st.session_state.counter >= len(st.session_state.pathsImages):
                st.session_state.counter = 0

    show_btn = col1.button("Show next pic ⏭️", on_click=showPhoto)



