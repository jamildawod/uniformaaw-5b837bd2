const path = require("path");

module.exports = {
  apps: [
    {
      name: "uniforma-frontend",
      script: "node_modules/next/dist/bin/next",
      args: "start -p 3000",
      cwd: path.resolve(__dirname),
      env: {
        NODE_ENV: "production",
        PORT: 3000,
      },
      watch: false,
      autorestart: true,
      max_restarts: 5,
      restart_delay: 3000,
    },
  ],
};
