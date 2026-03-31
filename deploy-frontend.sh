#!/bin/bash

echo "🚀 Deploy frontend..."

cd /opt/uniforma/frontend || exit

echo "📥 Pull latest code..."
git pull origin main

echo "🧹 Clean old build..."
rm -rf .next
rm -rf node_modules/.cache

echo "📦 Install deps..."
npm install

echo "🏗 Build..."
npm run build

echo "🔁 Restart app..."
pm2 restart uniforma-frontend || pm2 start /opt/uniforma/frontend/ecosystem.config.js --only uniforma-frontend
pm2 save

echo "🌐 Reload nginx..."
systemctl reload nginx

echo "✅ DONE"
