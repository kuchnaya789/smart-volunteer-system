# smart-volunteer-system

## Deploy on Vercel (Frontend + Backend Serverless)

This repository is structured as a monorepo:

- `frontend`: React + Vite app
- `backend`: Flask API deployed as a Vercel Python serverless function

### 1) Push to GitHub

Push the repository to GitHub first, then create two Vercel projects from the same repo.

### 2) Deploy frontend on Vercel

1. Import the repository in Vercel.
2. Set **Root Directory** to `frontend`.
3. Build command: `npm run build`
4. Output directory: `dist`
5. Add environment variable:
	- `VITE_API_BASE_URL` = `https://<your-backend-domain>/api`
6. Deploy.

### 3) Deploy backend on Vercel (serverless)

1. Create another Vercel project from the same repository.
2. Set **Root Directory** to `backend`.
3. Vercel will use `backend/vercel.json` and `backend/api/index.py`.
4. Add environment variables:
	- `MONGO_URI`
	- `JWT_SECRET`
	- `ADMIN_REGISTER_SECRET` (optional, only if you need admin self-registration)
	- `CORS_ORIGINS` (comma-separated allowed origins)
	  - Example: `https://<your-frontend-domain>,http://localhost:5173`
5. Deploy.

### 4) Verify deployment

1. Open backend health endpoint:
	- `https://<your-backend-domain>/api/health`
2. Open frontend URL and test login/register/task APIs.
3. Confirm browser network requests are sent to backend Vercel URL, not localhost.