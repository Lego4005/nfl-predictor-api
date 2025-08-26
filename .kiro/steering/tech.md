# Technology Stack

## Frontend
- **Framework**: React 18.3.1 with Vite 4.5.0 build system
- **Language**: JavaScript (ES modules)
- **Styling**: Inline styles (no CSS framework dependencies)
- **State Management**: React hooks (useState, useEffect)
- **HTTP Client**: Native fetch API with cache-busting

## Backend
- **Framework**: FastAPI with uvicorn server
- **Language**: Python 3.8+
- **Dependencies**: pandas, numpy, scikit-learn, fpdf
- **CORS**: Enabled for cross-origin requests

## Build System & Commands

### Development
```bash
npm install          # Install dependencies
npm run dev          # Start development server (Vite)
```

### Production
```bash
npm run build        # Build for production (outputs to dist/)
npm run preview      # Preview production build locally
```

### Python Backend
```bash
pip install -r requirements.txt    # Install Python dependencies
uvicorn main:app --reload          # Start FastAPI development server
```

## Environment Configuration
- **VITE_API_BASE**: Backend API URL (required for production)
- **Node Version**: 18.x or 20.x required
- **Default API**: https://nfl-predictor-api.onrender.com

## Deployment
- **Frontend**: Vercel (Framework: Other, Build: `npm run build`, Output: `dist`)
- **Backend**: Render.com or similar Python hosting
- **Build Output**: Static files in `dist/` directory