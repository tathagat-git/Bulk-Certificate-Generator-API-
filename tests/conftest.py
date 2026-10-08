import os
import shutil

# Use a separate database and folder for tests 
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["CERT_DIR"] = "test_certificates"

import pytest
from fastapi.testclient import TestClient

from database import Base, engine
from main import app


@pytest.fixture(autouse=True)
def clean_state():
    """Fresh database and certificate folder for every test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    shutil.rmtree("test_certificates", ignore_errors=True)
    yield


@pytest.fixture
def client():
    # TestClient runs background tasks before returning, so the job is finished
    # by the time we get the response back.
    return TestClient(app)
