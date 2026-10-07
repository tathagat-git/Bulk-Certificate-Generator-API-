from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class JobRequest(BaseModel):
    course_name: str = Field(min_length=1)
    issue_date: Optional[date] = None  # defaults to today
    # Plain dicts so that ONE bad recipient does not reject the whole request.
    # Each recipient is checked separately in main.py.
    recipients: List[dict] = Field(min_length=1)


class CertificateOut(BaseModel):
    id: int
    recipient_name: Optional[str]
    recipient_email: Optional[str]
    status: str
    error_message: Optional[str]
    download_url: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class JobOut(BaseModel):
    id: int
    course_name: str
    issue_date: str
    status: str
    total: int
    success_count: int
    failed_count: int
    certificates: List[CertificateOut]

    model_config = ConfigDict(from_attributes=True)
