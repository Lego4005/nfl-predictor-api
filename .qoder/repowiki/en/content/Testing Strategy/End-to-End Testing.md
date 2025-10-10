# End-to-End Testing

<cite>
**Referenced Files in This Document**   
- [playwrightConfig.ts](file://tests/e2e/playwrightConfig.ts) - *Updated in recent commit*
- [e2e-tests.yml](file://tests/e2e/.github/workflows/e2e-tests.yml)
- [run_tests.py](file://tests/e2e/scripts/run_tests.py)
- [conftest.py](file://tests/e2e/conftest.py)
- [basic-page-test.spec.js](file://tests/e2e/basic-page-test.spec.js)
- [enhanced-game-cards.spec.js](file://tests/e2e/enhanced-game-cards.spec.js)
- [docker-compose.test.yml](file://tests/e2e/docker-compose.test.yml)
- [Dockerfile](file://Dockerfile)
- [expert-section-responsive.spec.ts](file://tests/expert-section-responsive.spec.ts) - *Added in recent commit*
- [desktop-regression.spec.ts](file://tests/desktop-regression.spec.ts) - *Added in recent commit*
- [mobile-features.spec.ts](file://tests/mobile-features.spec.ts) - *Added in recent commit*
- [VERIFICATION-REPORT.md](file://tests/VERIFICATION-REPORT.md) - *Updated in recent commit*
</cite>

## Update Summary
- Added comprehensive responsive testing for expert section across multiple viewports
- Integrated desktop regression testing to ensure layout integrity
- Enhanced mobile feature testing with hamburger menu and navigation drawer interactions
- Added visual verification through screenshot capture for responsive layouts
- Updated documentation to reflect new test suites and verification methodology

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)

## Introduction
The NFL Predictor API employs a comprehensive end-to-end testing strategy using Playwright to ensure reliability, performance, and user experience across all critical user journeys. This documentation details the testing framework setup, execution workflow, and coverage of key features including prediction fetching, expert analysis viewing, and live game monitoring. The E2E tests validate the full stack from UI components through API endpoints to database interactions, with special emphasis on real-time WebSocket updates, dynamic game card rendering, and responsive dashboard behavior. The testing infrastructure leverages Docker for environment consistency and GitHub Actions for CI/CD pipeline integration, ensuring reliable test execution across different environments.

## Project Structure
The end-to-end testing framework is organized within the `tests/e2e` directory, following a structured approach that separates configuration, test scripts, utilities, and reporting. The framework supports multiple execution environments and provides comprehensive reporting capabilities.

```mermaid
graph TD
A[tests/e2e] --> B[.github/workflows]
A --> C[config]
A --> D[scripts]
A --> E[utils]
A --> F[playwrightConfig.ts]
A --> G[conftest.py]
A --> H[docker-compose.test.yml]
B --> I[e2e-tests.yml]
D --> J[run_tests.py]
F --> K[Browser Configuration]
G --> L[Test Fixtures]
H --> M[Docker Test Environment]
```

**Diagram sources**
- [playwrightConfig.ts](file://tests/e2e/playwrightConfig.ts)
- [.github/workflows/e2e-tests.yml](file://tests/e2e/.github/workflows/e2e-tests.yml)
- [docker-compose.test.yml](file://tests/e2e/docker-compose.test.yml)

**Section sources**
- [playwrightConfig.ts](file://tests/e2e/playwrightConfig.ts)
- [.github/workflows/e2e-tests.yml](file://tests/e2e/.github/workflows/e2e-tests.yml)
- [docker-compose.test.yml](file://tests/e2e/docker-compose.test.yml)

## Core Components
The E2E testing framework consists of several core components that work together to provide comprehensive test coverage. These include the Playwright configuration, test runner script, shared fixtures, and test specifications that validate critical user journeys. The framework is designed to test the full stack from UI components to API endpoints and database interactions, with special focus on real-time features and responsive design.

**Section sources**
- [playwrightConfig.ts](file://tests/e2e/playwrightConfig.ts)
- [run_tests.py](file://tests/e2e/scripts/run_tests.py)
- [conftest.py](file://tests/e2e/conftest.py)

## Architecture Overview
The E2E testing architecture is designed to provide comprehensive coverage of the NFL Predictor API across multiple dimensions including functionality, performance, and user experience. The framework supports cross-browser and cross-device testing, with configurations for desktop, mobile, and tablet devices.

```mermaid
graph TB
subgraph "Test Execution Environment"
A[GitHub Actions CI/CD] --> B[Docker Containers]
B --> C[Test Database]
B --> D[Test Redis]
B --> E[NFL Predictor API]
B --> F[Mock External Services]
B --> G[E2E Test Runner]
end
subgraph "Testing Framework"
H[Playwright] --> I[Browser Automation]
I --> J[Chromium]
I --> K[Firefox]
I --> L[WebKit]
H --> M[Test Runner]
M --> N[Pytest]
N --> O[Test Scripts]
end
subgraph "Reporting"
P[Test Results] --> Q[HTML Report]
P --> R[JUnit XML]
P --> S[JSON]
P --> T[Video Recordings]
P --> U[Screenshots]
end
G --> H
O --> P
```

**Diagram sources**
- [.github/workflows/e2e-tests.yml](file://tests/e2e/.github/workflows/e2e-tests.yml)
- [docker-compose.test.yml](file://tests/e2e/docker-compose.test.yml)
- [playwrightConfig.ts](file://tests/e2e/playwrightConfig.ts)

## Detailed Component Analysis

### Playwright Configuration
The Playwright configuration file defines the test environment settings, browser configurations, and reporting options for the E2E tests. It supports multiple projects for different device types and testing scenarios.

```mermaid
classDiagram
class PlaywrightConfig {
+string baseURL
+string wsURL
+string apiURL
+int testTimeout
+int navigationTimeout
+int actionTimeout
+int retries
+int workers
+string video
+string screenshot
+string trace
}
class ProjectConfig {
+string name
+Device device
+Viewport viewport
+string[] testMatch
}
class Device {
+string userAgent
+int deviceScaleFactor
+bool isMobile
+bool hasTouch
}
class Viewport {
+int width
+int height
}
class Reporter {
+string type
+object config
}
PlaywrightConfig --> ProjectConfig : "has"
ProjectConfig --> Device : "uses"
ProjectConfig --> Viewport : "uses"
PlaywrightConfig --> Reporter : "has"
```

**Diagram sources**
- [playwrightConfig.ts](file://tests/e2e/playwrightConfig.ts)

**Section sources**
- [playwrightConfig.ts](file://tests/e2e/playwrightConfig.ts)

### Test Runner Script
The test runner script provides a command-line interface for executing E2E tests with various configurations and reporting options. It supports different execution modes, parallel execution, and comprehensive reporting.

```mermaid
flowchart TD
Start([Start Test Runner]) --> ParseArgs["Parse Command Line Arguments"]
ParseArgs --> SetupEnv["Setup Test Environment"]
SetupEnv --> BuildCmd["Build Pytest Command"]
BuildCmd --> SetEnv["Set Environment Variables"]
SetEnv --> Execute["Execute Tests"]
Execute --> GenerateReport["Generate Reports"]
GenerateReport --> End([End])
BuildCmd --> Performance{"Performance Test?"}
Performance --> |Yes| AddPerformance["Add Performance Markers"]
Performance --> |No| Continue
SetEnv --> Headed{"Headed Mode?"}
Headed --> |Yes| SetHeadless["Set TEST_HEADLESS=false"]
Headed --> |No| Continue2
GenerateReport --> SaveSummary["Save Test Summary"]
SaveSummary --> GeneratePerf["Generate Performance Summary"]
```

**Diagram sources**
- [run_tests.py](file://tests/e2e/scripts/run_tests.py)

**Section sources**
- [run_tests.py](file://tests/e2e/scripts/run_tests.py)

### Test Fixtures and Configuration
The test fixtures provide shared setup and teardown functionality for E2E tests, including test server startup, browser initialization, and database setup. These fixtures ensure consistent test execution across different test files.

```mermaid
sequenceDiagram
participant Test as Test Runner
participant Fixture as conftest.py
participant Server as Test Server
participant Browser as Browser
participant DB as Test Database
Test->>Fixture : Request test_server fixture
Fixture->>Server : Start Uvicorn server
Server-->>Fixture : Server started
Fixture-->>Test : Server ready
Test->>Fixture : Request browser fixture
Fixture->>Browser : Launch Chromium
Browser-->>Fixture : Browser instance
Fixture-->Browser : Set default timeout
Fixture-->>Test : Browser ready
Test->>Fixture : Request test_database fixture
Fixture->>DB : Run migrations
DB-->>Fixture : Migrations complete
Fixture-->>Test : Database ready
Test->>Browser : Execute test steps
Browser->>Server : Make requests
Server->>DB : Query data
DB-->>Server : Return data
Server-->>Browser : Return response
Browser-->>Test : Complete test
```

**Diagram sources**
- [conftest.py](file://tests/e2e/conftest.py)

**Section sources**
- [conftest.py](file://tests/e2e/conftest.py)

### Test Specification Examples
The test specifications validate critical user journeys such as fetching predictions, viewing expert analysis, and monitoring live games. These tests cover both functional and non-functional requirements.

```mermaid
flowchart TD
A[Basic Page Test] --> B[Load Dashboard]
B --> C[Wait for React Root]
C --> D[Take Screenshot]
D --> E[Check Game Elements]
E --> F[Verify Title]
G[Enhanced Game Cards Test] --> H[Load Dashboard]
H --> I[Wait for Game Cards]
I --> J[Check Live Games]
J --> K[Verify Game State Content]
K --> L[Test Animations]
L --> M[Check Red Zone Alerts]
M --> N[Verify Weather Info]
N --> O[Test Grid Sizing]
O --> P[Check Betting Lines]
P --> Q[Verify Team Records]
Q --> R[Test Expand/Collapse]
```

**Diagram sources**
- [basic-page-test.spec.js](file://tests/e2e/basic-page-test.spec.js)
- [enhanced-game-cards.spec.js](file://tests/e2e/enhanced-game-cards.spec.js)

**Section sources**
- [basic-page-test.spec.js](file://tests/e2e/basic-page-test.spec.js)
- [enhanced-game-cards.spec.js](file://tests/e2e/enhanced-game-cards.spec.js)

### Responsive Testing Suite
The responsive testing suite validates the AI Experts section across multiple viewports, ensuring proper layout behavior on both desktop and mobile devices. The tests verify grid layout on desktop and horizontal scroll with snap behavior on mobile.

```mermaid
flowchart TD
A[Responsive Tests] --> B[Desktop Layout]
A --> C[Mobile Layout]
A --> D[Regression Verification]
B --> B1[1920x1080 Grid]
B --> B2[1440x900 Grid]
B --> B3[1024x768 Grid]
C --> C1[390x844 Scroll]
C --> C2[375x667 Scroll]
C --> C3[Touch Scroll]
D --> D1[Layout Integrity]
D --> D2[Visual Verification]
D --> D3[Screenshot Comparison]
```

**Diagram sources**
- [expert-section-responsive.spec.ts](file://tests/expert-section-responsive.spec.ts)
- [desktop-regression.spec.ts](file://tests/desktop-regression.spec.ts)
- [mobile-features.spec.ts](file://tests/mobile-features.spec.ts)

**Section sources**
- [expert-section-responsive.spec.ts](file://tests/expert-section-responsive.spec.ts) - *Added in recent commit*
- [desktop-regression.spec.ts](file://tests/desktop-regression.spec.ts) - *Added in recent commit*
- [mobile-features.spec.ts](file://tests/mobile-features.spec.ts) - *Added in recent commit*
- [VERIFICATION-REPORT.md](file://tests/VERIFICATION-REPORT.md) - *Updated in recent commit*

## Dependency Analysis
The E2E testing framework has dependencies on various components and services that must be properly configured for successful test execution. These include the test database, Redis cache, API server, and external service mocks.

```mermaid
graph TD
A[E2E Test Runner] --> B[Test Database]
A --> C[Test Redis]
A --> D[NFL Predictor API]
A --> E[Mock Sportsbook API]
A --> F[Mock Weather API]
D --> G[Production Database]
D --> H[Production Redis]
D --> I[External APIs]
E --> J[Sportsbook Data]
F --> K[Weather Data]
B --> M[PostgreSQL]
C --> N[Redis]
G --> M
H --> N
```

**Diagram sources**
- [docker-compose.test.yml](file://tests/e2e/docker-compose.test.yml)

**Section sources**
- [docker-compose.test.yml](file://tests/e2e/docker-compose.test.yml)

## Performance Considerations
The E2E testing framework includes performance testing configurations and options to ensure the NFL Predictor API meets performance requirements under various conditions. The framework supports performance testing with disabled images and CSS to measure core performance.

```mermaid
graph TD
A[Performance Testing] --> B[Desktop Chrome]
A --> C[Disabled Images]
A --> D[Disabled CSS]
A --> E[No Sandbox]
A --> F[Disabled GPU]
A --> G[Headless Mode]
H[Test Types] --> I[Smoke Tests]
H --> J[Integration Tests]
H --> K[Performance Tests]
L[Reporting] --> M[HTML Report]
L --> N[JUnit XML]
L --> O[JSON]
L --> P[Benchmark JSON]
I --> Q[Minimal Test Coverage]
J --> R[Comprehensive Test Coverage]
K --> S[Performance Metrics]
```

**Diagram sources**
- [playwrightConfig.ts](file://tests/e2e/playwrightConfig.ts)
- [run_tests.py](file://tests/e2e/scripts/run_tests.py)

**Section sources**
- [playwrightConfig.ts](file://tests/e2e/playwrightConfig.ts)
- [run_tests.py](file://tests/e2e/scripts/run_tests.py)

## Troubleshooting Guide
The E2E testing framework includes several features to aid in troubleshooting test failures, including screenshot capture, video recording, and detailed logging. These features help identify and resolve issues quickly.

```mermaid
flowchart TD
A[Test Failure] --> B[Capture Screenshot]
B --> C[Save to test-results/screenshots]
A --> D[Record Video]
D --> E[Save to test-results/videos]
A --> F[Collect Trace]
F --> G[Save to test-results/trace]
A --> H[Log Console Errors]
H --> I[Save to test-results/logs]
A --> J[Generate HTML Report]
J --> K[Include Failure Details]
A --> L[Generate JUnit XML]
L --> M[Include Failure Details]
```

**Diagram sources**
- [playwrightConfig.ts](file://tests/e2e/playwrightConfig.ts)
- [conftest.py](file://tests/e2e/conftest.py)

**Section sources**
- [playwrightConfig.ts](file://tests/e2e/playwrightConfig.ts)
- [conftest.py](file://tests/e2e/conftest.py)

## Conclusion
The end-to-end testing framework for the NFL Predictor API provides comprehensive coverage of critical user journeys and system functionality. By leveraging Playwright for browser automation, Docker for environment consistency, and GitHub Actions for CI/CD integration, the framework ensures reliable test execution across different environments. The testing strategy validates the full stack from UI components through API endpoints to database interactions, with special emphasis on real-time features and responsive design. The framework's comprehensive reporting and troubleshooting capabilities enable rapid identification and resolution of issues, ensuring high-quality releases.