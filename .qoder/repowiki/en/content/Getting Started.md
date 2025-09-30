# Getting Started

<cite>
**Referenced Files in This Document**   
- [README.md](file://README.md)
- [SUPABASE_SETUP.md](file://SUPABASE_SETUP.md)
- [PRODUCTION_SETUP_GUIDE.md](file://PRODUCTION_SETUP_GUIDE.md)
- [Dockerfile](file://Dockerfile)
- [docker-compose.yml](file://docker-compose.yml)
- [docker-compose.prod.yml](file://docker-compose.prod.yml)
- [requirements.txt](file://requirements.txt)
- [requirements-ml.txt](file://requirements-ml.txt)
- [scripts/populate_database.py](file://scripts/populate_database.py)
- [scripts/fetch_2025_nfl_season.mjs](file://scripts/fetch_2025_nfl_season.mjs)
- [config/production_deployment.py](file://config/production_deployment.py)
- [.env.production.template](file://.env.production.template)
- [nginx.conf](file://nginx.conf)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Development Environment Setup](#development-environment-setup)
3. [Database Initialization with Supabase](#database-initialization-with-supabase)
4. [Data Population and Migration](#data-population-and-migration)
5. [Environment Configuration](#environment-configuration)
6. [Starting Application Services](#starting-application-services)
7. [Production Deployment Preparation](#production-deployment-preparation)
8. [Troubleshooting Common Issues](#troubleshooting-common-issues)
9. [Verification and Testing](#verification-and-testing)

## Introduction
This guide provides comprehensive instructions for onboarding new developers and users to the NFL Predictor API. It covers the complete setup process from environment configuration to production deployment. The system combines machine learning models, real-time data processing, and expert competition frameworks to deliver accurate NFL predictions. This document details all necessary steps to initialize the development environment, configure database services, populate historical data, and launch the application successfully.

## Development Environment Setup
To set up the local development environment for the NFL Predictor API, follow these step-by-step instructions:

1. **Clone the Repository**
```bash
git clone https://github.com/your-organization/nfl-predictor-api.git
cd nfl-predictor-api
```

2. **Install Python Dependencies**
The project requires Python 3.9+ and uses pip for package management:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install core dependencies
pip install -r requirements.txt

# Install machine learning specific dependencies
pip install -r requirements-ml.txt
```

3. **Install Node.js Dependencies**
The frontend components require Node.js 18.x or 20.x:
```bash
# Install Node.js dependencies
npm install

# Verify installation
npm run build
```

4. **Configure Docker**
Install Docker and Docker Compose if not already available:
```bash
# Test Docker installation
docker --version
docker-compose --version

# Build and run containers
docker-compose up --build
```

The Dockerfile defines a multi-stage build process that optimizes the production image by separating build and runtime dependencies. The application runs as a non-root user for security, with health checks configured to monitor service availability.

**Section sources**
- [Dockerfile](file://Dockerfile#L1-L64)
- [docker-compose.yml](file://docker-compose.yml#L1-L72)
- [requirements.txt](file://requirements.txt#L1-L26)
- [requirements-ml.txt](file://requirements-ml.txt#L1-L28)

## Database Initialization with Supabase
Initialize the Supabase database following these steps:

1. **Create Supabase Account**
- Visit <https://supabase.com> and sign up
- Create a new project named "nfl-predictor"
- Select the region closest to your primary users
- Save the database password securely

2. **Run Database Schema**
Access the SQL Editor in the Supabase dashboard and execute the following schema definitions in order:

- Core tables (games, predictions, odds_history)
- User tables (user_picks, user_stats)
- Analytics tables (news_sentiment, model_performance)

3. **Enable Row Level Security (RLS)**
Configure security policies for data access:
```sql
-- Enable RLS on all tables
ALTER TABLE games ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;

-- Create public read access policies
CREATE POLICY "Public read access" ON games FOR SELECT USING (true);
CREATE POLICY "Public read access" ON predictions FOR SELECT USING (true);
```

4. **Set Up Realtime Subscriptions**
Navigate to Database > Replication in the Supabase dashboard and enable realtime for:
- games table (live score updates)
- predictions table (new predictions)
- odds_history table (line movements)

5. **Get Connection Details**
From Settings > API, copy:
- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_SERVICE_KEY (keep this private)

**Section sources**
- [SUPABASE_SETUP.md](file://SUPABASE_SETUP.md#L1-L347)
- [supabase/config.toml](file://supabase/config.toml)

## Data Population and Migration
Populate the database with NFL schedule and historical data using the provided scripts:

1. **Run Database Migrations**
Execute the migration scripts to create and optimize database tables:
```bash
# Apply core migrations
supabase db push

# Run production optimization script
psql -f supabase/migrations/030_production_database_optimization.sql
```

2. **Fetch NFL Season Data**
Use the dedicated script to retrieve the current season schedule:
```bash
node scripts/fetch_2025_nfl_season.mjs
```

3. **Populate Database with Historical Data**
Run the population script to import historical NFL data:
```bash
python scripts/populate_database.py
```

4. **Apply Additional Schema Enhancements**
Execute supplementary SQL scripts for enhanced functionality:
```bash
# Add performance indexes
python scripts/add_performance_indexes.py

# Fix schema issues if needed
node scripts/fix_rls_and_migrate.js
```

5. **Verify Data Integrity**
Check that all data has been loaded correctly:
```bash
node scripts/check_games_count.mjs
python scripts/check_coverage.py
```

The data pipeline includes comprehensive validation checks to ensure data quality and consistency across all tables.

**Section sources**
- [scripts/populate_database.py](file://scripts/populate_database.py)
- [scripts/fetch_2025_nfl_season.mjs](file://scripts/fetch_2025_nfl_season.mjs)
- [scripts/add_performance_indexes.py](file://scripts/add_performance_indexes.py)
- [scripts/fix_rls_and_migrate.js](file://scripts/fix_rls_and_migrate.js)
- [supabase/migrations/](file://supabase/migrations/)

## Environment Configuration
Configure environment variables for API keys and service connections:

1. **Create Environment Files**
Copy the production template:
```bash
cp .env.production.template .env.production
```

2. **Set Required Environment Variables**
Update the .env.production file with your credentials:

```bash
# Database Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key
DATABASE_URL=postgresql://postgres:password@host:5432/postgres

# External API Keys
ODDS_API_KEY=your-odds-api-key
SPORTSDATA_IO_KEY=your-sportsdata-key
RAPID_API_KEY=your-rapid-api-key
ESPN_API_KEY=your-espn-api-key

# Cache Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=secure-password

# Security Settings
API_SECRET_KEY=your-jwt-secret
CORS_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com

# Performance Tuning
DB_MIN_POOL_SIZE=10
DB_MAX_POOL_SIZE=50
DB_QUERY_TIMEOUT=60
```

3. **Generate Production Configuration**
Use the configuration generator for deployment:
```bash
python config/production_deployment.py
```

4. **Validate Configuration**
Test the environment setup:
```bash
python scripts/validate_implementation.py
```

The system uses environment-specific configuration to separate development, staging, and production settings while maintaining consistent interface patterns.

**Section sources**
- [.env.production.template](file://.env.production.template)
- [config/production_deployment.py](file://config/production_deployment.py)
- [PRODUCTION_SETUP_GUIDE.md](file://PRODUCTION_SETUP_GUIDE.md#L1-L286)

## Starting Application Services
Launch the application services using Docker Compose:

1. **Start Development Environment**
```bash
# Start all services in development mode
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

2. **Start Production Environment**
```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d
```

3. **Verify Service Status**
Check that all containers are running:
```bash
docker-compose ps

# View logs
docker-compose logs -f
```

4. **Access Application Endpoints**
The services expose the following ports:
- API Server: Port 8000
- WebSocket Service: Port 8080
- Redis Cache: Port 6379
- Nginx Reverse Proxy: Ports 80/443

5. **Monitor Health Checks**
Verify service health through the health endpoint:
```bash
curl http://localhost:8000/health
```

The production stack includes Nginx for SSL termination, rate limiting, and static file serving, with Redis providing caching capabilities to reduce database load.

**Section sources**
- [docker-compose.yml](file://docker-compose.yml#L1-L72)
- [docker-compose.prod.yml](file://docker-compose.prod.yml#L1-L76)
- [nginx.conf](file://nginx.conf)
- [Dockerfile](file://Dockerfile#L1-L64)

## Production Deployment Preparation
Prepare the system for production deployment:

1. **Configure Production Settings**
Update the production environment file with actual values:
```bash
# Make deployment script executable
chmod +x deploy.sh

# Edit production configuration
nano .env.production
```

2. **Run Automated Deployment**
Execute the deployment script:
```bash
./deploy.sh
```

3. **Set Up Monitoring**
Configure monitoring and alerting:
```bash
# Start monitoring stack
docker-compose -f monitoring.yml up -d

# Access Grafana dashboard
# http://localhost:3000
```

4. **Enable Security Features**
Implement production security measures:
- Configure SSL/TLS certificates
- Set up firewall rules
- Enable HSTS and CSP headers
- Implement regular API key rotation

5. **Optimize Performance**
Apply database optimization settings:
```bash
# Run optimization script
python config/database_optimization.py
```

The production configuration includes connection pooling, query optimization, and automated maintenance tasks to ensure high availability and performance under load.

**Section sources**
- [deploy.sh](file://deploy.sh)
- [docker-compose.prod.yml](file://docker-compose.prod.yml#L1-L76)
- [PRODUCTION_SETUP_GUIDE.md](file://PRODUCTION_SETUP_GUIDE.md#L1-L286)
- [config/database_optimization.py](file://config/database_optimization.py)

## Troubleshooting Common Issues
Address common setup issues with these solutions:

### Database Connection Errors
**Symptoms**: "Connection refused" or "Invalid credentials"
**Solutions**:
- Verify SUPABASE_URL and keys are correct
- Check that the database is running: `docker-compose ps`
- Test connection manually: `psql $DATABASE_URL`
- Ensure RLS policies are properly configured

### Missing Dependencies
**Symptoms**: "Module not found" or "Command not found"
**Solutions**:
- Reinstall Python dependencies: `pip install -r requirements.txt`
- Reinstall Node.js packages: `rm -rf node_modules && npm install`
- Verify Python and Node.js versions match requirements
- Check virtual environment activation

### Authentication Failures
**Symptoms**: "Unauthorized" or "Invalid token"
**Solutions**:
- Verify API_SECRET_KEY is set and matches across services
- Check JWT token expiration settings
- Validate Supabase service role key permissions
- Ensure CORS settings include your domain

### Performance Issues
**Symptoms**: Slow queries or high CPU usage
**Solutions**:
- Check slow query log: `docker exec nfl-predictor-api python -c "from config.database_optimization import get_db_optimizer; print(get_db_optimizer().get_performance_report())"`
- Verify Redis is running and accessible
- Check connection pool settings
- Monitor memory usage

### Migration Problems
**Symptoms**: "Relation does not exist" or "Column not found"
**Solutions**:
- Run migrations: `supabase db push`
- Verify migration scripts executed in correct order
- Check database schema version
- Clear migration state if needed

**Section sources**
- [PRODUCTION_SETUP_GUIDE.md](file://PRODUCTION_SETUP_GUIDE.md#L1-L286)
- [scripts/validate_implementation.py](file://scripts/validate_implementation.py)
- [config/database_optimization.py](file://config/database_optimization.py)

## Verification and Testing
Verify successful setup with these commands and expected outputs:

1. **Check Service Health**
```bash
curl http://localhost:8000/health
```
**Expected Output**:
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "available",
  "timestamp": "2025-09-16T10:00:00Z"
}
```

2. **Verify Database Connection**
```bash
node scripts/check_database_schema.mjs
```
**Expected Output**:
```
✓ Database connection successful
✓ Found 7 required tables
✓ RLS policies configured
✓ Realtime enabled on 3 tables
```

3. **Test Data Availability**
```bash
python scripts/show_all_predictions.py
```
**Expected Output**:
```
Found 272 predictions for 16 games
Latest game: KC vs BUF (Week 2)
Prediction accuracy: 78.4%
```

4. **Check Expert System**
```bash
curl http://localhost:8000/api/experts/leaderboard
```
**Expected Output**:
```json
[
  {
    "expert_name": "Statistical Analyst",
    "accuracy": 82.3,
    "games_predicted": 156,
    "streak": 8
  }
]
```

5. **Test WebSocket Connection**
```bash
wscat -c ws://localhost:8080/ws/live-updates
```
**Expected Output**:
```
Connected to live updates stream
Receiving game events...
```

6. **Run Comprehensive Validation**
```bash
python verify_comprehensive_system.py
```
**Expected Output**:
```
=== SYSTEM VERIFICATION ===
✓ Environment configuration
✓ Database connectivity
✓ API endpoints accessible
✓ Prediction engine operational
✓ Caching layer functional
✓ WebSocket connection established
All systems operational
```

These verification steps ensure all components are properly configured and functioning as expected before proceeding with regular use or production deployment.

**Section sources**
- [scripts/check_database_schema.mjs](file://scripts/check_database_schema.mjs)
- [scripts/show_all_predictions.py](file://scripts/show_all_predictions.py)
- [verify_comprehensive_system.py](file://verify_comprehensive_system.py)
- [src/api/app.py](file://src/api/app.py)
- [src/websocket/websocket_manager.py](file://src/websocket/websocket_manager.py)