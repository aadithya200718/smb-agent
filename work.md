# Deployment Guide: From Scratch to Production

This guide walks you through preparing your repository, pushing your local project to GitHub, and deploying your React/Vite Frontend to Vercel and your FastAPI Backend to Render.

## Prerequisites
- A GitHub account.
- A Vercel account (linked to your GitHub).
- A Render account (linked to your GitHub).
- Git installed on your local machine.

## Step 1: Secure Secrets & Set up `.gitignore`

Before pushing to GitHub, you **must never commit your `.env` files**. Environment variables contain sensitive API keys (like your OpenAI/Groq keys, MongoDB URIs, and Twilio secrets).

1. **Create the `.gitignore` file**
   Ensure your root directory (`d:\agentic hackathon`) has a file exactly named `.gitignore`. It should contain the following lines to prevent caching, build folders, and secret files from being uploaded to GitHub:

   ```txt
   # Environment variables
   .env
   .env.local
   .env.production
   backend/.env
   frontend/.env
   
   # Node dependencies
   node_modules/
   frontend/node_modules/
   
   # Python environments
   backend/venv/
   venv/
   env/
   
   # Build outputs
   dist/
   frontend/dist/
   build/
   
   # Python cache
   __pycache__/
   *.pyc
   
   # OS generated files
   .DS_Store
   ```

2. **Verify `.env` isolation**
   Ensure you have your environment keys safely stored locally (e.g. `backend/.env` and `frontend/.env`). Because these are ignored by git, you will manually provide them to Render and Vercel in their respective dashboards later.

---

## Step 2: Push Project to GitHub

1. **Initialize Git**
   Open your terminal in the root directory (`d:\agentic hackathon`) and run:
   ```bash
   git init
   ```

2. **Commit your code**
   Now that `.gitignore` is correctly protecting your secrets, add and commit the project files:
   ```bash
   git add .
   git commit -m "Initial commit for deployment"
   ```

3. **Create a new Repository on GitHub**
   - Go to [GitHub](https://github.com/new) and create a new repository (name it e.g., `agentic-hackathon`).
   - Do NOT check "Initialize this repository with a README" (since you already have local files).

4. **Push Local Code to GitHub**
   Link your local repository to GitHub and push:
   ```bash
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

---

## Step 3: Deploy FastAPI Backend on Render

Deploying the Backend first is recommended so you can supply the resulting live API URL to your Frontend later.

1. **Log in to Render**
   Go to [Render.com](https://render.com) and log in.

2. **Create a New Web Service**
   - Click the **New +** button and select **Web Service**.
   - Select **Build and deploy from a Git repository**.
   - Connect your GitHub account and select your `agentic-hackathon` repository.

3. **Configure the Service**
   - **Name**: `agentic-backend`
   - **Root Directory**: `backend` (Important! This tells Render where your Python code is).
   - **Environment**: Python 3
   - **Region**: (Choose closest to your users)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables (.env equivalents)**
   Because your `.env` file wasn't pushed to GitHub, you need to add your secrets manually into Render.
   - Scroll down to the **Environment Variables** section and click **Add Environment Variable**.
   - Open your local `backend/.env` file.
   - For every key-value pair in that file, create a corresponding row in Render. 
     - *Example:*
       - Key: `MONGODB_URI` | Value: `mongodb+srv://user:pass@cluster...`
       - Key: `GROQ_API_KEY` | Value: `gsk_abc123...`
       - Key: `ENVIRONMENT` | Value: `production`

5. **Deploy**
   - Click **Create Web Service**.
   - Wait for the build and deployment to finish. Once done, Render will give you a live URL (e.g., `https://agentic-backend-xxxx.onrender.com`).
   - **Copy this URL**. You will need it for the frontend deployment.

---

## Step 4: Deploy React Frontend on Vercel

1. **Log in to Vercel**
   Go to [Vercel.com](https://vercel.com) and log in.

2. **Create a New Project**
   - Click **Add New** > **Project**.
   - Import your GitHub repository (`agentic-hackathon`).

3. **Configure the Project**
   - **Project Name**: `agentic-frontend`
   - **Framework Preset**: Vercel should auto-detect **Vite**.
   - **Root Directory**: Click "Edit" and change it to `frontend` (Important!).
   
4. **Build and Output Settings** (Leave Default)
   - Build Command: `vite build`
   - Output Directory: `dist`
   - Install Command: `npm install` (or `yarn install` / `pnpm install` depending on what you use).

5. **Add Environment Variables (.env equivalents)**
   Because your `frontend/.env` file wasn't pushed to GitHub, add your frontend environment variables directly in Vercel.
   - Expand the **Environment Variables** section.
   - **Crucially**, add your deployed backend API URL you copied from Render:
     - **Name**: `VITE_API_URL`
     - **Value**: `https://agentic-backend-xxxx.onrender.com` (No trailing slash)
   - Add any other keys that exist in your `frontend/.env`.

6. **Deploy**
   - Click **Deploy**. Vercel will build your frontend application.
   - *Note:* We have already added a `vercel.json` file in your `frontend` directory to ensure that React Router works smoothly on refresh without giving a 404 error.

7. **Visit your live site!**
   - Once deployed, Vercel will provide you with a live domain (e.g., `https://agentic-frontend.vercel.app`).
   - Your frontend will now securely communicate with your live Render backend!
