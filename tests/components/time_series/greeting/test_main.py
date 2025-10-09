from time_series.greeting import main


def test_hello_world():
    assert main.hello_world() == "Hello world!"
