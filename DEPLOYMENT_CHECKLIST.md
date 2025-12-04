# Deployment Checklist

Use this checklist to ensure your app is ready for deployment.

## Pre-Deployment

- [ ] **Environment Variables**
  - [ ] Create `.env` file from `.env.example` template
  - [ ] Set `GEMINI_API_KEY` in your environment
  - [ ] Verify `.env` is in `.gitignore` (should not be committed)

- [ ] **Dependencies**
  - [ ] Run `npm install` to ensure all dependencies are installed
  - [ ] Verify `package-lock.json` is up to date

- [ ] **Build Test**
  - [ ] Run `npm run build` successfully
  - [ ] Test production build locally: `npm run preview`
  - [ ] Verify all features work in production build

- [ ] **Type Checking**
  - [ ] Run `npm run type-check` to ensure no TypeScript errors

- [ ] **Security Review**
  - [ ] Review API key usage (currently embedded in client bundle)
  - [ ] Consider implementing backend proxy for production
  - [ ] Set API key restrictions in Google Cloud Console

## Platform-Specific Deployment

### Docker Deployment

- [ ] **Docker Setup**
  - [ ] Docker is installed and running
  - [ ] `.dockerignore` is configured
  - [ ] `nginx.conf` is in place

- [ ] **Build & Run**
  ```bash
  npm run docker:build
  npm run docker:run
  ```
  - [ ] Verify app is accessible at `http://localhost`
  - [ ] Check container logs: `docker logs brooks-briefing`

### Vercel Deployment

- [ ] **Vercel Setup**
  - [ ] Install Vercel CLI: `npm i -g vercel`
  - [ ] `vercel.json` is configured

- [ ] **Deploy**
  ```bash
  vercel
  ```
  - [ ] Set `GEMINI_API_KEY` in Vercel dashboard (Project Settings > Environment Variables)
  - [ ] Verify deployment URL works

### Netlify Deployment

- [ ] **Netlify Setup**
  - [ ] Install Netlify CLI: `npm i -g netlify-cli`
  - [ ] `netlify.toml` is configured

- [ ] **Deploy**
  ```bash
  netlify deploy --prod
  ```
  - [ ] Set `GEMINI_API_KEY` in Netlify dashboard (Site Settings > Environment Variables)
  - [ ] Verify deployment URL works

### GitHub Pages

- [ ] **Setup**
  - [ ] Install `gh-pages`: `npm install --save-dev gh-pages`
  - [ ] Add deploy script to `package.json`:
    ```json
    "predeploy": "npm run build",
    "deploy": "gh-pages -d dist"
    ```

- [ ] **Deploy**
  ```bash
  npm run deploy
  ```
  - [ ] Note: Environment variables must be set during build (use GitHub Actions secrets)

## Post-Deployment

- [ ] **Functionality Testing**
  - [ ] Test report generation
  - [ ] Test chat interface
  - [ ] Test all interactive features
  - [ ] Test on multiple browsers

- [ ] **Performance**
  - [ ] Check Lighthouse scores
  - [ ] Verify asset caching is working
  - [ ] Check bundle sizes

- [ ] **Monitoring**
  - [ ] Set up error tracking (if applicable)
  - [ ] Monitor API usage in Google Cloud Console
  - [ ] Set up alerts for API quota limits

- [ ] **Documentation**
  - [ ] Update deployment URLs in documentation
  - [ ] Document any platform-specific configurations

## Security Reminders

⚠️ **Important**: The current implementation embeds the API key in the client-side bundle. This means:
- The API key is visible to anyone who inspects the code
- Consider implementing a backend proxy for production use
- Set API key restrictions in Google Cloud Console (HTTP referrer restrictions, IP restrictions, etc.)
- Monitor API usage regularly
- Rotate API keys periodically

## Troubleshooting

### Build Fails
- Check Node.js version (requires 20+)
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check TypeScript errors: `npm run type-check`

### Environment Variables Not Working
- Ensure `.env` file exists in root directory
- Restart dev server after changing `.env`
- For production, set variables in platform dashboard

### Docker Issues
- Clear Docker cache: `docker builder prune`
- Check `.dockerignore` configuration
- Verify all files are copied in Dockerfile

### Deployment Platform Issues
- Check platform-specific logs
- Verify environment variables are set correctly
- Ensure build command matches platform requirements

