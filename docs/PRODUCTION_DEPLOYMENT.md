# 🚀 NFL Predictor API - Production Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Application Deployment](#application-deployment)
5. [Server Configuration](#server-configuration)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Security Checklist](#security-checklist)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **Node.js**: 18.x or higher
- **npm**: 9.x or higher
- **PostgreSQL**: 14+ (via Supabase)
- **RAM**: Minimum 2GB, recommended 4GB
- **Storage**: 10GB minimum
- **Ports**: 80/443 (web), 8080 (WebSocket)

### Required Services
- Supabase account (database & auth)
- OpenRouter API key (AI predictions)
- The-Odds-API key (betting lines)
- News API key (sentiment analysis)
- Domain name with SSL certificate

---

## Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-org/nfl-predictor-api.git
cd nfl-predictor-api
```

### 2. Install Dependencies
```bash
npm ci --production
```

### 3. Configure Environment Variables
```bash
cp .env.example .env.production
```

Edit `.env.production`:
```env
# Required - Supabase Configuration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key  # For server-side operations

# Required - AI Predictions
VITE_OPENROUTER_API_KEY=sk-or-v1-your-key

# Required - Odds Data
VITE_ODDS_API_KEY=your-odds-api-key

# Optional - Enhanced Features
VITE_NEWS_API_KEY=your-news-api-key
VITE_WEATHER_API_KEY=your-weather-api-key

# Server Configuration
NODE_ENV=production
PORT=5000
WS_PORT=8080

# Security
CORS_ORIGIN=https://your-domain.com
RATE_LIMIT_WINDOW=15
RATE_LIMIT_MAX=100
```

---

## Database Configuration

### 1. Supabase Setup

#### Enable Required Extensions
```sql
-- Run in Supabase SQL Editor
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

#### Verify Tables
```sql
-- Check required tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('games', 'predictions', 'user_picks', 'profiles');
```

#### Configure Row Level Security
```sql
-- Disable RLS for public read access (adjust based on your needs)
ALTER TABLE games ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users
CREATE POLICY "Games are viewable by everyone"
ON games FOR SELECT
USING (true);

CREATE POLICY "Predictions are viewable by everyone"
ON predictions FOR SELECT
USING (true);

CREATE POLICY "Users can manage their own picks"
ON user_picks
USING (auth.uid() = user_id);
```

### 2. Initial Data Load
```bash
# Run data migration
node scripts/dataMigrationService.js

# Verify data
node scripts/validate_system.js
```

---

## Application Deployment

### Option 1: PM2 (Recommended)

#### Install PM2
```bash
npm install -g pm2
```

#### Create PM2 Ecosystem File
```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'nfl-frontend',
      script: 'npm',
      args: 'run preview',
      env: {
        NODE_ENV: 'production',
        PORT: 4173
      }
    },
    {
      name: 'nfl-websocket',
      script: './src/websocket/websocketServer.js',
      instances: 1,
      env: {
        NODE_ENV: 'production',
        WS_PORT: 8080
      }
    },
    {
      name: 'nfl-scheduler',
      script: './src/services/schedulerService.js',
      instances: 1,
      cron_restart: '0 */30 * * *',
      env: {
        NODE_ENV: 'production'
      }
    }
  ]
};
```

#### Start Services
```bash
# Build production assets
npm run build

# Start all services
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save
pm2 startup
```

### Option 2: Docker Deployment

#### Dockerfile
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --production

# Copy application files
COPY . .

# Build frontend
RUN npm run build

# Expose ports
EXPOSE 4173 8080

# Start services
CMD ["npm", "run", "start-full"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  nfl-app:
    build: .
    ports:
      - "4173:4173"
      - "8080:8080"
    env_file:
      - .env.production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4173"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### Deploy with Docker
```bash
docker-compose up -d
```

### Option 3: Systemd Services

#### Create Service Files
```ini
# /etc/systemd/system/nfl-frontend.service
[Unit]
Description=NFL Predictor Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/nfl-predictor
ExecStart=/usr/bin/npm run preview
Restart=on-failure
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/nfl-websocket.service
[Unit]
Description=NFL Predictor WebSocket Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/nfl-predictor
ExecStart=/usr/bin/node src/websocket/websocketServer.js
Restart=on-failure
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

#### Enable Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable nfl-frontend nfl-websocket
sudo systemctl start nfl-frontend nfl-websocket
```

---

## Server Configuration

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/nfl-predictor
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:4173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self' https: wss:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/rss+xml application/atom+xml image/svg+xml text/javascript application/x-javascript application/x-font-ttf application/vnd.ms-fontobject font/opentype;
}
```

### SSL Certificate Setup
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## Monitoring & Maintenance

### 1. Health Monitoring

#### Setup Health Check Endpoint
```javascript
// Add to src/services/healthCheck.js
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    services: {
      database: checkDatabase(),
      websocket: checkWebSocket(),
      predictions: checkPredictions()
    }
  });
});
```

#### Uptime Monitoring Services
- **UptimeRobot**: Free tier available
- **Pingdom**: Advanced monitoring
- **New Relic**: Application performance monitoring

### 2. Logging

#### Configure PM2 Logs
```bash
# View logs
pm2 logs

# Setup log rotation
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
```

#### Application Logging
```javascript
// Use Winston for structured logging
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});
```

### 3. Backup Strategy

#### Database Backups
```bash
# Daily backup script
#!/bin/bash
# /home/user/backup-db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"

# Use Supabase CLI for backup
supabase db dump -f "$BACKUP_DIR/backup_$DATE.sql"

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
```

#### Cron Job
```bash
# Add to crontab
0 2 * * * /home/user/backup-db.sh
```

### 4. Performance Optimization

#### CDN Setup (Cloudflare)
1. Add domain to Cloudflare
2. Enable caching for static assets
3. Configure page rules for API endpoints
4. Enable Argo for improved routing

#### Database Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_games_game_time ON games(game_time);
CREATE INDEX idx_predictions_game_id ON predictions(game_id);
CREATE INDEX idx_user_picks_user_game ON user_picks(user_id, game_id);

-- Analyze tables regularly
ANALYZE games;
ANALYZE predictions;
ANALYZE user_picks;
```

---

## Security Checklist

### Essential Security Measures
- [ ] **Environment Variables**: Never commit `.env` files
- [ ] **HTTPS Only**: Force SSL redirect
- [ ] **Rate Limiting**: Implement API rate limits
- [ ] **Input Validation**: Sanitize all user inputs
- [ ] **SQL Injection**: Use parameterized queries
- [ ] **XSS Protection**: Implement CSP headers
- [ ] **CORS**: Configure allowed origins
- [ ] **Dependencies**: Regular security audits with `npm audit`
- [ ] **Secrets Rotation**: Rotate API keys quarterly
- [ ] **Access Logs**: Monitor suspicious activity
- [ ] **Firewall**: Configure UFW or cloud firewall
- [ ] **SSH**: Disable password auth, use keys only

### API Key Security
```javascript
// Implement key rotation
const rotateApiKeys = async () => {
  // Store multiple keys in env
  const keys = [
    process.env.API_KEY_PRIMARY,
    process.env.API_KEY_SECONDARY
  ];

  // Use round-robin or failover
  return keys[Date.now() % keys.length];
};
```

---

## Troubleshooting

### Common Issues & Solutions

#### Frontend Not Loading
```bash
# Check if port is in use
lsof -i :4173

# Check build output
ls -la dist/

# Rebuild if necessary
npm run build
```

#### WebSocket Connection Failed
```bash
# Check if WebSocket server is running
pm2 status nfl-websocket

# Check logs
pm2 logs nfl-websocket --lines 100

# Test WebSocket connection
wscat -c ws://localhost:8080
```

#### Database Connection Issues
```bash
# Test Supabase connection
curl https://your-project.supabase.co/rest/v1/games \
  -H "apikey: your-anon-key" \
  -H "Authorization: Bearer your-anon-key"

# Check RLS policies
psql -h your-project.supabase.co -U postgres -d postgres
\dt
\d games
```

#### High Memory Usage
```bash
# Check memory usage
pm2 monit

# Restart services
pm2 restart all

# Increase Node memory limit if needed
NODE_OPTIONS="--max-old-space-size=4096" npm start
```

### Monitoring Commands
```bash
# System resources
htop

# Network connections
netstat -tulpn

# Disk usage
df -h

# Service status
systemctl status nfl-frontend
pm2 status

# Real-time logs
pm2 logs --lines 200
tail -f /var/log/nginx/error.log
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Run tests: `npm test`
- [ ] Build production: `npm run build`
- [ ] Validate system: `node scripts/validate_system.js`
- [ ] Update dependencies: `npm update`
- [ ] Security audit: `npm audit fix`

### Deployment
- [ ] Backup database
- [ ] Update environment variables
- [ ] Deploy code
- [ ] Run migrations
- [ ] Restart services
- [ ] Clear caches

### Post-Deployment
- [ ] Verify all endpoints
- [ ] Check WebSocket connection
- [ ] Test authentication flow
- [ ] Monitor error logs
- [ ] Check performance metrics
- [ ] Verify scheduled tasks

---

## Support & Maintenance

### Regular Maintenance Tasks
- **Daily**: Check logs for errors
- **Weekly**: Review performance metrics
- **Monthly**: Update dependencies
- **Quarterly**: Security audit & key rotation

### Monitoring Dashboard
Access system metrics at:
- PM2 Web: `pm2 web`
- Health Check: `https://your-domain.com/health`
- Supabase Dashboard: `https://app.supabase.io`

### Emergency Contacts
- **System Admin**: admin@your-company.com
- **Database Issues**: Use Supabase support
- **API Issues**: Check provider status pages

---

## Conclusion

This deployment guide covers the essential steps to get your NFL Predictor API running in production. Remember to:
1. Always test in staging first
2. Keep regular backups
3. Monitor system health
4. Update dependencies regularly
5. Follow security best practices

For additional support, refer to the project documentation or contact the development team.

**Last Updated**: January 2025
**Version**: 1.0.0