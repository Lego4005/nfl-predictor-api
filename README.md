
# NFL Frontend (Clean Vite + React)

A minimal React dashboard for your NFL Predictor API. 

## Steps to Deploy

### 1. Local Development
```bash
npm install
npm run dev
```

### 2. Build for Production
```bash
npm run build
```

### 3. Vercel Setup
- Framework Preset: **Other**
- Build Command: `npm run build`
- Output Directory: `dist`
- Node: 18.x or 20.x

### 4. Environment Variable
```
VITE_API_BASE=https://nfl-predictor-api.onrender.com
```

That's it. Once deployed, you'll have tables, week selector, and working downloads.
