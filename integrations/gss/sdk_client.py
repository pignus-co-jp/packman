import os
import gspread
from google.oauth2.service_account import Credentials


def create_sdk_client(credentials_json_path: str = os.path.join("datalake", "credentials.json")):
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    # 2. ダウンロードしたJSONファイルを使って認証
    credentials = Credentials.from_service_account_file(credentials_json_path,scopes=scopes)
    return gspread.authorize(credentials)
