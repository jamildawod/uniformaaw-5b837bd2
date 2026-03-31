#!/bin/bash

echo "🚀 DEPLOY ADMIN START"

cd /opt/uniforma/admin || exit

echo "📦 npm install"
npm install || exit

echo "🏗 build"
npm run build || exit

echo "🛑 stop old"
pm2 delete uniforma-admin 2>/dev/null

echo "▶ start admin"
pm2 start npm --name "uniforma-admin" -- start

sleep 2

echo "🔍 check port 3001"
ss -tlnp | grep 3001 || echo "❌ app not listening"

echo "🔄 reload nginx"
sudo systemctl reload nginx

echo "📊 pm2 list"
pm2 list

echo "✅ DONE"
