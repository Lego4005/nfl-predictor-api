# 🚀 Production Database Configuration Guide

## Overview
This guide covers the complete production database setup and optimization for the AI-Powered Sports Prediction Platform. The system is optimized for high performance with 15 competing expert models, AI Council voting, and comprehensive analytics.

## Files Created

### 1. Core Configuration Files
- `supabase/config.toml` - Supabase local development configuration
- `config/database_optimization.py` - Database optimization utilities and connection pooling
- `config/production_deployment.py` - Production deployment configuration generator

### 2. Database Optimization
- `supabase/migrations/030_production_database_optimization.sql` - Production database optimization SQL

### 3. Production Deployment Files
- `docker-compose.prod.yml` - Production Docker Compose configuration
- `nginx.conf` - Production Nginx reverse proxy configuration
- `deploy.sh` - Automated production deployment script
- `.env.production.template` - Production environment variables template
- `monitoring.yml` - Prometheus monitoring configuration

## Database Optimization Features

### Connection Pool Optimization
- **Min Pool Size**: 10 connections (configurable via DB_MIN_POOL_SIZE)
- **Max Pool Size**: 50 connections (configurable via DB_MAX_POOL_SIZE)
- **Query Timeout**: 60 seconds (configurable via DB_QUERY_TIMEOUT)
- **Statement Cache**: 2048 prepared statements
- **Connection Lifetime**: 600 seconds max inactive time

### Performance Indexes
The system creates 15+ optimized indexes for:
- Expert competition queries (expert rankings, performance metrics)
- AI Council selection and voting processes
- Prediction category filtering and searching
- Performance analytics and trending
- Self-healing event tracking
- Episodic memory retrieval

### Materialized Views
- `mv_expert_leaderboard` - Real-time expert rankings with council status
- `mv_expert_performance_trends` - 30-day performance trend analysis

### Query Optimization
- **Slow Query Monitoring**: Queries >2 seconds automatically logged
- **Statement Caching**: Prepared statement optimization
- **Connection-level Settings**: Optimized timeout and memory settings
- **Automated ANALYZE**: Statistics updated regularly

## Production Deployment Architecture

### Container Stack
1. **NFL Predictor API** (Port 8000)
   - FastAPI application with expert competition framework
   - Database connection pooling and optimization
   - Health checks and monitoring endpoints

2. **Redis Cache** (Port 6379)
   - 256MB memory limit with LRU eviction
   - Password-protected access
   - Data persistence enabled

3. **Nginx Reverse Proxy** (Ports 80/443)
   - SSL termination and HTTPS redirection
   - Rate limiting (10 req/s API, 5 req/s auth)
   - Static file serving and caching
   - Gzip compression enabled

### Security Features
- **SSL/TLS**: TLS 1.2+ with strong cipher suites
- **Security Headers**: HSTS, X-Frame-Options, CSP
- **Rate Limiting**: Per-endpoint rate limiting
- **CORS**: Configurable cross-origin policies

### Monitoring & Health Checks
- **Application Health**: /health endpoint monitoring
- **Database Health**: Connection pool monitoring
- **Redis Health**: Cache availability checks
- **Performance Metrics**: Query time and error rate tracking

## Environment Configuration

### Required Environment Variables
```bash
# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key
DATABASE_URL=postgresql://postgres:password@host:5432/postgres

# API Keys
ODDS_API_KEY=your-odds-api-key
SPORTSDATA_IO_KEY=your-sportsdata-key
RAPID_API_KEY=your-rapid-api-key

# Cache & Performance
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=secure-password
DB_MIN_POOL_SIZE=10
DB_MAX_POOL_SIZE=50

# Security
API_SECRET_KEY=your-jwt-secret
CORS_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com
```

## Database Schema Optimization

### Expert Competition Tables
- `enhanced_expert_models` - 15 expert personalities with performance metrics
- `expert_predictions_enhanced` - 27-category prediction storage
- `ai_council_selections` - Top 5 expert selection tracking
- `ai_council_voting` - Weighted consensus voting system
- `expert_performance_analytics` - Multi-dimensional performance tracking

### Performance Features
- **Category-Specific Indexing**: Each of 27 prediction categories optimized
- **Time-Series Optimization**: Recent performance queries (<30 days)
- **Composite Indexes**: Multi-column indexes for complex queries
- **Partial Indexes**: Filtered indexes for active experts only

### Auto-Maintenance
- **Auto-Vacuum**: Enabled with optimized thresholds
- **Statistics Updates**: Automated ANALYZE on critical tables
- **Index Maintenance**: Automatic reindexing of high-usage tables
- **Data Cleanup**: Automated cleanup of old analytics data

## Deployment Process

### 1. Initial Setup
```bash
# Copy environment template
cp .env.production.template .env.production

# Edit with your actual values
nano .env.production

# Make deployment script executable
chmod +x deploy.sh
```

### 2. Database Setup
```bash
# Run database migrations
supabase db push

# Apply optimization settings
psql -f supabase/migrations/030_production_database_optimization.sql
```

### 3. Deploy Application
```bash
# Run automated deployment
./deploy.sh
```

### 4. Verify Deployment
```bash
# Check health endpoint
curl http://localhost/health

# Check expert competition status
curl http://localhost/api/experts/leaderboard

# Check AI Council status
curl http://localhost/api/council/members
```

## Performance Monitoring

### Database Performance Views
- `v_database_performance` - Table statistics and dead row percentages
- `v_slow_queries` - Queries taking >1 second average
- `v_index_usage` - Index hit ratio analysis

### Application Metrics
- Expert prediction accuracy rates
- AI Council voting consensus times
- Database query performance
- Cache hit/miss ratios

### Alerts Configuration
- High error rates (>10% for 5 minutes)
- Database connection failures
- Slow queries (>2 seconds average)
- Memory usage (>90%)
- Expert competition system failures

## Optimization Maintenance

### Daily Tasks (Automated)
- Refresh materialized views
- Update table statistics
- Clean old performance data
- Check slow query reports

### Weekly Tasks
- Comprehensive VACUUM ANALYZE
- Index usage analysis
- Performance trend review
- Backup verification

### Monthly Tasks
- Review and optimize slow queries
- Analyze expert competition performance
- Update prediction accuracy baselines
- Security patch updates

## Scaling Considerations

### Database Scaling
- **Read Replicas**: For analytics queries
- **Connection Pooling**: Optimized for concurrent users
- **Query Optimization**: Continuous monitoring and tuning
- **Index Strategy**: Regular review and optimization

### Application Scaling
- **Horizontal Scaling**: Multiple API instances
- **Load Balancing**: Nginx upstream configuration
- **Cache Strategy**: Redis cluster for larger datasets
- **Expert Distribution**: Parallel expert processing

## Troubleshooting

### Common Issues
1. **High Database CPU**: Check slow queries and optimize indexes
2. **Memory Pressure**: Review cache settings and query complexity
3. **Expert Competition Delays**: Monitor self-healing events
4. **Council Voting Failures**: Check expert availability and ranking

### Monitoring Commands
```bash
# Database performance
docker exec -it nfl-predictor-api python -c "
from config.database_optimization import get_db_optimizer
print(get_db_optimizer().get_performance_report())
"

# Redis status
docker exec -it nfl-predictor-redis redis-cli info memory

# Container logs
docker logs nfl-predictor-api --tail 100
```

## Security Best Practices

### Database Security
- Use service role key only in backend
- Enable Row Level Security (RLS)
- Regular security updates
- Monitor access patterns

### Application Security
- Environment variable protection
- API key rotation schedule
- SSL certificate management
- Rate limiting configuration

## Backup & Recovery

### Automated Backups
- Daily database snapshots
- Configuration file backups
- 30-day retention policy
- Monitoring backup success

### Recovery Procedures
- Point-in-time recovery capability
- Expert model state restoration
- Performance analytics rebuild
- Configuration rollback procedures

---

## Next Steps After Configuration

1. **Set up Supabase project** with the provided schema
2. **Configure environment variables** with actual API keys
3. **Run deployment script** to start production services
4. **Monitor performance** using the provided dashboards
5. **Scale as needed** based on usage patterns

The production configuration provides a robust, scalable foundation for the AI-Powered Sports Prediction Platform with comprehensive monitoring, optimization, and security features.