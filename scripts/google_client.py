"""Talk to Google Drive and Slides, either with Google's own Python client or through the gws CLI."""
import json
import subprocess
import urllib.request
from pathlib import Path

PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
SLIDES_MIME = "application/vnd.google-apps.presentation"
# drive.file only reaches files this tool created, which is all it needs.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CONFIG = Path.home() / ".config" / "deck-builder"


class ApiClient:
    """Google's official client, signed in with the user's own OAuth client (see references/google-auth.md)."""

    def __init__(self, client_secret=None):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        token = CONFIG / "token.json"
        secret = Path(client_secret) if client_secret else CONFIG / "client_secret.json"
        creds = Credentials.from_authorized_user_file(str(token), SCOPES) if token.exists() else None
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            if not secret.exists():
                raise SystemExit(f"No Google sign-in yet. Follow references/google-auth.md, then put the OAuth client file at {secret}")
            creds = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES).run_local_server(port=0)
        CONFIG.mkdir(parents=True, exist_ok=True)
        token.write_text(creds.to_json())
        token.chmod(0o600)
        self.drive = build("drive", "v3", credentials=creds)
        self.slides = build("slides", "v1", credentials=creds)

    def import_pptx(self, pptx, title, file_id=None):
        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(str(pptx), mimetype=PPTX_MIME)
        if file_id:
            return self.drive.files().update(fileId=file_id, media_body=media, fields="id").execute()["id"]
        body = {"name": title, "mimeType": SLIDES_MIME}
        return self.drive.files().create(body=body, media_body=media, fields="id").execute()["id"]

    def revision(self, file_id):
        """An id that changes only when the deck's content changes."""
        return self.slides.presentations().get(presentationId=file_id, fields="revisionId").execute()["revisionId"]

    def page_ids(self, file_id):
        pres = self.slides.presentations().get(presentationId=file_id, fields="slides.objectId").execute()
        return [slide["objectId"] for slide in pres.get("slides", [])]

    def thumbnail_url(self, file_id, page_id):
        return self.slides.presentations().pages().getThumbnail(
            presentationId=file_id, pageObjectId=page_id, thumbnailProperties_thumbnailSize="LARGE").execute()["contentUrl"]


class GwsClient:
    """The same calls through the gws CLI, for people who already use it."""

    def _run(self, *args, cwd=None):
        out = subprocess.run(["gws", *args], capture_output=True, text=True, cwd=cwd)
        text = "\n".join(line for line in out.stdout.splitlines() if "keyring backend" not in line)
        if out.returncode:
            raise SystemExit(f"gws {' '.join(args[:3])} failed:\n{text[-1500:]}{out.stderr[-1500:]}")
        return json.loads(text) if text.strip() else {}

    def import_pptx(self, pptx, title, file_id=None):
        # gws only uploads files inside its working directory, so run it from the file's folder.
        pptx = Path(pptx).resolve()
        upload = ["--upload", pptx.name, "--upload-content-type", PPTX_MIME]
        if file_id:
            return self._run("drive", "files", "update", "--params", json.dumps({"fileId": file_id}), *upload, cwd=pptx.parent)["id"]
        body = {"name": title, "mimeType": SLIDES_MIME}
        return self._run("drive", "files", "create", "--json", json.dumps(body), *upload, cwd=pptx.parent)["id"]

    def revision(self, file_id):
        return self._run("slides", "presentations", "get", "--params", json.dumps({"presentationId": file_id, "fields": "revisionId"}))["revisionId"]

    def page_ids(self, file_id):
        pres = self._run("slides", "presentations", "get", "--params", json.dumps({"presentationId": file_id, "fields": "slides.objectId"}))
        return [slide["objectId"] for slide in pres.get("slides", [])]

    def thumbnail_url(self, file_id, page_id):
        params = {"presentationId": file_id, "pageObjectId": page_id, "thumbnailProperties.thumbnailSize": "LARGE"}
        return self._run("slides", "presentations", "pages", "getThumbnail", "--params", json.dumps(params))["contentUrl"]


def connect(via, client_secret=None):
    return GwsClient() if via == "gws" else ApiClient(client_secret)


def download(url, path):
    with urllib.request.urlopen(url) as response:
        Path(path).write_bytes(response.read())
