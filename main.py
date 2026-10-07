import os
import re
from datetime import date

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine, get_db
from generator import create_certificate_pdf
from models import Certificate, Job
from schemas import JobOut, JobRequest

CERT_DIR = os.getenv("CERT_DIR", "certificates")
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Bulk Certificate Generator")


def validate_recipient(recipient):
    """Returns an error message if the recipient is invalid, otherwise None."""
    if not isinstance(recipient, dict):
        return "Recipient must be an object with name and email"

    name = recipient.get("name")
    email = recipient.get("email")

    if not isinstance(name, str) or not name.strip():
        return "name is required"
    if not isinstance(email, str) or not re.match(EMAIL_PATTERN, email.strip()):
        return "email is missing or invalid"
    return None


def process_job(job_id: int):
    """Runs in the background. Generates a certificate for every pending recipient."""
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        job.status = "processing"
        db.commit()

        pending = db.query(Certificate).filter_by(job_id=job_id, status="pending").all()
        for cert in pending:
            # try/except per certificate: one failure must not stop the others
            try:
                path = os.path.join(CERT_DIR, f"job_{job_id}", f"certificate_{cert.id}.pdf")
                create_certificate_pdf(cert.recipient_name, job.course_name, job.issue_date, path)
                cert.status = "success"
                cert.file_path = path
                job.success_count += 1
            except Exception as e:
                cert.status = "failed"
                cert.error_message = str(e)
                job.failed_count += 1
            db.commit()  # commit after each one so progress can be seen

        job.status = "completed"
        db.commit()
    finally:
        db.close()


@app.post("/jobs", status_code=202, response_model=JobOut)
def create_job(request: JobRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = Job(
        course_name=request.course_name.strip(),
        issue_date=str(request.issue_date or date.today()),
        status="pending",
        total=len(request.recipients),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    for recipient in request.recipients:
        error = validate_recipient(recipient)
        if error:
            # invalid recipient: save it as failed, but keep going with the others
            raw = recipient if isinstance(recipient, dict) else {}
            db.add(Certificate(
                job_id=job.id,
                recipient_name=str(raw.get("name"))[:255] if raw.get("name") is not None else None,
                recipient_email=str(raw.get("email"))[:255] if raw.get("email") is not None else None,
                status="failed",
                error_message=error,
            ))
            job.failed_count += 1
        else:
            db.add(Certificate(
                job_id=job.id,
                recipient_name=recipient["name"].strip(),
                recipient_email=recipient["email"].strip(),
                status="pending",
            ))
    db.commit()

    background_tasks.add_task(process_job, job.id)
    db.refresh(job)
    return job


@app.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/certificates/{certificate_id}/download")
def download_certificate(certificate_id: int, db: Session = Depends(get_db)):
    cert = db.get(Certificate, certificate_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert.status != "success":
        raise HTTPException(status_code=400, detail=f"Certificate is not available (status: {cert.status})")
    if not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="Certificate file not found")
    return FileResponse(cert.file_path, media_type="application/pdf",
                        filename=f"certificate_{cert.id}.pdf")
