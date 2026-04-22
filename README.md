# NamanDarshan Ops AI

An AI-powered platform for temple darshan bookings, pandit services, and spiritual guidance using NamanDarshan.com data.

## Features

- 🤖 AI Agent for spiritual guidance and bookings
- 🕉️ Temple darshan information and VIP bookings
- 👨‍🦱 Pandit services for pujas and ceremonies
- 🏨 Hotel and cab booking assistance
- 🔍 Web scraping from namandarshan.com
- 📊 Excel data management

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React + TypeScript + Vite
- **AI**: Groq API (Llama 3.3)
- **Database**: Excel files (for simplicity)
- **Deployment**: Render (backend) + Vercel (frontend)

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### Setup

1. **Clone the repository**
   `ash
   git clone https://github.com/Sana-aafreen/Naman_ops_ai.git
   cd Naman_ops_ai
   `

2. **Backend Setup**
   `ash
   cd Backend
   python -m venv venv
   venv\Scripts\activate  # On Windows
   pip install -r requirements.txt
   `

3. **Frontend Setup**
   `ash
   cd ../Frontend
   npm install
   `

4. **Environment Variables**
   `ash
   cp .env.production .env
   # Edit .env with your GROQ_API_KEY
   `

5. **Run Data Scripts** (optional - regenerates scraped data)
   `ash
   cd ../scripts
   python scrape_all_pages.py
   python fetch_darshan_data.py
   `

6. **Start Services**
   `ash
   # Backend (from Backend directory)
   python main.py

   # Frontend (from Frontend directory)
   npm run dev
   `

## Deployment

### Backend (Render)

1. **Connect to Render**
   - Go to [render.com](https://render.com)
   - Connect your GitHub repository
   - Create a new Web Service

2. **Configuration**
   - **Runtime**: Docker
   - **Dockerfile Path**: ./Dockerfile
   - **Environment Variables**:
     - GROQ_API_KEY: Your Groq API key
     - Other variables as in .env.production

3. **Deploy**
   - Render will automatically build and deploy using the Dockerfile

### Frontend (Vercel)

1. **Connect to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Connect your GitHub repository
   - Import the project

2. **Configuration**
   - **Framework Preset**: Vite
   - **Root Directory**: Frontend
   - **Build Command**: 
pm run build
   - **Output Directory**: dist
   - **Environment Variables**:
     - VITE_API_URL: Your Render backend URL (e.g., https://your-app.onrender.com)

3. **Deploy**
   - Vercel will automatically build and deploy the frontend

### Environment Variables

Copy .env.production to .env and configure:

`ash
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional (with defaults)
HOST=0.0.0.0
PORT=8000
ENABLE_NAMANDARSHAN_SCRAPE=true
SCRAPE_TIMEOUT_SEC=12
SCRAPE_MAX_PAGES=4
SCRAPE_MAX_CHARS=6000
MAX_TOOL_ROUNDS=5
SESSION_TTL_MIN=60
CORS_ORIGINS=*

# Frontend (Vercel)
VITE_API_URL=https://your-render-backend.onrender.com
`

## API Endpoints

- GET /api/health - Health check
- POST /api/agent/chat - AI agent chat
- GET /api/data/{sheet} - Excel data endpoints
- POST /api/excel/upload - Upload Excel files
- GET /docs - API documentation

## Project Structure

`
├── Backend/              # FastAPI backend
│   ├── main.py          # Application entry point
│   ├── config.py        # Configuration management
│   ├── routes.py        # API route handlers
│   ├── ops_agent.py     # AI agent logic
│   ├── tools.py         # Agent tools
│   ├── namandarshan_scrape.py  # Web scraping
│   └── requirements.txt # Python dependencies
├── Frontend/             # React frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── scripts/              # Utility scripts
├── data/                 # Generated data files
├── Dockerfile            # Container configuration
├── render.yaml          # Render deployment config
├── vercel.json          # Vercel deployment config
└── .gitignore          # Git ignore rules
`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

MIT License - see LICENSE file for details
