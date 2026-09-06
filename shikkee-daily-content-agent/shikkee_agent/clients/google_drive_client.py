"""
Read-only wrapper over the Google Drive API for browsing the Shikkee asset
library (real product photos/video). Requires a service account JSON at the
path in GOOGLE_APPLICATION_CREDENTIALS, shared with edit/view access to the
asset folder.

Per the asset-library rules: prefer an equivalent asset already hosted on
shikkee.com's WordPress media library over pulling large files through this
client -- Drive is primarily for discovery, WordPress-hosted URLs are what
actually get attached to HeyGen calls or Metricool posts.
"""
from __future__ import annotations

from google.oauth2 import service_account
from googleapiclient.discovery import build
from shikkee_agent.config import settings

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class GoogleDriveClient:
    def __init__(self, credentials_path: str = "./service-account.json"):
        creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        self.service = build("drive", "v3", credentials=creds)

    def list_children(self, folder_id: str | None = None) -> list[dict]:
        folder_id = folder_id or settings.gdrive_asset_root_folder_id
        resp = self.service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="files(id, name, mimeType, webViewLink)",
            pageSize=200,
        ).execute()
        return resp.get("files", [])

    def search(self, name_contains: str) -> list[dict]:
        resp = self.service.files().list(
            q=f"name contains '{name_contains}' and trashed = false",
            fields="files(id, name, mimeType, webViewLink, parents)",
            pageSize=50,
        ).execute()
        return resp.get("files", [])
