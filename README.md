# Bulk Certificate Generator

A backend API built with **FastAPI**, **SQLite** (SQLAlchemy) and **ReportLab**.
The client sends one request with many recipients, the server creates a PDF certificate for
each valid recipient, and the client can check the progress and download the certificates.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run the application

```bash
uvicorn main:app --reload
```

API docs: http://127.0.0.1:8000/docs

## Run the tests

```bash
pytest
```

## Submit a certificate generation request

`POST /jobs`

```bash
curl -X POST http://127.0.0.1:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "course_name": "Python Basics",
    "issue_date": "2026-01-15",
    "recipients": [
      {"name": "Alice", "email": "alice@example.com"},
      {"name": "Bob", "email": "bob@example.com"}
    ]
  }'
```

The response contains the job `id`.

## Check progress / result

`GET /jobs/{job_id}` returns the job `status` (`pending`, `processing`, `completed`),
`total`, `success_count`, `failed_count`, and one entry per recipient with its `status`
(`pending` / `success` / `failed`), an `error_message` if it failed, and a `download_url`
if it succeeded.

```bash
curl http://127.0.0.1:8000/jobs/1
```

## Retrieve generated certificates

`GET /certificates/{certificate_id}/download` (use the `download_url` from the job result)

```bash
curl -o certificate.pdf http://127.0.0.1:8000/certificates/1/download
```

## Design decisions

**Background processing.** `POST /jobs` saves the job and recipients, then returns immediately.
The certificates are generated afterwards with FastAPI's `BackgroundTasks`, so the client does
not wait with an open connection for a large list and can check progress with `GET /jobs/{id}`.
I used `BackgroundTasks` because it is built into FastAPI and needs no extra tools. The
downside is that a job does not continue if the server restarts while it is running.

**Validation.** `course_name` and at least one recipient are required (otherwise `422`).
Each recipient is checked separately: `name` is required and `email` must look valid. An
invalid recipient is saved as `failed` with an error message, and the others are still processed.

**Failure handling.** Each certificate is generated in its own `try/except` and saved after each
one. If one fails it is marked `failed` and the next recipient is processed.
