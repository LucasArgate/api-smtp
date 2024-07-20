import json
import smtplib
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Form, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email import encoders
from email.utils import formatdate
import mimetypes
import os
from minio import Minio
from minio.error import S3Error

app = FastAPI()

class EmailRequest(BaseModel):
    recipient_email: str
    subject: str
    body: str
    debug: Optional[bool] = False

def load_smtp_config():
    with open('smtp_config.json', 'r') as file:
        return json.load(file)

smtp_config = load_smtp_config()

# Initialize MinIO client
minio_client = Minio(
    smtp_config.get('minio_server', "localhost:9000"),
    access_key=smtp_config.get('minio_access_key', "minioadmin"),
    secret_key=smtp_config.get('minio_secret_key', "minioadmin"),
    secure=smtp_config.get('minio_secure', False),
)

def save_email_result(email_id: str, status: str, detail: str, client_ip: str, headers: dict, message_length: int):
    date_str = datetime.now().strftime("%Y-%m-%d")
    status_dir = "success" if status == "success" else "failure"
    dir_path = os.path.join("data", date_str, status_dir)
    os.makedirs(dir_path, exist_ok=True)

    result = {
        "email_id": email_id,
        "status": status,
        "detail": detail,
        "timestamp": datetime.now().isoformat(),
        "client_ip": client_ip,
        "headers": headers,
        "message_length": message_length
    }

    with open(os.path.join(dir_path, f"{email_id}.json"), "w") as f:
        json.dump(result, f, indent=4)

def save_debug_email(email_id: str, message: MIMEMultipart):
    date_str = datetime.now().strftime("%Y-%m-%d")
    dir_path = os.path.join("data", date_str, "debug")
    os.makedirs(dir_path, exist_ok=True)

    with open(os.path.join(dir_path, f"{email_id}_email.txt"), "w") as f:
        f.write(message.as_string())

def upload_to_minio(file: UploadFile):
    bucket_name = "emails"
    object_name = f"{uuid.uuid4()}_{file.filename}"

    # Save the file temporarily
    temp_file_path = f"/tmp/{object_name}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(file.file.read())

    # Upload the file to MinIO
    minio_client.fput_object(bucket_name, object_name, temp_file_path)

    # Remove the temporary file
    os.remove(temp_file_path)

    return object_name

def add_attachment(object_name: str):
    bucket_name = "emails"
    response = minio_client.get_object(bucket_name, object_name)
    file_content = response.read()
    filename = object_name.split("_", 1)[1]
    ctype, encoding = mimetypes.guess_type(filename)
    if ctype is None or encoding is not None:
        ctype = "application/octet-stream"
    maintype, subtype = ctype.split('/', 1)

    if maintype == "text":
        attachment = MIMEText(file_content.decode('utf-8'), _subtype=subtype)
    elif maintype == "image":
        attachment = MIMEImage(file_content, _subtype=subtype)
    elif maintype == "audio":
        attachment = MIMEAudio(file_content, _subtype=subtype)
    else:
        attachment = MIMEBase(maintype, subtype)
        attachment.set_payload(file_content)
        encoders.encode_base64(attachment)

    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
    return attachment

def send_email_task(email_request: EmailRequest, email_id: str, client_ip: str, headers: dict, attachment_names: List[Optional[str]]):
    try:
        message = MIMEMultipart()
        message["From"] = smtp_config["sender_email"]
        message["To"] = email_request.recipient_email
        message["Subject"] = email_request.subject
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = f"<{email_id}@{smtp_config['sender_domain']}>"

        message.attach(MIMEText(email_request.body, "plain"))

        if attachment_names:
            for object_name in attachment_names:
                if object_name:  # Ensure object_name is not None
                    attachment_part = add_attachment(object_name)
                    message.attach(attachment_part)

        message_length = len(message.as_string())

        if smtp_config["use_ssl"]:
            with smtplib.SMTP_SSL(smtp_config["smtp_server"], smtp_config["smtp_port"]) as server:
                if smtp_config["use_password"]:
                    server.login(smtp_config["sender_email"], smtp_config["sender_password"])
                server.sendmail(smtp_config["sender_email"], email_request.recipient_email, message.as_string())
        else:
            with smtplib.SMTP(smtp_config["smtp_server"], smtp_config["smtp_port"]) as server:
                if smtp_config.get("use_tls"):
                    server.starttls()
                if smtp_config["use_password"]:
                    server.login(smtp_config["sender_email"], smtp_config["sender_password"])
                server.sendmail(smtp_config["sender_email"], email_request.recipient_email, message.as_string())

        save_email_result(email_id, "success", "Email sent successfully", client_ip, headers, message_length)

        if email_request.debug:
            save_debug_email(email_id, message)
    
    except smtplib.SMTPAuthenticationError:
        save_email_result(email_id, "failure", "Authentication failed. Check your username and password.", client_ip, headers, 0)
    except smtplib.SMTPConnectError:
        save_email_result(email_id, "failure", "Failed to connect to the SMTP server.", client_ip, headers, 0)
    except smtplib.SMTPRecipientsRefused:
        save_email_result(email_id, "failure", "Recipient address rejected by the server.", client_ip, headers, 0)
    except smtplib.SMTPSenderRefused:
        save_email_result(email_id, "failure", "Sender address rejected by the server.", client_ip, headers, 0)
    except smtplib.SMTPDataError:
        save_email_result(email_id, "failure", "The SMTP server refused to accept the message data.", client_ip, headers, 0)
    except smtplib.SMTPException as e:
        save_email_result(email_id, "failure", f"An SMTP error occurred: {e}", client_ip, headers, 0)
    except Exception as e:
        save_email_result(email_id, "failure", f"An unexpected error occurred: {e}", client_ip, headers, 0)

@app.post("/send-email")
async def send_email(
    background_tasks: BackgroundTasks,
    request: Request,
    recipient_email: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    debug: bool = Form(False),
    attachments: Optional[List[UploadFile]] = File(None)
):
    email_id = str(uuid.uuid4())
    client_ip = request.client.host
    headers = dict(request.headers)
    email_request = EmailRequest(
        recipient_email=recipient_email,
        subject=subject,
        body=body,
        debug=debug
    )
    
    attachment_names = []
    if attachments:
        for attachment in attachments:
            object_name = upload_to_minio(attachment)
            attachment_names.append(object_name)
    
    background_tasks.add_task(send_email_task, email_request, email_id, client_ip, headers, attachment_names)
    return {"message": "Email is being sent in the background", "email_id": email_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
