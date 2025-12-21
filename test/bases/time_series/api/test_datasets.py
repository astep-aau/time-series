import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_pagination import add_pagination
from sqlalchemy import StaticPool
from sqlmodel import Session, SQLModel, create_engine
from time_series.api.helpers import get_overview_service, get_session
from time_series.api.routes.datasets import router
from time_series.database.unit_of_work import UnitOfWork
from time_series.services import OverviewService


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine(
        "sqlite:///file:memdb?mode=memory&cache=shared&uri=true",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.connect() as conn:
        conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS timeseries")
        conn.commit()
    SQLModel.metadata.create_all(engine)

    yield engine
    engine.dispose()


@pytest.fixture
def test_session(test_engine):
    """Create a test database session."""
    with Session(test_engine) as session:
        yield session
        session.rollback()


@pytest.fixture
def client(test_session):
    """Create a FastAPI test client with a minimal app containing only the datasets router."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/datasets")
    add_pagination(test_app)

    def override_get_session():
        yield test_session

    def override_get_overview_service():
        return OverviewService(UnitOfWork(test_session))

    test_app.dependency_overrides[get_session] = override_get_session
    test_app.dependency_overrides[get_overview_service] = override_get_overview_service
    with TestClient(test_app) as test_client:
        yield test_client
    test_app.dependency_overrides.clear()


def test_get_datasets_empty(client: TestClient):
    """Test getting datasets when database is empty."""
    response = client.get("/datasets/")
    assert response.status_code == 200
    assert response.json() == {"datasets": []}


def test_post_dataset_success(client: TestClient):
    """Test successfully creating a dataset."""
    csv_content = "unix_time,values\n1761122229,0.019685\n1761122230,0.204010"
    response = client.post(
        "/datasets/?name=My Dataset&description=A test dataset",
        content=csv_content,
        headers={"Content-Type": "text/csv"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["id"] is not None


def test_post_dataset_invalid_csv(client: TestClient):
    """Test creating a dataset with invalid CSV format."""
    csv_content = "invalid,csv,format\nno,unix,time"
    response = client.post("/datasets/?name=Invalid Dataset", content=csv_content, headers={"Content-Type": "text/csv"})
    assert response.status_code == 400


def test_put_dataset_success(client: TestClient):
    """Test successfully adding data to an existing dataset."""
    csv_content = "unix_time,values\n1761122229,0.019685"
    response = client.post("/datasets/?name=Test Dataset", content=csv_content, headers={"Content-Type": "text/csv"})
    dataset_id = response.json()["id"]

    new_csv_content = "unix_time,values\n1761122231,0.345678"
    response = client.put(
        f"/datasets/?dataset_id={dataset_id}", content=new_csv_content, headers={"Content-Type": "text/csv"}
    )
    assert response.status_code == 200


def test_put_dataset_nonexistent(client: TestClient):
    """Test adding data to a non-existent dataset."""
    csv_content = "unix_time,values\n1761122229,0.019685"
    response = client.put("/datasets/?dataset_id=99999", content=csv_content, headers={"Content-Type": "text/csv"})
    assert response.status_code == 400


def test_get_dataset_success(client: TestClient):
    """Test getting a specific dataset by ID."""
    csv_content = "unix_time,values\n1761122229,0.019685\n1761122230,0.204010"
    response = client.post("/datasets/?name=Test Dataset", content=csv_content, headers={"Content-Type": "text/csv"})
    dataset_id = response.json()["id"]

    response = client.get(f"/datasets/{dataset_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dataset_id
    assert data["name"] == "Test Dataset"
    assert data["num_entries"] == 2


def test_get_dataset_nonexistent(client: TestClient):
    """Test getting a non-existent dataset."""
    response = client.get("/datasets/99999")
    assert response.status_code == 200
    data = response.json()
    assert "error" in data


def test_delete_dataset_success(client: TestClient):
    """Test successfully deleting a dataset."""
    csv_content = "unix_time,values\n1761122229,0.019685"
    response = client.post(
        "/datasets/?name=Dataset to Delete", content=csv_content, headers={"Content-Type": "text/csv"}
    )
    dataset_id = response.json()["id"]

    response = client.delete(f"/datasets/{dataset_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == dataset_id


def test_delete_dataset_nonexistent(client: TestClient):
    """Test deleting a non-existent dataset."""
    response = client.delete("/datasets/99999")
    assert response.status_code == 404


def test_get_records_all(client: TestClient):
    """Test getting all records from a dataset."""
    csv_content = "unix_time,values\n1761122229,0.019685\n1761122230,0.204010\n1761122231,0.345678"
    response = client.post("/datasets/?name=Test Dataset", content=csv_content, headers={"Content-Type": "text/csv"})
    dataset_id = response.json()["id"]

    response = client.get(f"/datasets/{dataset_id}/records")
    data = response.json()

    assert response.status_code == 200
    assert "items" in data
    assert len(data["items"]) == 3
    assert data["items"][0]["value"] == 0.019685
    assert data["items"][1]["value"] == 0.20401
    assert data["items"][2]["value"] == 0.345678
    assert "time" in data["items"][0]
    assert "time" in data["items"][1]
    assert "time" in data["items"][2]


def test_get_records_nonexistent_dataset(client: TestClient):
    """Test getting records from a non-existent dataset."""
    response = client.get("/datasets/99999/records")
    assert response.status_code in [200, 404]


def test_get_dataset_analyses(client: TestClient):
    """Test getting analyses for a dataset."""
    csv_content = "unix_time,values\n1761122229,0.019685"
    response = client.post("/datasets/?name=Test Dataset", content=csv_content, headers={"Content-Type": "text/csv"})
    dataset_id = response.json()["id"]

    response = client.get(f"/datasets/{dataset_id}/analyses")
    assert response.status_code == 200
    data = response.json()
    assert "analyses" in data
    assert data["analyses"] == []
