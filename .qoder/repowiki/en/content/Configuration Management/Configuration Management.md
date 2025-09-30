# Configuration Management

<cite>
**Referenced Files in This Document**   
- [production.py](file://config/production.py)
- [database_optimization.py](file://config/database_optimization.py)
- [key_rotation.py](file://config/key_rotation.py)
- [redis_config.py](file://config/redis_config.py)
- [production_deployment.py](file://config/production_deployment.py)
- [docker-compose.prod.yml](file://docker-compose.prod.yml)
- [nginx.conf](file://nginx.conf)
- [alert_rules.yml](file://src/monitoring/config/alert_rules.yml)
- [prometheus.yml](file://src/monitoring/config/prometheus.yml)
</cite>

## Table of Contents
1. [Environment-Specific Configuration](#environment-specific-configuration)
2. [Production Configuration](#production-configuration)
3. [Database Optimization Settings](#database-optimization-settings)
4. [Key Rotation System](#key-rotation-system)
5. [Supabase Configuration](#supabase-configuration)
6. [Configuration Overrides and Environment Variables](#configuration-overrides-and-environment-variables)
7. [Best Practices for Configuration Management](#best-practices-for-configuration-management)

## Environment-Specific Configuration

The NFL Predictor API implements a comprehensive environment-specific configuration system that supports distinct settings for production, development, and testing environments. The configuration system is built around environment variables and Python configuration classes that adapt behavior based on the current environment. The core configuration is managed through the `ProductionConfig` class in `production.py`, which determines the environment type through the `ENVIRONMENT` environment variable with values of "development", "staging", or "production". Each environment has specific defaults and validation rules that ensure appropriate settings for the context. Development environments allow more permissive settings like debug mode and broader CORS origins, while production environments enforce strict security requirements including HTTPS for the API base URL and restricted CORS policies. The configuration system validates settings at initialization, preventing the application from starting with invalid configurations that could compromise security or performance.

**Section sources**
- [production.py](file://config/production.py#L1-L310)

## Production Configuration

The production configuration for the NFL Predictor API includes comprehensive security settings, performance parameters, and deployment-specific options designed to ensure reliability, security, and optimal performance. Security settings enforce HTTPS for the API base URL and restrict CORS origins to prevent wildcard usage in production, mitigating cross-site request forgery risks. The configuration validates that essential API keys are present and properly configured, with specific validation for primary data sources like the Odds API and SportsData IO. Performance parameters include configurable rate limits for various API sources, with default limits of 500 requests per window for the Odds API and 1,000 for SportsData IO. Monitoring is enabled by default with configurable log levels and health check intervals. The configuration also manages cache settings through Redis, specifying the Redis URL, password, database number, TTL for cached items, and maximum memory allocation. These settings are validated at startup to ensure production requirements are met before the application becomes available.

**Section sources**
- [production.py](file://config/production.py#L126-L294)

## Database Optimization Settings

The database optimization configuration provides comprehensive settings for tuning query performance and connection pooling in the NFL Predictor API. The `DatabaseOptimizer` class manages connection pooling with configurable minimum and maximum pool sizes, with production defaults of 10 and 50 connections respectively. Query optimization is achieved through statement caching with a configurable cache size (default 2048) and prepared statement caching. The system implements query timeout settings (default 60 seconds) and tracks query performance metrics including execution time, row counts, and frequency. Connection-level optimizations include statement timeout, lock timeout, and idle transaction session timeout settings that prevent long-running queries from impacting system performance. The optimizer automatically creates performance indexes on critical tables such as `enhanced_expert_models`, `expert_predictions_enhanced`, and `ai_council_selections`, with composite indexes on frequently queried columns. Monitoring features include slow query detection (threshold configurable at 2.0 seconds) and detailed query statistics that can be used to generate performance reports. The system also supports automated database maintenance operations like ANALYZE, VACUUM, and REINDEX to maintain optimal database performance.

**Section sources**
- [database_optimization.py](file://config/database_optimization.py#L53-L346)
- [database_optimization.py](file://config/database_optimization.py#L350-L374)

## Key Rotation System

The NFL Predictor API implements a robust key rotation system for managing API credentials and security tokens through the `KeyRotationManager` class. This system provides secure storage, rotation, and validation of API keys for external services including the Odds API, SportsData IO, and Rapid API. Each API key is assigned a unique key ID and stored with a secure hash rather than the plaintext key, enhancing security. The system tracks key status through a lifecycle that includes ACTIVE, ROTATING, DEPRECATED, and REVOKED states, allowing for graceful transitions during rotation. When rotating keys, the system maintains both the current and new keys during a configurable grace period (default 24 hours), ensuring uninterrupted service during the transition. The manager validates key configuration and can detect issues such as missing required keys, multiple active keys for the same service, or keys approaching expiration. Rate limit information from external APIs is tracked and updated, allowing the system to adapt to usage patterns. The key manager also provides cleanup functionality to remove expired keys and maintains detailed logging of all key operations for audit purposes.

**Section sources**
- [key_rotation.py](file://config/key_rotation.py#L67-L363)

## Supabase Configuration

The NFL Predictor API integrates with Supabase for database management and authentication, with configuration settings that support both direct database connections and Supabase-specific features. The database optimization configuration includes dedicated fields for Supabase URL, anonymous key, service role key, and direct database URL, allowing flexible connection options. When only the Supabase URL is provided, the system automatically constructs the appropriate PostgreSQL connection string using the standard Supabase database format. The configuration supports environment variables for database credentials, enabling secure credential management without hardcoding values. Database operations are optimized for Supabase's PostgreSQL backend with connection parameters tuned for performance, including statement timeout, lock timeout, and idle transaction session timeout settings. The system creates specialized indexes on Supabase tables to optimize query performance for the application's access patterns, particularly on tables involved in expert competition, prediction analytics, and self-healing systems. Monitoring configurations include specific alert rules for database health, connection counts, and performance metrics that integrate with Supabase's observability features.

**Section sources**
- [database_optimization.py](file://config/database_optimization.py#L350-L374)
- [alert_rules.yml](file://src/monitoring/config/alert_rules.yml#L1-L264)

## Configuration Overrides and Environment Variables

The NFL Predictor API supports flexible configuration overrides through environment variables, allowing deployment-specific settings without code changes. The production configuration system loads settings from environment variables with sensible defaults, enabling easy customization across different deployment environments. For example, the Redis URL defaults to "redis://localhost:6379" but can be overridden with the `REDIS_URL` environment variable. Similarly, database connection pool size can be adjusted using `DB_MIN_POOL_SIZE` and `DB_MAX_POOL_SIZE` variables. The Docker Compose production configuration demonstrates this approach by passing environment variables to the application container, including `ENVIRONMENT=production` and `DEBUG=false`. The Nginx configuration uses environment variables for Redis password through the `${REDIS_PASSWORD}` syntax. The deployment system generates a `.env.production.template` file that lists all configurable environment variables with example values, serving as documentation for deployment configuration. This approach allows operators to customize the system for their specific infrastructure while maintaining consistent behavior across environments. The configuration validation ensures that required variables are present and properly formatted before the application starts.

**Section sources**
- [production.py](file://config/production.py#L126-L294)
- [production_deployment.py](file://config/production_deployment.py#L1-L631)
- [docker-compose.prod.yml](file://docker-compose.prod.yml#L1-L76)
- [nginx.conf](file://nginx.conf#L1-L110)

## Best Practices for Configuration Management

The NFL Predictor API follows several best practices for managing configuration data, version control, and deployment-specific configuration. Sensitive configuration data is never hardcoded in source files but is instead managed through environment variables and secure storage mechanisms. The key rotation system stores only hashed versions of API keys and uses environment variables for the actual key values, minimizing exposure. Configuration files are structured to separate environment-specific settings from code, with the production configuration validating security settings like HTTPS usage and restricted CORS origins. Version control strategies include template files like `.env.production.template` that provide documentation without exposing actual credentials. Deployment-specific configuration is managed through Docker Compose files and deployment scripts that orchestrate the application, Redis, and Nginx services with appropriate networking and volume mounts. The monitoring system implements comprehensive alerting through Prometheus and Alertmanager with rules covering API performance, ML accuracy, cache health, system resources, and database health. Configuration changes are validated at startup, preventing the application from running with invalid settings. The deployment script includes backup creation, health checks, and rollback procedures to ensure reliable updates. This comprehensive approach ensures that configuration management supports security, reliability, and maintainability across the application lifecycle.

**Section sources**
- [production.py](file://config/production.py#L126-L294)
- [production_deployment.py](file://config/production_deployment.py#L1-L631)
- [docker-compose.prod.yml](file://docker-compose.prod.yml#L1-L76)
- [nginx.conf](file://nginx.conf#L1-L110)
- [alert_rules.yml](file://src/monitoring/config/alert_rules.yml#L1-L264)
- [prometheus.yml](file://src/monitoring/config/prometheus.yml#L1-L59)