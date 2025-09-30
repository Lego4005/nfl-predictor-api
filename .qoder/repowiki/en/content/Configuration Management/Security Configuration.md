# Security Configuration

<cite>
**Referenced Files in This Document**   
- [key_rotation.py](file://config/key_rotation.py)
- [production.py](file://config/production.py)
- [redis_config.py](file://config/redis_config.py)
</cite>

## Table of Contents
1. [Key Rotation System](#key-rotation-system)
2. [Production Security Settings](#production-security-settings)
3. [Secrets Management](#secrets-management)
4. [Compliance and Audit Logging](#compliance-and-audit-logging)
5. [Troubleshooting Authentication Issues](#troubleshooting-authentication-issues)

## Key Rotation System

The NFL Predictor API implements a comprehensive key rotation system in `key_rotation.py` to securely manage API credentials, database passwords, and third-party service tokens. The system uses a secure storage mechanism that stores only hashed versions of API keys, preventing exposure of sensitive credentials in configuration files.

The KeyRotationManager class provides a complete lifecycle management system for API keys with four distinct statuses: ACTIVE, ROTATING, DEPRECATED, and REVOKED. When rotating keys, the system implements a grace period where both old and new keys remain valid, ensuring uninterrupted service during the transition. The rotation process automatically marks current active keys as ROTATING with an expiration time before adding the new key as ACTIVE.

Key retrieval is handled through the `get_active_key()` method, which validates that the key in the environment variables matches the stored hash before returning it. This prevents unauthorized key changes from being used by the application. The system also tracks key usage statistics including last used timestamp and usage count, providing valuable insights for security monitoring.

The key rotation system includes automated cleanup of expired keys through the `cleanup_expired_keys()` method, which removes keys that are in ROTATING or DEPRECATED status and have passed their expiration date. This ensures that old keys do not accumulate in the system over time.

**Section sources**
- [key_rotation.py](file://config/key_rotation.py#L67-L363)
- [key_rotation.py](file://config/key_rotation.py#L210-L238)
- [key_rotation.py](file://config/key_rotation.py#L251-L270)

## Production Security Settings

The production security configuration in `production.py` implements multiple layers of protection for the NFL Predictor API. The SecurityConfig class manages critical security settings including CORS origins, allowed hosts, and the API base URL. In production environments, the system enforces HTTPS for the API base URL and prohibits wildcard CORS origins to prevent security vulnerabilities.

The configuration system validates security settings during initialization, raising errors if production requirements are not met. This validation ensures that sensitive endpoints cannot be exposed through misconfiguration. The system also validates Redis URL format, requiring URLs to start with redis:// or rediss:// to prevent connection to insecure endpoints.

Rate limiting thresholds are configured through the RateLimitConfig class, with different limits for various API services. The current configuration sets 500 requests per hour for the odds API, 1,000 for SportsData.io, 1,000 for ESPN API, 500 for NFL API, and 100 for Rapid API. These limits help prevent abuse and ensure fair usage of third-party services.

JWT expiration is managed through the API_SECRET_KEY environment variable, which is used for token signing. While the exact expiration time is not specified in the configuration files, the system is designed to use short-lived tokens for enhanced security. The configuration also includes monitoring settings with configurable log levels and health check intervals.

**Section sources**
- [production.py](file://config/production.py#L126-L217)
- [production.py](file://config/production.py#L194-L217)
- [production.py](file://config/production.py#L227-L267)

## Secrets Management

The NFL Predictor API follows industry best practices for handling sensitive data across different environments. All credentials are stored in environment variables rather than configuration files, with the production configuration loading API keys from environment variables such as ODDS_API_KEY, SPORTSDATA_IO_KEY, RAPID_API_KEY, and API_SECRET_KEY.

For local development, the system can use default values, but in production, the absence of required API keys triggers validation errors. This ensures that production deployments cannot run without proper credentials. The key rotation system enhances this security by storing only hashed versions of keys in the keys.json file, with the actual keys remaining in environment variables.

The system implements encrypted storage for production keys through file permission controls. When saving the keys.json file, the system sets secure permissions (0o600) to ensure only the owner can read or write the file. This prevents unauthorized access to the key metadata even if an attacker gains access to the file system.

Secure configuration patterns are enforced through validation rules that check for proper Redis URL formatting and HTTPS usage in production. The system also supports optional services like Rapid API, allowing for flexible deployment scenarios while maintaining security for required services.

**Section sources**
- [production.py](file://config/production.py#L146-L153)
- [key_rotation.py](file://config/key_rotation.py#L106-L127)
- [production.py](file://config/production.py#L269-L294)

## Compliance and Audit Logging

The security configuration system includes several features to support compliance requirements and protect against common vulnerabilities. The key rotation system provides audit capabilities through detailed logging of key operations including additions, rotations, and revocations. Each key operation is logged with timestamps and key identifiers, creating an audit trail for security reviews.

The system protects against information disclosure vulnerabilities by validating configuration settings in production environments. It specifically checks for the use of wildcard CORS origins and HTTP URLs, both of which could expose the API to security risks. The validation process prevents the application from starting with insecure configurations.

Rate limiting helps prevent denial-of-service attacks and protects third-party API quotas. The system tracks rate limit information for active keys through the update_rate_limit_info() method, allowing the application to respond appropriately when limits are approaching. This proactive monitoring helps maintain service availability and prevents unexpected API disruptions.

The configuration system also includes mechanisms to detect and report potential security issues. The validate_key_configuration() method returns detailed information about configuration problems, including errors for missing required keys, warnings for multiple active keys, and notifications about keys approaching expiration. This comprehensive validation helps maintain a secure configuration state.

**Section sources**
- [key_rotation.py](file://config/key_rotation.py#L330-L363)
- [production.py](file://config/production.py#L194-L217)
- [key_rotation.py](file://config/key_rotation.py#L290-L323)

## Troubleshooting Authentication Issues

Authentication failures related to security configuration can be diagnosed using several built-in tools and methods. The first step is to verify that required environment variables are properly set, particularly ODDS_API_KEY and SPORTSDATA_IO_KEY, which are required for production operation. Missing or incorrect environment variables are the most common cause of authentication failures.

When key rotation is involved, check for hash mismatches between the stored key hash and the environment variable value. The system logs warnings when such mismatches occur, indicating that the key in the environment has been changed without updating the key rotation system. This can happen when keys are updated manually without using the rotation API.

For rate limiting issues, verify that the application is not exceeding the configured limits for third-party APIs. The get_key_status() method provides information about remaining rate limit counts, which can help determine if rate limiting is the cause of authentication failures. Temporary issues may resolve themselves as rate limit counters reset.

Configuration validation errors will prevent the application from starting in production mode. Check the application logs for validation error messages, which will specify exactly which security requirements are not being met. Common issues include using HTTP instead of HTTPS for the API base URL or using wildcard CORS origins in production.

The system provides several diagnostic methods to help troubleshoot issues. The get_all_services_status() method returns the status of all configured services, while the validate_key_configuration() method identifies specific configuration problems. These tools can quickly pinpoint the source of authentication and authorization issues.

**Section sources**
- [key_rotation.py](file://config/key_rotation.py#L162-L208)
- [production.py](file://config/production.py#L194-L217)
- [key_rotation.py](file://config/key_rotation.py#L325-L328)