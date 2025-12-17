import pytest

# Import the module (so we can monkeypatch its functions)
import time_series.forecasting as forecasting

TEST_DATA = [
    0.143,
    0.663,
    0.256,
    0.155,
    0.199,
    0.125,
    0.165,
    0.14,
    0.148,
    0.154,
    0.137,
    0.493,
    0.354,
    0.228,
    0.195,
    0.527,
    0.886,
    0.198,
    0.243,
    0.193,
    0.342,
    0.27,
    0.325,
    0.269,
    0.143,
    0.663,
    0.256,
    0.155,
    0.199,
    0.125,
    0.165,
    0.14,
    0.148,
    0.154,
    0.137,
    0.493,
    0.354,
    0.228,
    0.195,
    0.527,
    0.886,
    0.198,
    0.243,
    0.193,
    0.342,
    0.27,
    0.325,
    0.269,
    0.143,
    0.663,
    0.256,
    0.155,
    0.199,
    0.125,
    0.165,
    0.14,
    0.148,
    0.154,
    0.137,
    0.493,
    0.354,
    0.228,
    0.195,
    0.527,
    0.886,
    0.198,
    0.243,
    0.193,
    0.342,
    0.27,
    0.325,
    0.269,
]


def test_predict_raises_if_too_short():
    with pytest.raises(ValueError, match=r"Expected 24"):
        forecasting.predict(TEST_DATA[:-1], city="Aalborg")


def test_predict_return_type():
    result = forecasting.predict(TEST_DATA, city="Aalborg")
    assert type(result) is type(TEST_DATA)
    assert len(result) == 12
    for num in result:
        assert isinstance(num, (int, float))
