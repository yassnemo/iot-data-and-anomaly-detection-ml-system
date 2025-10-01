"""
Pytest configuration
"""
import pytest


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests"
    )


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "integration: mark test as integration test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers"""
    if config.getoption("--integration"):
        # Run integration tests
        return
    
    # Skip integration tests by default
    skip_integration = pytest.mark.skip(reason="need --integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
