import os

import main


def make_request(recipients=None):
    if recipients is None:
        recipients = [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
        ]
    return {"course_name": "Python Basics", "issue_date": "2026-01-15", "recipients": recipients}


# 1. Creating a generation job
def test_create_job(client):
    response = client.post("/jobs", json=make_request())

    assert response.status_code == 202
    assert response.json()["id"] is not None
    assert response.json()["total"] == 2


# 2. Input validation
def test_missing_course_name_is_rejected(client):
    body = make_request()
    del body["course_name"]
    assert client.post("/jobs", json=body).status_code == 422


def test_empty_recipient_list_is_rejected(client):
    assert client.post("/jobs", json=make_request([])).status_code == 422


def test_invalid_recipients_are_marked_failed_but_valid_ones_still_work(client):
    recipients = [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "No Email"},
        {"name": "Bad Email", "email": "not-an-email"},
    ]
    job_id = client.post("/jobs", json=make_request(recipients)).json()["id"]

    job = client.get(f"/jobs/{job_id}").json()

    assert job["success_count"] == 1
    assert job["failed_count"] == 2


# 3. Certificate generation
def test_certificate_pdf_is_created(client):
    job_id = client.post("/jobs", json=make_request()).json()["id"]

    job = client.get(f"/jobs/{job_id}").json()

    assert all(c["status"] == "success" for c in job["certificates"])
    assert len(os.listdir(f"test_certificates/job_{job_id}")) == 2


# 4. Job status / progress
def test_job_status_and_counts(client):
    job_id = client.post("/jobs", json=make_request()).json()["id"]

    job = client.get(f"/jobs/{job_id}").json()

    assert job["status"] == "completed"
    assert job["total"] == 2
    assert job["success_count"] == 2
    assert job["failed_count"] == 0


# 5. Handling an individual certificate failure
def test_one_failure_does_not_stop_other_certificates(client, monkeypatch):
    real_function = main.create_certificate_pdf

    def fake_create(name, course, date, path):
        if name == "Bob":
            raise Exception("something went wrong")
        real_function(name, course, date, path)

    monkeypatch.setattr(main, "create_certificate_pdf", fake_create)

    recipients = [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
        {"name": "Carol", "email": "carol@example.com"},
    ]
    job_id = client.post("/jobs", json=make_request(recipients)).json()["id"]
    job = client.get(f"/jobs/{job_id}").json()

    assert job["success_count"] == 2
    assert job["failed_count"] == 1
    status_by_name = {c["recipient_name"]: c["status"] for c in job["certificates"]}
    assert status_by_name == {"Alice": "success", "Bob": "failed", "Carol": "success"}


# 6. Retrieving generated certificates
def test_download_certificate(client):
    job_id = client.post("/jobs", json=make_request()).json()["id"]
    cert = client.get(f"/jobs/{job_id}").json()["certificates"][0]

    response = client.get(cert["download_url"])

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
