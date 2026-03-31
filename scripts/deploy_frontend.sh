#!/bin/bash

set -e

echo "🚀 FRONTEND DEPLOY START"

cd /opt/uniforma/frontend

echo "🧹 Removing .next..."
rm -rf .next

echo "🧹 Clearing Next cache..."
rm -rf node_modules/.cache

echo "📦 Installing deps..."
npm install

echo "🏗 Building..."
npm run build

echo "🔁 Restarting PM2..."
pm2 restart uniforma-frontend || pm2 start /opt/uniforma/frontend/ecosystem.config.js --only uniforma-frontend

echo "💾 Saving PM2..."
pm2 save

echo "✅ FRONTEND DEPLOY DONE"
