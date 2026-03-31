#!/bin/bash

echo "🚀 Fixing Next.js build..."

cd /opt/uniforma/frontend || exit

echo "🧹 Cleaning..."
rm -rf .next
rm -rf node_modules/.cache

echo "📦 Installing..."
npm install

echo "🏗 Building..."
npm run build

echo "🔁 Restarting..."
pm2 restart uniforma-frontend 2>/dev/null || pm2 start ecosystem.config.js --only uniforma-frontend 2>/dev/null
pm2 save 2>/dev/null

echo "✅ DONE"
