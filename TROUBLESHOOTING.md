# Troubleshooting Guide

## Common Errors and Solutions

### Error: "API Key not found" or Blank Page

**Symptoms:**
- App loads but shows "API Key not found" error
- Blank page or initialization spinner that never completes
- Console shows: "API_KEY or GEMINI_API_KEY is missing"

**Solutions:**
1. **Check .env file exists:**
   ```bash
   # Windows PowerShell
   Test-Path .env
   Get-Content .env
   ```

2. **Verify .env file format:**
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```
   - No quotes around the value
   - No spaces around the `=`
   - No trailing spaces

3. **Restart the dev server:**
   - Stop the server (Ctrl+C)
   - Start again: `npm run dev`
   - Vite needs to be restarted to pick up new environment variables

4. **Check vite.config.ts:**
   - Ensure it's loading from `.env` file
   - The config should have: `loadEnv(mode, '.', '')`

### Error: "Cannot GET /" or 404 Errors

**Symptoms:**
- Browser shows "Cannot GET /" or 404
- Network tab shows failed requests

**Solutions:**
1. **Ensure dev server is running:**
   ```bash
   npm run dev
   ```
   Should see: `Local: http://localhost:8080/`

2. **Check port 8080 is available:**
   - Another app might be using port 8080 (e.g., Streamlit backend)
   - Vite will try the next available port if 8080 is taken
   - Check the terminal output for the actual port

3. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
   - Or clear cache in browser settings

### Error: Module Not Found

**Symptoms:**
- Console shows: "Failed to resolve import" or "Module not found"
- Red error overlay in browser

**Solutions:**
1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Check node_modules exists:**
   ```bash
   Test-Path node_modules
   ```

3. **Delete and reinstall:**
   ```bash
   Remove-Item -Recurse -Force node_modules
   Remove-Item package-lock.json
   npm install
   ```

### Error: "Failed to initialize report"

**Symptoms:**
- App loads but shows error message
- Falls back to input form
- Console shows API errors

**Solutions:**
1. **Verify API key is valid:**
   - Check at https://ai.google.dev/
   - Ensure API key has proper permissions
   - Check API quota hasn't been exceeded

2. **Check network connectivity:**
   - Ensure internet connection is working
   - Check if firewall is blocking requests

3. **Try manual report generation:**
   - Use the input form to generate a report manually
   - This will show more detailed error messages

### Error: Blank Page / Nothing Renders

**Symptoms:**
- Browser shows blank page
- No console errors
- Network requests succeed

**Solutions:**
1. **Check browser console:**
   - Open DevTools (F12)
   - Look for JavaScript errors in Console tab
   - Check Network tab for failed requests

2. **Verify index.html:**
   - Ensure `<div id="root"></div>` exists
   - Check that `index.tsx` is being loaded

3. **Check React is mounting:**
   - Add console.log in `index.tsx` to verify it's running
   - Check if root element is found

### Error: Port Already in Use

**Symptoms:**
- Terminal shows: "Port 8080 is in use"
- Server won't start

**Solutions:**
1. **Find and kill the process:**
   ```powershell
   # Windows PowerShell
   netstat -ano | findstr :8080
   taskkill /PID <PID> /F
   ```
   Note: If Streamlit backend is using port 8080, stop it first or run on different port

2. **Use a different port:**
   - Edit `vite.config.ts`
   - Change `port: 8080` to another port (e.g., `port: 3000`)

### Error: TypeScript Errors

**Symptoms:**
- Red squiggles in IDE
- Build fails with TypeScript errors

**Solutions:**
1. **Run type check:**
   ```bash
   npm run type-check
   ```

2. **Check tsconfig.json:**
   - Ensure it's properly configured
   - Check for any syntax errors

3. **Restart TypeScript server:**
   - In VS Code/Cursor: Ctrl+Shift+P → "TypeScript: Restart TS Server"

## Quick Diagnostic Steps

1. **Check .env file:**
   ```powershell
   Get-Content .env
   ```

2. **Verify dependencies:**
   ```bash
   npm list --depth=0
   ```

3. **Check dev server output:**
   - Look for any error messages in terminal
   - Check what port it's actually using

4. **Browser DevTools:**
   - Open Console tab - look for errors
   - Open Network tab - check for failed requests
   - Check if API calls are being made

5. **Test API key directly:**
   - The app should show a clear error if API key is missing
   - If API key is invalid, you'll get an error from Gemini API

## Still Having Issues?

1. **Check the browser console** - Most errors will be logged there
2. **Check the terminal** where `npm run dev` is running
3. **Verify your .env file** has the correct API key
4. **Restart everything:**
   - Stop dev server
   - Clear browser cache
   - Restart dev server
   - Hard refresh browser

## Getting Help

When reporting issues, please include:
- Error message from browser console
- Error message from terminal
- Steps to reproduce
- Browser and version
- Node.js version (`node --version`)
- Whether .env file exists and is formatted correctly

