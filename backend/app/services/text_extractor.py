import email
from email import policy
from html.parser import HTMLParser
from io import BytesIO, StringIO
from pathlib import Path

import extract_msg
import pdfplumber
import openpyxl


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text = StringIO()
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip_depth += 1
        if tag in ("br", "p", "div", "li", "tr"):
            self._text.write("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data):
        if not self._skip_depth:
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


def extract_text_from_msg(raw_bytes: bytes) -> dict:
    """Parse Outlook .msg files using extract-msg."""
    msg = extract_msg.Message(BytesIO(raw_bytes))
    try:
        sender = msg.sender or ""
        subject = msg.subject or ""
        body = msg.body or ""
        html_body = msg.htmlBody
        if isinstance(html_body, bytes):
            html_body = html_body.decode("utf-8", errors="replace")

        if not body and html_body:
            body = html_to_text(html_body)

        attachments = []
        for att in msg.attachments:
            if hasattr(att, 'data') and att.data:
                attachments.append({
                    "filename": att.longFilename or att.shortFilename or "unnamed",
                    "content_type": att.mimetype or "application/octet-stream",
                    "data": att.data,
                })

        return {
            "sender": sender,
            "subject": subject,
            "body": body,
            "html_body": html_body,
            "attachments": attachments,
        }
    finally:
        msg.close()


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
    try:
        text_parts = []
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                row_text = " | ".join(str(cell) for cell in row if cell is not None)
                if row_text:
                    text_parts.append(row_text)
        return "\n".join(text_parts)
    finally:
        wb.close()
