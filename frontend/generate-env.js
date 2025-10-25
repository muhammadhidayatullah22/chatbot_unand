/**
 * Generate env.js from root .env file
 * This script reads environment variables from root .env and generates public/env.js
 */

const fs = require('fs');
const path = require('path');

// Load dotenv from root directory
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });

// Extract only REACT_APP_* variables
const envConfig = {
  REACT_APP_BACKEND_URL: process.env.REACT_APP_BACKEND_URL || "http://localhost:8001",
  REACT_APP_GOOGLE_CLIENT_ID: process.env.REACT_APP_GOOGLE_CLIENT_ID || "",
  REACT_APP_ADMIN_DOMAIN: process.env.REACT_APP_ADMIN_DOMAIN || "localhost"
};

// Generate env.js content
const envJsContent = `window.__ENV__ = ${JSON.stringify(envConfig, null, 2)};
`;

// Write to public/env.js
const envJsPath = path.resolve(__dirname, 'public/env.js');

try {
  fs.writeFileSync(envJsPath, envJsContent, 'utf8');
  
  console.log('✅ Generated env.js from root .env file');
  console.log('📍 Location:', envJsPath);
  console.log('📝 Configuration:');
  console.log('   - REACT_APP_BACKEND_URL:', envConfig.REACT_APP_BACKEND_URL);
  console.log('   - REACT_APP_GOOGLE_CLIENT_ID:', envConfig.REACT_APP_GOOGLE_CLIENT_ID ? envConfig.REACT_APP_GOOGLE_CLIENT_ID.substring(0, 30) + '...' : 'NOT SET');
  console.log('   - REACT_APP_ADMIN_DOMAIN:', envConfig.REACT_APP_ADMIN_DOMAIN);
  console.log('');
  console.log('ℹ️  Note: env.js is auto-generated. Edit .env in root folder instead!');
  
} catch (error) {
  console.error('❌ Error generating env.js:', error.message);
  process.exit(1);
}

