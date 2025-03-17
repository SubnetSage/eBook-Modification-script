import google.generativeai as genai  # Gemini API
from googleapiclient.discovery import build
from google.oauth2 import service_account
import io
from googleapiclient.http import MediaIoBaseDownload

# Configure Gemini API
# Replace 'YOUR_API_KEY' with your actual Gemini API key, but DO NOT share it publicly
genai.configure(api_key="YOUR_API_KEY")  # Ensure your Gemini API key is set correctly

def simplify_text(text):
    """Uses Gemini API to rewrite text for a high school audience."""
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = f"Rewrite the following so that a high school student can understand it:\n{text}"
    response = model.generate_content(prompt)
    return response.text if response else ""

# Configure Google Docs API
SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]
# Replace 'YOUR_SERVICE_ACCOUNT_FILE_PATH' with the actual path to your service account file, but DO NOT share it publicly
SERVICE_ACCOUNT_FILE = "YOUR_SERVICE_ACCOUNT_FILE_PATH"  # Ensure the path is correct
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("docs", "v1", credentials=credentials)
drive_service = build("drive", "v3", credentials=credentials)

def get_google_doc_content(doc_id):
    """Fetches the content of a Google Doc and returns a list of paragraphs."""
    document = service.documents().get(documentId=doc_id).execute()
    paragraphs = []
    for element in document['body']['content']:
        if 'paragraph' in element:
            paragraph_text = ""
            for text_run in element['paragraph']['elements']:
                if 'textRun' in text_run:
                    paragraph_text += text_run['textRun']['content']
            if paragraph_text.strip():  # Only add non-empty paragraphs
                paragraphs.append(paragraph_text)
    return paragraphs

def create_google_doc(title, content):
    """Creates a new Google Doc with the simplified content."""
    doc = service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    
    # Insert simplified content into the new document
    requests = []
    for paragraph in content:
        requests.append({
            "insertText": {
                "location": {"index": 1},
                "text": paragraph + "\n\n"  # Add extra newline for separation
            }
        })
    
    service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": requests}
    ).execute()

    return doc_id

def export_to_pdf(doc_id):
    """Exports the Google Doc as a PDF file."""
    request = drive_service.files().export_media(
        fileId=doc_id, mimeType="application/pdf"
    )
    fh = io.FileIO(f"{doc_id}.pdf", "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")
    return f"{doc_id}.pdf"

def process_google_doc(doc_id):
    """Fetches the content from a Google Doc, simplifies it, and creates a single Google Doc with the simplified content."""
    # Get content from the original Google Doc
    paragraphs = get_google_doc_content(doc_id)
    
    # Simplify the content using Gemini API
    simplified_paragraphs = []
    for i, paragraph in enumerate(paragraphs):
        print(f"Simplifying paragraph {i+1}/{len(paragraphs)}")
        simplified_content = simplify_text(paragraph)
        simplified_paragraphs.append(simplified_content)
    
    # Create a new Google Doc with the simplified content (all in one document)
    new_doc_title = "Simplified Google Doc Content"
    new_doc_id = create_google_doc(new_doc_title, simplified_paragraphs)
    print(f"New Google Doc created with ID: {new_doc_id}")
    
    # Export the new Google Doc to PDF
    pdf_file = export_to_pdf(new_doc_id)
    print(f"PDF file created: {pdf_file}")

# Example usage
# Replace 'YOUR_DOC_ID' with the actual Google Doc ID but DO NOT share it publicly
process_google_doc("YOUR_DOC_ID")
