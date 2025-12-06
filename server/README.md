# Brooks Data Center Daily Briefing API

Node.js/Express backend API for the Brooks Data Center Daily Briefing application.

## Features

- **Report Generation**: AI-powered daily trading reports using Google Gemini
- **Firestore Integration**: Store and retrieve reports from Google Cloud Firestore
- **TTS Support**: Text-to-speech with Eleven Labs (primary) and Gemini TTS (fallback)
- **Cloud Storage**: Store audio files in Google Cloud Storage
- **Health Checks**: Comprehensive health check endpoint
- **Chat/Q&A**: Interactive chat interface for follow-up questions
- **Error Handling**: Retry logic, circuit breakers, and comprehensive error tracking

## Setup

### Prerequisites

- Node.js 20+
- GCP service account with appropriate permissions
- Gemini API key
- Eleven Labs API key (optional, falls back to Gemini TTS)

### Installation

```bash
cd server
npm install
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
- `GCP_PROJECT_ID`: Your GCP project ID (default: "mikebrooks")
- `GEMINI_API_KEY`: Your Gemini API key
- `ELEVEN_LABS_API_KEY`: Your Eleven Labs API key (optional)

For local development, set:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=".secrets/app-backend-sa.json"
```

### Development

```bash
npm run dev
```

Server runs on `http://localhost:8000`

### Production Build

```bash
npm run build
npm start
```

## API Endpoints

### Reports

- `POST /reports/generate` - Generate a new daily report
- `GET /reports/:tradingDate` - Fetch an existing report
- `GET /reports/:tradingDate/audio` - Get audio metadata
- `POST /reports/generate/watchlist` - Generate watchlist-based report

### Health

- `GET /health` - Comprehensive health check

### Chat

- `POST /chat/message` - Send a chat message and get AI response

## Architecture

```
server/
├── src/
│   ├── index.ts              # Express app entry point
│   ├── routes/               # API route handlers
│   ├── services/             # Business logic
│   ├── repositories/         # Data access layer
│   ├── clients/              # GCP client initialization
│   ├── utils/                # Utility functions
│   ├── types/                # TypeScript interfaces
│   └── config/               # Configuration and constants
```

## Deployment

### Docker

```bash
docker build -t brooks-briefing-api:latest -f server/Dockerfile .
docker run -p 8000:8000 brooks-briefing-api:latest
```

### Google Cloud Run

See deployment scripts in `scripts/` directory.

## Testing

```bash
npm test
```

## License

ISC

