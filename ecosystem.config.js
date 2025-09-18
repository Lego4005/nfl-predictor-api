module.exports = {
  apps: [
    {
      // Frontend Application
      name: 'nfl-frontend',
      script: 'npm',
      args: 'run preview',
      cwd: './',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 4173
      },
      env_development: {
        NODE_ENV: 'development',
        PORT: 5173
      },
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      log_file: './logs/frontend-combined.log',
      time: true
    },
    {
      // WebSocket Server
      name: 'nfl-websocket',
      script: './src/websocket/websocketServer.js',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        WS_PORT: 8080
      },
      env_development: {
        NODE_ENV: 'development',
        WS_PORT: 8080
      },
      error_file: './logs/websocket-error.log',
      out_file: './logs/websocket-out.log',
      log_file: './logs/websocket-combined.log',
      time: true
    },
    {
      // Data Scheduler Service
      name: 'nfl-scheduler',
      script: './src/services/schedulerService.js',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      cron_restart: '0 */30 * * *', // Restart every 30 minutes
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production'
      },
      env_development: {
        NODE_ENV: 'development'
      },
      error_file: './logs/scheduler-error.log',
      out_file: './logs/scheduler-out.log',
      log_file: './logs/scheduler-combined.log',
      time: true
    }
  ],

  // Deployment configuration
  deploy: {
    production: {
      user: 'deploy',
      host: 'your-server.com',
      ref: 'origin/main',
      repo: 'git@github.com:your-org/nfl-predictor-api.git',
      path: '/var/www/nfl-predictor',
      'pre-deploy-local': 'npm test',
      'post-deploy': 'npm install && npm run build && pm2 reload ecosystem.config.js --env production',
      'pre-setup': 'mkdir -p /var/www/nfl-predictor'
    },
    staging: {
      user: 'deploy',
      host: 'staging.your-server.com',
      ref: 'origin/develop',
      repo: 'git@github.com:your-org/nfl-predictor-api.git',
      path: '/var/www/nfl-predictor-staging',
      'post-deploy': 'npm install && npm run build && pm2 reload ecosystem.config.js --env development',
      'pre-setup': 'mkdir -p /var/www/nfl-predictor-staging'
    }
  }
};