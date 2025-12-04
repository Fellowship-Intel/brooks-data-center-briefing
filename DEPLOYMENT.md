# Deployment Guide

This guide covers various deployment options for the Brooks Data Center Briefing application.

## Prerequisites

- Node.js 20+ installed
- Google Gemini API Key ([Get one here](https://ai.google.dev/))
- npm or yarn package manager

## Environment Variables

The application requires the following environment variable:

- `GEMINI_API_KEY`: Your Google Gemini API key

Create a `.env` file in the root directory:

```bash
GEMINI_API_KEY=your_api_key_here
```

**Important**: Never commit your `.env` file to version control. The `.env.example` file is provided as a template.

## Local Build and Preview

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set environment variables:**
   Create a `.env` file with your `GEMINI_API_KEY`

3. **Build for production:**
   ```bash
   npm run build
   ```

4. **Preview the production build:**
   ```bash
   npm run preview
   ```

The preview will be available at `http://localhost:3000`

## Docker Deployment

### Building the Docker Image

**Important**: The API key must be provided at build time since it's embedded in the client bundle.

```bash
docker build --build-arg GEMINI_API_KEY=your_api_key_here -t brooks-briefing:latest .
```

Or using a `.env` file with build args:

```bash
docker build --build-arg GEMINI_API_KEY=$(cat .env | grep GEMINI_API_KEY | cut -d '=' -f2) -t brooks-briefing:latest .
```

### Running the Container

```bash
docker run -d \
  -p 80:80 \
  --name brooks-briefing \
  brooks-briefing:latest
```

**Note**: Since the API key is embedded at build time, you don't need to pass it at runtime.

The application will be available at `http://localhost`

### Docker Compose

A `docker-compose.yml` file is already provided. To use it:

1. Create a `.env` file with your `GEMINI_API_KEY`
2. Build and run:

```bash
docker-compose build --build-arg GEMINI_API_KEY=${GEMINI_API_KEY}
docker-compose up -d
```

Or use the npm scripts:

```bash
npm run docker:build
npm run docker:run
```

To stop:

```bash
npm run docker:stop
```

## Platform-Specific Deployments

### Vercel

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   vercel
   ```

3. **Set environment variables:**
   - Go to your project settings in Vercel dashboard
   - Add `GEMINI_API_KEY` in the Environment Variables section

### Netlify

1. **Install Netlify CLI:**
   ```bash
   npm i -g netlify-cli
   ```

2. **Create `netlify.toml`:**
   ```toml
   [build]
     command = "npm run build"
     publish = "dist"

   [[redirects]]
     from = "/*"
     to = "/index.html"
     status = 200
   ```

3. **Deploy:**
   ```bash
   netlify deploy --prod
   ```

4. **Set environment variables:**
   - Go to Site settings > Environment variables
   - Add `GEMINI_API_KEY`

### AWS S3 + CloudFront

1. **Build the application:**
   ```bash
   npm run build
   ```

2. **Upload to S3:**
   ```bash
   aws s3 sync dist/ s3://your-bucket-name --delete
   ```

3. **Configure CloudFront:**
   - Create a CloudFront distribution pointing to your S3 bucket
   - Set up error pages: 404 → `/index.html` (for React Router)

4. **Set environment variables:**
   - Build-time environment variables are embedded in the bundle
   - Ensure `GEMINI_API_KEY` is set during build

### GitHub Pages

1. **Install gh-pages:**
   ```bash
   npm install --save-dev gh-pages
   ```

2. **Add to `package.json`:**
   ```json
   {
     "scripts": {
       "predeploy": "npm run build",
       "deploy": "gh-pages -d dist"
     }
   }
   ```

3. **Deploy:**
   ```bash
   npm run deploy
   ```

**Note**: Environment variables need to be set during build time. Consider using GitHub Actions secrets.

## Environment Variables in Production

### Build-time Variables

The current setup embeds environment variables at build time. This means:

- Variables are included in the JavaScript bundle
- They are visible in the client-side code
- **Security Note**: API keys exposed in client-side code can be accessed by anyone

### Recommended Approach

For production deployments, consider:

1. **Backend Proxy**: Create a backend service that holds the API key and proxies requests to Gemini
2. **Serverless Functions**: Use Vercel/Netlify functions to handle API calls server-side
3. **API Gateway**: Use an API gateway to manage and secure API keys

## Troubleshooting

### Build Fails

- Ensure all dependencies are installed: `npm install`
- Check that Node.js version is 20 or higher
- Verify TypeScript compilation: `npx tsc --noEmit`

### Environment Variables Not Working

- Ensure `.env` file exists in the root directory
- Variable names must start with `VITE_` for Vite to expose them (or use the current `define` approach)
- Restart the dev server after changing `.env` files

### Docker Build Issues

- Clear Docker cache: `docker builder prune`
- Ensure `.dockerignore` is properly configured
- Check that all required files are copied in Dockerfile

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Rotate API keys** regularly
4. **Monitor API usage** in Google Cloud Console
5. **Set API key restrictions** in Google Cloud Console
6. **Use HTTPS** in production
7. **Consider rate limiting** for API calls

## Monitoring and Maintenance

- Monitor application logs for errors
- Set up alerts for API quota limits
- Regularly update dependencies: `npm update`
- Review and update security patches

## Support

For issues or questions:
- Check the main [README.md](README.md)
- Review application logs
- Check Google Gemini API status

