from datetime import datetime, timedelta

import pytest
from sqlmodel import SQLModel, create_engine
from time_series.database import (
    AnalysisRepository,
    AnomalyRepository,
    AnomalyType,
    DatapointRepository,
    DatasetRepository,
)


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine("sqlite:///file:memdb?mode=memory&cache=shared&uri=true", echo=False)
    with engine.connect() as conn:
        conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS timeseries")
        conn.commit()
    SQLModel.metadata.create_all(engine)

    yield engine
    engine.dispose()


@pytest.fixture
def dataset_repo(test_engine):
    """Create a DatasetRepository instance"""
    return DatasetRepository(engine=test_engine)


@pytest.fixture
def datapoint_repo(test_engine):
    """Create a DatapointRepository instance"""
    return DatapointRepository(engine=test_engine)


@pytest.fixture
def sample_dataset(dataset_repo):
    """Create a sample dataset for testing"""
    dataset = dataset_repo.create(
        name=f"Test Dataset {datetime.now().timestamp()}",
        description="Test dataset",
    )
    yield dataset


@pytest.fixture
def dataset_with_datapoints(sample_dataset, datapoint_repo):
    """Create a dataset with sample datapoints"""
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    datapoints = [
        {"dataset_id": sample_dataset.id, "time": base_time + timedelta(minutes=i), "value": 20.0 + (i * 0.5)}
        for i in range(10)
    ]
    datapoint_repo.bulk_create(datapoints)
    yield sample_dataset


@pytest.fixture
def analysis_repo(test_engine):
    """Create an AnalysisRepository instance"""
    return AnalysisRepository(engine=test_engine)


@pytest.fixture
def anomaly_repo(test_engine):
    """Create an AnomalyRepository instance"""
    return AnomalyRepository(engine=test_engine)


@pytest.fixture
def sample_analysis(sample_dataset, analysis_repo):
    """Create a sample analysis"""
    analysis = analysis_repo.create(
        dataset_id=sample_dataset.id,
        model="IsolationForest",
        name=f"IF_Analysis_{datetime.now().timestamp()}",
        description="Isolation Forest anomaly detection",
    )
    yield analysis


@pytest.fixture
def analysis_with_anomalies(sample_analysis, anomaly_repo):
    """Create an analysis with sample anomalies"""
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    anomalies = [
        {
            "analysis_id": sample_analysis.id,
            "start": base_time + timedelta(hours=i),
            "end": base_time + timedelta(hours=i, minutes=30),
            "type": AnomalyType.point,
            "validated": False,
        }
        for i in range(5)
    ]
    anomaly_repo.bulk_create(anomalies)
    yield sample_analysis


class TestDatasetRepositry:
    """Tests for DatasetRepository"""

    def test_create_dataset(self, dataset_repo):
        """Test creating a dataset"""
        dataset = dataset_repo.create(
            name=f"Test Dataset {datetime.now().timestamp()}",
            description="This is a test dataset",
        )

        assert dataset.id is not None
        assert dataset.name is not None
        assert dataset.description == "This is a test dataset"

    def test_get_all_datasets(self, sample_dataset, dataset_repo):
        """Test retrieving all datasets"""
        datasets = dataset_repo.get_all()

        assert isinstance(datasets, list)
        assert len(datasets) >= 1
        assert any(ds.id == sample_dataset.id for ds in datasets)

    def test_get_dataset_by_id(self, sample_dataset, dataset_repo):
        """Test retrieving a dataset by ID"""
        dataset = dataset_repo.get_by_id(sample_dataset.id)

        assert dataset is not None
        assert dataset.id == sample_dataset.id
        assert dataset.name == sample_dataset.name

    def test_get_dataset_by_name(self, sample_dataset, dataset_repo):
        """Test retrieving a dataset by name"""
        dataset = dataset_repo.get_by_name(sample_dataset.name)

        assert dataset is not None
        assert dataset.id == sample_dataset.id
        assert dataset.name == sample_dataset.name

    def test_update_dataset(self, sample_dataset, dataset_repo):
        """Test updating a dataset"""
        new_description = f"Updated at {datetime.now()}"
        updated_dataset = dataset_repo.update(sample_dataset.id, description=new_description)

        assert updated_dataset is not None
        assert updated_dataset.description == new_description

    def test_delete_dataset(self, sample_dataset, dataset_repo):
        """Test deleting a dataset"""
        dataset_id = sample_dataset.id
        success = dataset_repo.delete(dataset_id)

        assert success is True
        assert dataset_repo.get_by_id(dataset_id) is None

    def test_get_nonexistent_dataset(self, dataset_repo):
        """Test getting a dataset that doesn't exist"""
        dataset = dataset_repo.get_by_id(99999)
        assert dataset is None


class TestDatapointRepository:
    """Tests for DatapointRepository"""

    def test_create_datapoint(self, sample_dataset, datapoint_repo):
        """Test creating a single datapoint"""
        now = datetime.now()
        datapoint = datapoint_repo.create(dataset_id=sample_dataset.id, time=now, value=25.5)

        assert datapoint.dataset_id == sample_dataset.id
        assert datapoint.value == 25.5
        assert datapoint.time == now

    def test_bulk_create_datapoints(self, sample_dataset, datapoint_repo):
        """Test creating multiple datapoints"""
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        datapoints = [
            {"dataset_id": sample_dataset.id, "time": base_time + timedelta(minutes=i), "value": 20.0 + (i * 0.5)}
            for i in range(10)
        ]

        count = datapoint_repo.bulk_create(datapoints)
        assert count == 10

    def test_get_datapoints_by_dataset(self, dataset_with_datapoints, datapoint_repo):
        """Test retrieving all datapoints for a dataset"""
        datapoints = datapoint_repo.get_by_dataset(dataset_with_datapoints.id)

        assert isinstance(datapoints, list)
        assert len(datapoints) == 10

    def test_get_datapoints_range(self, dataset_with_datapoints, datapoint_repo):
        """Test retrieving datapoints within a time range"""
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        start_time = base_time + timedelta(minutes=2)
        end_time = base_time + timedelta(minutes=7)

        datapoints = datapoint_repo.get_range(
            dataset_id=dataset_with_datapoints.id, start_time=start_time, end_time=end_time
        )

        assert isinstance(datapoints, list)
        assert len(datapoints) == 6  # Minutes 2, 3, 4, 5, 6, 7
        # Verify all datapoints are in the range
        for dp in datapoints:
            assert start_time <= dp.time <= end_time

    def test_delete_old_datapoints(self, dataset_with_datapoints, datapoint_repo):
        """Test deleting old datapoints"""
        before_count = len(datapoint_repo.get_by_dataset(dataset_with_datapoints.id))

        # Delete datapoints older than 5 minutes from base time
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        cutoff_time = base_time + timedelta(minutes=5)
        deleted_count = datapoint_repo.delete_before(dataset_with_datapoints.id, cutoff_time)

        after_count = len(datapoint_repo.get_by_dataset(dataset_with_datapoints.id))
        assert after_count == before_count - deleted_count
        assert deleted_count == 5  # Should delete datapoints 0-4

    def test_datapoints_ordered_by_time(self, dataset_with_datapoints, datapoint_repo):
        """Test that datapoints are returned in time order"""
        datapoints = datapoint_repo.get_by_dataset(dataset_with_datapoints.id)

        times = [dp.time for dp in datapoints]
        assert times == sorted(times), "Datapoints should be ordered by time"


class TestCascadeDelete:
    """Tests for cascade delete behavior"""

    def test_cascade_delete(self, dataset_repo, datapoint_repo):
        """Test that deleting a dataset cascades to datapoints"""
        # Create a dataset
        dataset = dataset_repo.create(
            name=f"Cascade Test {datetime.now().timestamp()}",
            description="Testing cascade delete",
        )

        # Add some datapoints
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        datapoint_repo.bulk_create(
            [{"dataset_id": dataset.id, "time": base_time + timedelta(minutes=i), "value": float(i)} for i in range(5)]
        )

        # Verify datapoints exist
        datapoints_before = datapoint_repo.get_by_dataset(dataset.id)
        assert len(datapoints_before) == 5

        # Delete the dataset
        dataset_repo.delete(dataset.id)

        # Verify datapoints are also deleted (cascade)
        datapoints_after = datapoint_repo.get_by_dataset(dataset.id)
        assert len(datapoints_after) == 0


class TestAnalysisRepositoryCreate:
    """Tests for creating analyses"""

    def test_create_analysis_complete(self, sample_dataset, analysis_repo):
        """Test creating an analysis with all fields"""
        analysis = analysis_repo.create(
            dataset_id=sample_dataset.id,
            model="LSTM_Autoencoder",
            name="LSTM_Test_Run_1",
            description="First test run with LSTM",
        )

        assert analysis.id is not None
        assert analysis.dataset_id == sample_dataset.id
        assert analysis.model == "LSTM_Autoencoder"
        assert analysis.name == "LSTM_Test_Run_1"
        assert analysis.description == "First test run with LSTM"

    def test_create_analysis_minimal(self, sample_dataset, analysis_repo):
        """Test creating an analysis with only required fields"""
        analysis = analysis_repo.create(
            dataset_id=sample_dataset.id,
            model="Z-Score",
            name="Z-Score_Run",
        )

        assert analysis.id is not None
        assert analysis.dataset_id == sample_dataset.id
        assert analysis.model == "Z-Score"
        assert analysis.name == "Z-Score_Run"
        assert analysis.description is None

    def test_create_multiple_analyses(self, sample_dataset, analysis_repo):
        """Test creating multiple analyses for the same dataset"""
        models = ["IsolationForest", "LSTM_Autoencoder", "Z-Score"]
        created_analyses = []

        for model in models:
            analysis = analysis_repo.create(
                dataset_id=sample_dataset.id,
                model=model,
                name=f"{model}_Run",
                description=f"Test run for {model}",
            )
            created_analyses.append(analysis)

        assert len(created_analyses) == 3
        assert all(a.id is not None for a in created_analyses)
        assert all(a.dataset_id == sample_dataset.id for a in created_analyses)

    def test_create_analysis_smap_models(self, sample_dataset, analysis_repo):
        """Test creating analyses with common SMAP model names"""
        smap_models = [
            "IsolationForest",
            "LSTM_Autoencoder",
            "GRU_Autoencoder",
            "Statistical_ZScore",
            "MAD",
            "ARIMA",
        ]

        for model in smap_models:
            analysis = analysis_repo.create(
                dataset_id=sample_dataset.id,
                model=model,
                name=f"{model}_SMAP",
            )
            assert analysis.model == model


class TestAnalysisRepositoryRead:
    """Tests for reading/retrieving analyses"""

    def test_get_analysis_by_id(self, sample_analysis, analysis_repo):
        """Test retrieving an analysis by ID"""
        retrieved = analysis_repo.get_by_id(sample_analysis.id)

        assert retrieved is not None
        assert retrieved.id == sample_analysis.id
        assert retrieved.model == sample_analysis.model
        assert retrieved.name == sample_analysis.name
        assert retrieved.description == sample_analysis.description

    def test_get_analysis_by_id_nonexistent(self, analysis_repo):
        """Test retrieving a non-existent analysis returns None"""
        retrieved = analysis_repo.get_by_id(99999)
        assert retrieved is None

    def test_get_by_dataset_empty(self, sample_dataset, analysis_repo):
        """Test getting analyses for a dataset with no analyses"""
        analyses = analysis_repo.get_by_dataset(sample_dataset.id)
        assert analyses == []

    def test_get_by_dataset_single(self, sample_analysis, analysis_repo):
        """Test getting analyses when there's only one"""
        analyses = analysis_repo.get_by_dataset(sample_analysis.dataset_id)

        assert len(analyses) == 1
        assert analyses[0].id == sample_analysis.id

    def test_get_by_dataset_multiple(self, sample_dataset, analysis_repo):
        """Test getting multiple analyses for a dataset"""
        created = []
        for i in range(5):
            analysis = analysis_repo.create(
                dataset_id=sample_dataset.id,
                model="IsolationForest",
                name=f"Analysis_{i}",
                description=f"Test analysis {i}",
            )
            created.append(analysis)

        analyses = analysis_repo.get_by_dataset(sample_dataset.id)

        assert len(analyses) == 5
        assert all(a.dataset_id == sample_dataset.id for a in analyses)

    def test_get_by_dataset_ordered_by_id(self, sample_dataset, analysis_repo):
        """Test that analyses are returned ordered by ID"""
        for i in range(5):
            analysis_repo.create(
                dataset_id=sample_dataset.id,
                model="Model",
                name=f"Analysis_{i}",
            )

        analyses = analysis_repo.get_by_dataset(sample_dataset.id)
        ids = [a.id for a in analyses]

        assert ids == sorted(ids), "Analyses should be ordered by ID"

    def test_get_by_dataset_isolation(self, dataset_repo, analysis_repo):
        """Test that get_by_dataset only returns analyses for that specific dataset"""
        dataset1 = dataset_repo.create(
            name=f"Dataset_1_{datetime.now().timestamp()}",
        )
        dataset2 = dataset_repo.create(
            name=f"Dataset_2_{datetime.now().timestamp()}",
        )

        # Create analyses for dataset1
        for i in range(3):
            analysis_repo.create(
                dataset_id=dataset1.id,
                model="Model_A",
                name=f"Dataset1_Analysis_{i}",
            )

        # Create analyses for dataset2
        for i in range(2):
            analysis_repo.create(
                dataset_id=dataset2.id,
                model="Model_B",
                name=f"Dataset2_Analysis_{i}",
            )

        analyses1 = analysis_repo.get_by_dataset(dataset1.id)
        analyses2 = analysis_repo.get_by_dataset(dataset2.id)

        assert len(analyses1) == 3
        assert len(analyses2) == 2
        assert all(a.dataset_id == dataset1.id for a in analyses1)
        assert all(a.dataset_id == dataset2.id for a in analyses2)


class TestAnalysisRepositoryUpdate:
    """Tests for updating analyses"""

    def test_update_single_field(self, sample_analysis, analysis_repo):
        """Test updating a single field"""
        new_description = "Updated description after parameter tuning"
        updated = analysis_repo.update(sample_analysis.id, description=new_description)

        assert updated is not None
        assert updated.id == sample_analysis.id
        assert updated.description == new_description
        assert updated.model == sample_analysis.model
        assert updated.name == sample_analysis.name

    def test_update_multiple_fields(self, sample_analysis, analysis_repo):
        """Test updating multiple fields at once"""
        updated = analysis_repo.update(
            sample_analysis.id,
            name="Updated_Name",
            description="Updated description",
            model="Updated_Model",
        )

        assert updated is not None
        assert updated.id == sample_analysis.id
        assert updated.name == "Updated_Name"
        assert updated.description == "Updated description"
        assert updated.model == "Updated_Model"

    def test_update_name_only(self, sample_analysis, analysis_repo):
        """Test updating only the name"""
        original_description = sample_analysis.description
        original_model = sample_analysis.model

        updated = analysis_repo.update(sample_analysis.id, name="New_Analysis_Name")

        assert updated.name == "New_Analysis_Name"
        assert updated.description == original_description
        assert updated.model == original_model

    def test_update_model_only(self, sample_analysis, analysis_repo):
        """Test updating only the model"""
        original_name = sample_analysis.name
        original_description = sample_analysis.description

        updated = analysis_repo.update(sample_analysis.id, model="NewModel")

        assert updated.model == "NewModel"
        assert updated.name == original_name
        assert updated.description == original_description

    def test_update_nonexistent_analysis(self, analysis_repo):
        """Test updating an analysis that doesn't exist returns None"""
        result = analysis_repo.update(99999, name="New Name")
        assert result is None

    def test_update_clears_description(self, sample_analysis, analysis_repo):
        """Test that updating can clear optional fields"""
        updated = analysis_repo.update(sample_analysis.id, description=None)

        assert updated is not None
        assert updated.description is None

    def test_update_persists_across_sessions(self, sample_analysis, analysis_repo):
        """Test that updates persist when retrieved in a new session"""
        # Update the analysis
        analysis_repo.update(sample_analysis.id, name="Persisted_Name")

        # Retrieve in a new session
        retrieved = analysis_repo.get_by_id(sample_analysis.id)

        assert retrieved.name == "Persisted_Name"


class TestAnalysisRepositoryDelete:
    """Tests for deleting analyses"""

    def test_delete_analysis(self, sample_analysis, analysis_repo):
        """Test deleting an analysis"""
        analysis_id = sample_analysis.id

        # Verify it exists
        assert analysis_repo.get_by_id(analysis_id) is not None

        # Delete it
        success = analysis_repo.delete(analysis_id)

        assert success is True
        assert analysis_repo.get_by_id(analysis_id) is None

    def test_delete_nonexistent_analysis(self, analysis_repo):
        """Test deleting an analysis that doesn't exist returns False"""
        success = analysis_repo.delete(99999)
        assert success is False

    def test_delete_removes_from_dataset_list(self, sample_dataset, analysis_repo):
        """Test that deleted analysis is removed from dataset's analysis list"""
        # Create multiple analyses
        analyses = []
        for i in range(3):
            analysis = analysis_repo.create(
                dataset_id=sample_dataset.id,
                model="Model",
                name=f"Analysis_{i}",
            )
            analyses.append(analysis)

        # Delete the middle one
        analysis_repo.delete(analyses[1].id)

        # Verify it's removed
        remaining = analysis_repo.get_by_dataset(sample_dataset.id)
        assert len(remaining) == 2
        assert analyses[1].id not in [a.id for a in remaining]
        assert analyses[0].id in [a.id for a in remaining]
        assert analyses[2].id in [a.id for a in remaining]

    def test_delete_multiple_analyses(self, sample_dataset, analysis_repo):
        """Test deleting multiple analyses"""
        # Create analyses
        created_ids = []
        for i in range(5):
            analysis = analysis_repo.create(
                dataset_id=sample_dataset.id,
                model="Model",
                name=f"Analysis_{i}",
            )
            created_ids.append(analysis.id)

        # Delete them one by one
        for analysis_id in created_ids:
            success = analysis_repo.delete(analysis_id)
            assert success is True

        # Verify all are gone
        remaining = analysis_repo.get_by_dataset(sample_dataset.id)
        assert len(remaining) == 0

    def test_delete_is_idempotent(self, sample_analysis, analysis_repo):
        """Test that deleting the same analysis twice returns False the second time"""
        analysis_id = sample_analysis.id

        # First delete
        first_delete = analysis_repo.delete(analysis_id)
        assert first_delete is True

        # Second delete
        second_delete = analysis_repo.delete(analysis_id)
        assert second_delete is False


class TestAnalysisWithAnomalies:
    """Tests for analysis interactions with anomalies"""

    def test_analysis_has_anomalies(self, analysis_with_anomalies, anomaly_repo):
        """Test that anomalies are properly linked to analysis"""
        anomalies = anomaly_repo.get_by_analysis(analysis_with_anomalies.id)

        assert len(anomalies) == 5
        assert all(a.analysis_id == analysis_with_anomalies.id for a in anomalies)

    def test_delete_analysis_cascades_to_anomalies(self, analysis_with_anomalies, analysis_repo, anomaly_repo):
        """Test that deleting an analysis also deletes its anomalies (cascade delete)"""
        analysis_id = analysis_with_anomalies.id

        # Verify anomalies exist
        anomalies_before = anomaly_repo.get_by_analysis(analysis_id)
        assert len(anomalies_before) == 5

        # Delete the analysis
        success = analysis_repo.delete(analysis_id)
        assert success is True

        # Verify anomalies are deleted
        anomalies_after = anomaly_repo.get_by_analysis(analysis_id)
        assert len(anomalies_after) == 0

    def test_update_analysis_preserves_anomalies(self, analysis_with_anomalies, analysis_repo, anomaly_repo):
        """Test that updating an analysis doesn't affect its anomalies"""
        analysis_id = analysis_with_anomalies.id

        # Verify anomalies exist
        anomalies_before = anomaly_repo.get_by_analysis(analysis_id)
        assert len(anomalies_before) == 5

        # Update the analysis
        analysis_repo.update(analysis_id, name="Updated_Name", description="Updated")

        # Verify anomalies still exist
        anomalies_after = anomaly_repo.get_by_analysis(analysis_id)
        assert len(anomalies_after) == 5
        assert all(a.analysis_id == analysis_id for a in anomalies_after)


class TestAnalysisCascadeDelete:
    """Tests for cascade delete behavior through the chain"""

    def test_delete_dataset_cascades_to_analyses(self, sample_dataset, dataset_repo, analysis_repo):
        """Test that deleting a dataset also deletes all its analyses"""
        # Create multiple analyses
        for i in range(3):
            analysis_repo.create(
                dataset_id=sample_dataset.id,
                model="Model",
                name=f"Analysis_{i}",
            )

        # Verify analyses exist
        analyses_before = analysis_repo.get_by_dataset(sample_dataset.id)
        assert len(analyses_before) == 3

        # Delete the dataset
        dataset_repo.delete(sample_dataset.id)

        # Verify analyses are deleted
        analyses_after = analysis_repo.get_by_dataset(sample_dataset.id)
        assert len(analyses_after) == 0

    def test_delete_dataset_cascades_to_anomalies(self, sample_dataset, dataset_repo, analysis_repo, anomaly_repo):
        """Test that deleting a dataset cascades through analysis to anomalies"""
        base_time = datetime(2024, 1, 1, 0, 0, 0)

        # Create analysis
        analysis = analysis_repo.create(
            dataset_id=sample_dataset.id,
            model="IsolationForest",
            name="Test_Analysis",
        )

        # Create anomalies
        anomaly_repo.bulk_create(
            [
                {
                    "analysis_id": analysis.id,
                    "start": base_time + timedelta(hours=i),
                    "end": base_time + timedelta(hours=i + 1),
                    "type": AnomalyType.point,
                }
                for i in range(5)
            ]
        )

        # Verify everything exists
        assert analysis_repo.get_by_id(analysis.id) is not None
        assert len(anomaly_repo.get_by_analysis(analysis.id)) == 5

        # Delete the dataset
        dataset_repo.delete(sample_dataset.id)

        # Verify everything is deleted
        assert analysis_repo.get_by_id(analysis.id) is None
        assert len(anomaly_repo.get_by_analysis(analysis.id)) == 0


class TestAnalysisEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_analysis_with_empty_string_description(self, sample_dataset, analysis_repo):
        """Test creating an analysis with empty string description"""
        analysis = analysis_repo.create(
            dataset_id=sample_dataset.id,
            model="Model",
            name="Analysis",
            description="",
        )

        assert analysis.description == ""

    def test_analysis_with_long_names(self, sample_dataset, analysis_repo):
        """Test creating analyses with long names (within limit)"""
        long_name = "A" * 255  # Max length
        analysis = analysis_repo.create(
            dataset_id=sample_dataset.id,
            model="M" * 255,
            name=long_name,
        )

        assert len(analysis.name) == 255
        assert len(analysis.model) == 255

    def test_analysis_same_name_same_dataset(self, sample_dataset, analysis_repo):
        """Test that multiple analyses can have the same name on the same dataset"""
        analysis1 = analysis_repo.create(
            dataset_id=sample_dataset.id,
            model="Model_A",
            name="Same_Name",
        )
        analysis2 = analysis_repo.create(
            dataset_id=sample_dataset.id,
            model="Model_B",
            name="Same_Name",
        )

        assert analysis1.id != analysis2.id
        assert analysis1.name == analysis2.name
        assert analysis1.dataset_id == analysis2.dataset_id

    def test_multiple_datasets_with_same_analysis_names(self, dataset_repo, analysis_repo):
        """Test that different datasets can have analyses with the same name"""
        dataset1 = dataset_repo.create(
            name=f"Dataset_1_{datetime.now().timestamp()}",
        )
        dataset2 = dataset_repo.create(
            name=f"Dataset_2_{datetime.now().timestamp()}",
        )

        analysis1 = analysis_repo.create(
            dataset_id=dataset1.id,
            model="IsolationForest",
            name="Standard_Analysis",
        )
        analysis2 = analysis_repo.create(
            dataset_id=dataset2.id,
            model="LSTM_Autoencoder",
            name="Standard_Analysis",
        )

        assert analysis1.id != analysis2.id
        assert analysis1.name == analysis2.name
        assert analysis1.dataset_id != analysis2.dataset_id


class TestSMAPWorkflows:
    """Tests for typical SMAP data workflows"""

    def test_smap_iterative_refinement_workflow(self, dataset_with_datapoints, analysis_repo):
        """Test a typical workflow of iterative model refinement"""
        # First pass - conservative
        analysis1 = analysis_repo.create(
            dataset_id=dataset_with_datapoints.id,
            model="IsolationForest",
            name="IF_conservative",
            description="contamination=0.05, n_estimators=100",
        )

        # Second pass - standard
        analysis2 = analysis_repo.create(
            dataset_id=dataset_with_datapoints.id,
            model="IsolationForest",
            name="IF_standard",
            description="contamination=0.1, n_estimators=100",
        )

        # Third pass - aggressive
        analysis3 = analysis_repo.create(
            dataset_id=dataset_with_datapoints.id,
            model="IsolationForest",
            name="IF_aggressive",
            description="contamination=0.15, n_estimators=100",
        )

        # Verify all created
        all_analyses = analysis_repo.get_by_dataset(dataset_with_datapoints.id)
        assert len(all_analyses) == 3

        # Verify ordering
        assert all_analyses[0].id == analysis1.id
        assert all_analyses[1].id == analysis2.id
        assert all_analyses[2].id == analysis3.id

    def test_smap_multi_model_comparison(self, dataset_with_datapoints, analysis_repo, anomaly_repo):
        """Test comparing different models on the same SMAP dataset"""
        base_time = datetime(2024, 1, 1, 0, 0, 0)

        models = ["IsolationForest", "LSTM_Autoencoder", "Statistical_ZScore"]
        analyses = []

        for model in models:
            analysis = analysis_repo.create(
                dataset_id=dataset_with_datapoints.id,
                model=model,
                name=f"{model}_SMAP_Run",
                description=f"Standard {model} configuration",
            )
            analyses.append(analysis)

            # Add some anomalies
            anomaly_repo.bulk_create(
                [
                    {
                        "analysis_id": analysis.id,
                        "start": base_time + timedelta(minutes=10 * i),
                        "end": base_time + timedelta(minutes=10 * i + 5),
                        "type": AnomalyType.point,
                    }
                    for i in range(3)
                ]
            )

        # Verify all analyses created
        all_analyses = analysis_repo.get_by_dataset(dataset_with_datapoints.id)
        assert len(all_analyses) == 3

        # Verify each has anomalies
        for analysis in analyses:
            anomalies = anomaly_repo.get_by_analysis(analysis.id)
            assert len(anomalies) == 3

    def test_smap_cleanup_old_analyses(self, sample_dataset, analysis_repo):
        """Test cleaning up old analyses (keeping only recent ones)"""
        # Create 5 analyses
        created = []
        for i in range(5):
            analysis = analysis_repo.create(
                dataset_id=sample_dataset.id,
                model="IsolationForest",
                name=f"Analysis_{i}",
            )
            created.append(analysis)

        # Keep only the last 3, delete the first 2
        for analysis in created[:2]:
            analysis_repo.delete(analysis.id)

        # Verify only 3 remain
        remaining = analysis_repo.get_by_dataset(sample_dataset.id)
        assert len(remaining) == 3
        assert set(a.id for a in remaining) == set(a.id for a in created[2:])
