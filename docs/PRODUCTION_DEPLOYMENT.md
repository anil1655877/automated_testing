# 🚀 Production Deployment & Architecture Guide

This guide details the folder layouts, architecture workflows, security, and production steps to deploy and run the AI-Powered automated testing platform.

---

## 🏗️ Platform Folder Structure

```
Automation_Testing/
├── 📁 qa-backend-node/               # 🟢 Node.js Playwright Backend
│   ├── 📁 public/                    # Static routes (screenshots, videos, local uploads)
│   ├── 📄 db.js                      # Sequelize connection (SQLite fallback / Postgres)
│   ├── 📄 server.js                  # Express API Server and Socket.IO
│   ├── 📄 test-engine.js             # Playwright automation crawler
│   ├── 📄 package.json               # Backend dependencies
│   ├── 📄 Dockerfile                 # Official Microsoft Playwright Image Docker container
│   └── 📄 .env.example               # Environment variables example
│
├── 📁 qa-frontend/                   # ⚛️ React Vite Frontend Dashboard
│   ├── 📁 src/
│   │   ├── 📄 App.jsx                # Redesigned premium Dashboard & Tab uploaders
│   │   ├── 📄 index.css              # Custom styling
│   │   └── 📄 main.jsx               # Entrypoint file
│   ├── 📄 package.json               # Frontend dependencies
│   └── 📄 vite.config.js             # Vite configurations (Proxies points to port 5000)
│
└── 📄 docker-compose-platform.yml    # Combined database, backend & frontend orchestrator
```

---

## ⚡ Local Setup & Execution Guide

### Prerequisites
- Node.js v20+
- npm v10+

### 1. Set Up and Run the Backend
```bash
cd qa-backend-node
npm install

# Run the dev server
npm run dev
```
*By default, the server runs on port `5000` and creates a local `database.sqlite` file in the directory.*

### 2. Set Up and Run the Frontend
In a new terminal window:
```bash
cd qa-frontend
npm install

# Run Vite dev server
npm run dev
```
*The Vite development server runs on port `5173` and proxies API requests `/api` to the backend on port `5000`.*

---

## 🐳 Docker Deployment Setup

For containerized production workloads, use the configured orchestrator to spin up a PostgreSQL instance, backend engine (with pre-built browsers), and frontend:

```bash
# Build and launch all services in background
docker-compose -f docker-compose-platform.yml up -d --build

# View logs
docker-compose -f docker-compose-platform.yml logs -f

# Shut down and clean data volumes
docker-compose -f docker-compose-platform.yml down -v
```

---

## ⚙️ Environment Configurations

Rename `.env.example` in `qa-backend-node` to `.env` to configure properties:

```ini
PORT=5000
DATABASE_URL=postgres://user:pass@host:5432/dbname
DATABASE_SSL=false
```

---

## 🛡️ Security Implementations
- **Zip-Slip Attack Shield:** Files unpacked inside the ZIP parser are validated to ensure they remain within the target sandbox directories.
- **Path Sanitization:** Reconstructed uploaded folder structures utilize strict root boundaries to prevent directories climbing.
- **Auto-Deletion:** Temporary folder files and unpacked artifacts are cleared immediately after a scanning job finishes execution.
