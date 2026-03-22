import email
from email import policy
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path

import pdfplumber
import openpyxl


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text = StringIO()
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True
        if tag in ("br", "p", "div", "li", "tr"):
            self._text.write("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self._text.write(data)

    def get_text(self) -> str:
        return self._text.getvalue().strip()


def html_to_text(html: str | None) -> str:
    if not html:
        return ""
    extractor = _HTMLTextExtractor()
    extractor.feed(html)
    return extractor.get_text()


def extract_text_from_eml(raw_bytes: bytes) -> dict:
    msg = email.message_from_bytes(raw_bytes, policy=policy.default)
    sender = str(msg.get("From", ""))
    subject = str(msg.get("Subject", ""))

    body = ""
    html_body = None
    attachments = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in disposition:
                attachments.append({
                    "filename": part.get_filename() or "unnamed",
                    "content_type": content_type,
                    "data": part.get_payload(decode=True),
                })
            elif content_type == "text/plain":
                body = part.get_content()
            elif content_type == "text/html":
                html_body = part.get_content()
    else:
        content_type = msg.get_content_type()
        if content_type == "text/html":
            html_body = msg.get_content()
            body = html_to_text(html_body)
        else:
            body = msg.get_content()

    if not body and html_body:
        body = html_to_text(html_body)

    return {
        "sender": sender,
        "subject": subject,
        "body": body,
        "html_body": html_body,
        "attachments": attachments,
    }


def extract_text_from_pdf(file_path: str | Path) -> str:
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_xlsx(file_path: str | Path) -> str:
    wb = openpyxl.load_workbook(file_path, read_only=True)
    text_parts = []
    for sheet in wb.worksheets:
        for row in sheet.iter_rows(values_only=True):
            row_text = " | ".join(str(cell) for cell in row if cell is not None)
            if row_text:
                text_parts.append(row_text)
    wb.close()
    return "\n".join(text_parts)
