#!/bin/bash

cd /opt/uniforma/frontend || exit

echo "🚀 Starting frontend clean..."

pm2 restart uniforma-frontend || pm2 start ecosystem.config.js --only uniforma-frontend

pm2 save

echo "✅ Frontend running"
