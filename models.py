from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    course_name = Column(String, nullable=False)
    issue_date = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending -> processing -> completed
    total = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)

    certificates = relationship("Certificate", back_populates="job")


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    recipient_name = Column(String)
    recipient_email = Column(String)
    status = Column(String, default="pending")  # pending / success / failed
    error_message = Column(String, nullable=True)
    file_path = Column(String, nullable=True)

    job = relationship("Job", back_populates="certificates")

    @property
    def download_url(self):
        if self.status == "success":
            return f"/certificates/{self.id}/download"
        return None
