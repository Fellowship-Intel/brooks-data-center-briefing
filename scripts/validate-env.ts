/**
 * Environment variable validation script
 * Run before build to ensure required variables are set
 */

const requiredEnvVars = ['VITE_API_URL'];

function validateEnv(): void {
  const missing: string[] = [];
  const errors: string[] = [];

  // Check required variables
  for (const varName of requiredEnvVars) {
    const value = process.env[varName];
    if (!value || value.trim() === '') {
      missing.push(varName);
    }
  }

  // Validate VITE_API_URL format if set
  const apiUrl = process.env.VITE_API_URL;
  if (apiUrl) {
    try {
      const url = new URL(apiUrl);
      if (!['http:', 'https:'].includes(url.protocol)) {
        errors.push('VITE_API_URL must use http:// or https:// protocol');
      }
    } catch (e) {
      errors.push('VITE_API_URL must be a valid URL');
    }
  }

  // Report errors
  if (missing.length > 0) {
    console.error('❌ Missing required environment variables:');
    missing.forEach(v => console.error(`   - ${v}`));
    console.error('\nPlease set these variables before building.');
    process.exit(1);
  }

  if (errors.length > 0) {
    console.error('❌ Environment variable validation errors:');
    errors.forEach(e => console.error(`   - ${e}`));
    process.exit(1);
  }

  console.log('✅ All environment variables are valid');
}

validateEnv();

