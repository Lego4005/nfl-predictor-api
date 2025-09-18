"""
Pytest configuration and shared fixtures for E2E tests
"""
import os
import asyncio
import pytest
import uvicorn
import threading
import time
from typing import Generator, AsyncGenerator
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from httpx import AsyncClient
import logging
from pathlib import Path

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_CONFIG = {
    "BASE_URL": os.getenv("TEST_BASE_URL", "http://localhost:8001"),
    "WS_URL": os.getenv("TEST_WS_URL", "ws://localhost:8001"),
    "BROWSER": os.getenv("TEST_BROWSER", "chromium"),
    "HEADLESS": os.getenv("TEST_HEADLESS", "true").lower() == "true",
    "SLOW_MO": int(os.getenv("TEST_SLOW_MO", "0")),
    "TIMEOUT": int(os.getenv("TEST_TIMEOUT", "30000")),
    "DATABASE_URL": os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost:5432/nfl_predictor_test"),
    "REDIS_URL": os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")
}


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_server():
    """Start test server instance"""
    from src.api.app import app

    # Configure test server
    config = uvicorn.Config(
        app,
        host="localhost",
        port=8001,
        log_level="error",
        access_log=False
    )
    server = uvicorn.Server(config)

    # Start server in thread
    def run_server():
        asyncio.run(server.serve())

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    import httpx
    max_retries = 30
    for i in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{TEST_CONFIG['BASE_URL']}/health")
                if response.status_code == 200:
                    logger.info("✅ Test server started successfully")
                    break
        except Exception:
            if i == max_retries - 1:
                raise Exception("Failed to start test server")
            await asyncio.sleep(1)

    yield server

    # Cleanup would go here if needed


@pytest.fixture(scope="session")
async def browser():
    """Create browser instance"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=TEST_CONFIG["HEADLESS"],
            slow_mo=TEST_CONFIG["SLOW_MO"]
        )
        yield browser
        await browser.close()


@pytest.fixture(scope="function")
async def browser_context(browser: Browser) -> AsyncGenerator[BrowserContext, None]:
    """Create browser context with default settings"""
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="NFL-Predictor-E2E-Test/1.0",
        extra_http_headers={
            "X-Test-Mode": "true"
        }
    )

    # Set default timeout
    context.set_default_timeout(TEST_CONFIG["TIMEOUT"])

    yield context
    await context.close()


@pytest.fixture(scope="function")
async def page(browser_context: BrowserContext) -> AsyncGenerator[Page, None]:
    """Create a new page"""
    page = await browser_context.new_page()

    # Add console logging for debugging
    page.on("console", lambda msg: logger.info(f"Console: {msg.text}"))
    page.on("pageerror", lambda error: logger.error(f"Page error: {error}"))

    yield page
    await page.close()


@pytest.fixture(scope="function")
async def api_client(test_server) -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client for API testing"""
    async with AsyncClient(base_url=TEST_CONFIG["BASE_URL"]) as client:
        yield client


@pytest.fixture(scope="session")
def test_database():
    """Setup test database"""
    from database import run_migrations

    # Set test database URL
    os.environ["DATABASE_URL"] = TEST_CONFIG["DATABASE_URL"]

    try:
        # Run migrations for test database
        run_migrations()
        logger.info("✅ Test database initialized")
        yield TEST_CONFIG["DATABASE_URL"]
    except Exception as e:
        logger.warning(f"⚠️ Database setup failed: {e}")
        # Continue with tests even if database setup fails
        yield None


@pytest.fixture(autouse=True)
async def cleanup_between_tests():
    """Cleanup between tests"""
    yield
    # Add any cleanup logic here
    pass


def pytest_configure(config):
    """Pytest configuration"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers based on test file paths
    for item in items:
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.performance)
        elif "user_journey" in item.nodeid:
            item.add_marker(pytest.mark.smoke)


@pytest.fixture
def screenshot_on_failure(request, page: Page):
    """Take screenshot on test failure"""
    yield
    if request.node.rep_call.failed:
        screenshot_dir = Path("test-results/screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = screenshot_dir / f"{request.node.name}.png"
        page.screenshot(path=str(screenshot_path))
        logger.info(f"📸 Screenshot saved: {screenshot_path}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results for screenshot on failure"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)