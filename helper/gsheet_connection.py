import os
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

class GsheetConnection:
    def __init__(self, token_json, scopes, spreadsheet_id, sheet_name):
        # Convert the embedded JSON to a temporary credentials file
        json_path = "token_sheet.json"
        with open(json_path, "w") as json_file:
            json.dump(token_json, json_file)

        self.token_json = json_path
        self.scopes = scopes
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.service = self.authenticate_google_sheets()

    def authenticate_google_sheets(self):
        creds = None
        if os.path.exists(self.token_json):
            creds = Credentials.from_authorized_user_file(self.token_json, self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
        return build("sheets", "v4", credentials=creds)

    def get_data(self):
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}"
            ).execute()
            data = result.get("values", [])
            if data:
                df = pd.DataFrame(data[1:], columns=data[0])

                # Define columns that should be numeric
                numeric_columns = [
                    "Qty", "Harga Perolehan", "Tahun Beli", "Umur Ekonomis",
                    "Nilai Penyusutan per Bulan", "VALUASI ASSET 2019",
                    "VALUASI ASSET 2020", "VALUASI ASSET 2021",
                    "VALUASI ASSET 2022", "VALUASI ASSET 2023",
                    "VALUASI ASSET 2024", "VALUASI ASSET 2025",
                    "Nilai Buku 2024"
                ]

                # Clean and convert numeric columns
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = (
                            df[col]
                            .astype(str)  # Ensure all values are strings before cleaning
                            .str.replace(r"[^\d.-]", "", regex=True)  # Remove non-numeric characters
                            .replace("-", "0")  # Convert dashes to zero
                            .replace("", "0")  # Replace empty strings with 0
                            .astype(float)  # Convert to float
                        )
                return df
            return pd.DataFrame()
        except HttpError as err:
            return pd.DataFrame()

    def append_data(self, new_row):
        try:
            body = {"values": [new_row]}
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()
        except HttpError as err:
            print(f"Error: {err}")

    def update_data(self, index, updated_row):
        try:
            range_to_update = f"{self.sheet_name}!A{index+2}:X{index+2}"
            body = {"values": [updated_row]}
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_to_update,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
        except HttpError as err:
            print(f"Error: {err}")

    def delete_data(self, index):
        try:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={
                    "requests": [{
                        "deleteDimension": {
                            "range": {
                                "sheetId": 0,
                                "dimension": "ROWS",
                                "startIndex": index+1,
                                "endIndex": index+2
                            }
                        }
                    }]
                }
            ).execute()
        except HttpError as err:
            print(f"Error: {err}")
