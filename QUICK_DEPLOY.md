# Quick Deployment Guide

Get your app deployed in minutes!

## Prerequisites

1. **Node.js 20+** installed
2. **Google Gemini API Key** - [Get one here](https://ai.google.dev/)
3. **Docker** (optional, for containerized deployment)

## Quick Start

### 1. Setup Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# GEMINI_API_KEY=your_actual_api_key_here
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Test Build Locally

```bash
npm run build
npm run preview
```

Visit `http://localhost:3000` to verify everything works.

## Deployment Options

### Option 1: Docker (Recommended for Self-Hosting)

```bash
# Build the image
docker build --build-arg GEMINI_API_KEY=your_api_key_here -t brooks-briefing:latest .

# Run the container
docker run -d -p 80:80 --name brooks-briefing brooks-briefing:latest
```

Or use Docker Compose:

```bash
# Set GEMINI_API_KEY in .env file first
docker-compose build --build-arg GEMINI_API_KEY=$(grep GEMINI_API_KEY .env | cut -d '=' -f2)
docker-compose up -d
```

### Option 2: Vercel (Easiest)

1. Install Vercel CLI: `npm i -g vercel`
2. Deploy: `vercel`
3. Set `GEMINI_API_KEY` in Vercel dashboard (Project Settings > Environment Variables)
4. Redeploy to apply environment variables

### Option 3: Netlify

1. Install Netlify CLI: `npm i -g netlify-cli`
2. Deploy: `netlify deploy --prod`
3. Set `GEMINI_API_KEY` in Netlify dashboard (Site Settings > Environment Variables)

### Option 4: GitHub Pages

```bash
# Install gh-pages
npm install --save-dev gh-pages

# Deploy
npm run deploy
```

**Note**: For GitHub Pages, set `GEMINI_API_KEY` as a GitHub Actions secret and use it in your build workflow.

## Verify Deployment

1. ✅ App loads without errors
2. ✅ Can generate a report
3. ✅ Chat interface works
4. ✅ All features functional

## Troubleshooting

**Build fails?**
- Check Node.js version: `node --version` (should be 20+)
- Clear cache: `rm -rf node_modules package-lock.json && npm install`

**API key not working?**
- Verify `.env` file exists and has correct key
- For production builds, ensure key is set during build process
- Check API key restrictions in Google Cloud Console

**Docker issues?**
- Ensure Docker is running
- Check logs: `docker logs brooks-briefing`
- Rebuild: `docker-compose down && docker-compose build --no-cache`

## Next Steps

- Review [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment options
- Check [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for comprehensive checklist
- Set up monitoring and error tracking
- Configure API key restrictions in Google Cloud Console

## Security Note

⚠️ The API key is currently embedded in the client bundle. For production:
- Set API key restrictions in Google Cloud Console
- Consider implementing a backend proxy
- Monitor API usage regularly

