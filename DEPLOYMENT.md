# BAROS Deployment Guide

Both the **backend** (FastAPI) and **frontend** (React/Vite) live in the same GitHub repo under `backend/` and `frontend/` subdirectories.

- **Backend → Northflank** (Docker)
- **Frontend → Render** (Static Site)

---

## Step 1 – Push to GitHub

Make sure everything is committed and pushed to your GitHub repo before starting.

```bash
git add -A
git commit -m "feat: finalize end-to-end MVP ..."
git push origin main
```

---

## Step 2 – Deploy Backend on Northflank (Docker)

### 2.1 – Create a Northflank Account
Go to [northflank.com](https://northflank.com) and sign up.

### 2.2 – Create a new Project
- Click **New Project** → give it a name like `baros`

### 2.3 – Create a Combined Service (Docker)
1. Inside your project, click **New Service** → **Combined Service**
2. Connect your **GitHub** account and select your BAROS repo
3. Set **Root Directory** to `backend`
4. Northflank will detect the `Dockerfile` automatically
5. Set **Port** to `8000`

### 2.4 – Set Environment Variables (Secret Group)
In Northflank, go to **Secrets** → **New Secret Group** and add all the following:

| Variable | Value |
|---|---|
| `DATABASE_URL` | Your PostgreSQL connection string (asyncpg format) |
| `SECRET_KEY` | A long random string for JWT signing |
| `WALLET_ENCRYPTION_KEY` | Your Fernet encryption key (base64) |
| `SOLANA_RPC_URL` | `https://api.devnet.solana.com` (or mainnet) |
| `SOLANA_ESCROW_PROGRAM_ID` | Your Anchor program address |
| `SOLANA_USDC_MINT` | Devnet USDC mint address |
| `UNDERDOG_API_KEY` | Your Underdog Protocol API key |
| `GOOGLE_CLIENT_ID` | Your Google OAuth client ID |
| `BREVO_API_KEY` | Your Brevo (Sendinblue) email API key |
| `CLOUDINARY_CLOUD_NAME` | Your Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Your Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Your Cloudinary API secret |
| `FRONTEND_URL` | Your Render frontend URL (e.g. `https://baros.onrender.com`) |

> **Important**: `DATABASE_URL` must use the **asyncpg** driver format:
> `postgresql+asyncpg://user:password@host:5432/dbname`
>
> Northflank has a managed PostgreSQL add-on. Enable **PostGIS** extension after creation by running:
> ```sql
> CREATE EXTENSION IF NOT EXISTS postgis;
> ```

### 2.5 – Link the Secret Group to your Service
In your Combined Service settings → **Environment** → attach the Secret Group you just created.

### 2.6 – Deploy
Click **Deploy** and watch the build logs. Your backend will be live at:
`https://<your-service>.northflank.app`

---

## Step 3 – Deploy Frontend on Render (Static Site)

### 3.1 – Create a Render Account
Go to [render.com](https://render.com) and sign up.

### 3.2 – Create a New Static Site
1. Click **New** → **Static Site**
2. Connect your GitHub repo
3. Configure the build:

| Setting | Value |
|---|---|
| **Root Directory** | `frontend` |
| **Build Command** | `npm install && npm run build` |
| **Publish Directory** | `dist` |

### 3.3 – Set Environment Variables
In Render, go to **Environment** and add:

| Variable | Value |
|---|---|
| `VITE_API_URL` | Your Northflank backend URL + `/api/v1` (e.g. `https://baros-abc.northflank.app/api/v1`) |
| `VITE_CLOUDINARY_CLOUD_NAME` | Your Cloudinary cloud name |
| `VITE_CLOUDINARY_UPLOAD_PRESET` | Your Cloudinary unsigned upload preset |
| `VITE_GOOGLE_CLIENT_ID` | Your Google OAuth client ID |

> **Important**: Vite only embeds env variables that start with `VITE_`. These are baked into the static build at compile time.

### 3.4 – Add a Redirect Rule for SPA Routing
Since BAROS uses client-side routing (`react-router-dom`), direct URL access (e.g. `/dashboard/jobs`) would 404 on a static host. Fix this:

In Render, go to **Redirects/Rewrites** → **Add Rule**:

| Source | Destination | Action |
|---|---|---|
| `/*` | `/index.html` | Rewrite |

### 3.5 – Deploy
Click **Create Static Site** and wait. Your frontend will be live at:
`https://baros.onrender.com` (or whatever name you pick)

---

## Step 4 – Update Google OAuth Allowed Origins

Go to [console.cloud.google.com](https://console.cloud.google.com):
1. APIs & Services → Credentials → your OAuth 2.0 Client ID
2. Add your Render URL to **Authorized JavaScript origins**:
   - `https://baros.onrender.com`
3. Add your backend URL to **Authorized redirect URIs** (if applicable)

---

## Step 5 – Final Checklist

- [ ] Backend deployed and `/docs` is reachable at your Northflank URL
- [ ] Frontend deployed and loads at your Render URL
- [ ] `FRONTEND_URL` env var set on the backend so CORS allows the Render domain
- [ ] `VITE_API_URL` env var set on the frontend pointing to the backend
- [ ] Google OAuth origins updated to include both URLs
- [ ] PWA: Visit your Render URL in Chrome → you should see the "Install App" prompt in the address bar

---

## PWA Installation

BAROS is now a fully installable **Progressive Web App**. Users can install it to their phone or desktop:

- **Android/Chrome**: Tap the "Add to Home Screen" banner or the install button in the address bar
- **iOS/Safari**: Tap Share → Add to Home Screen
- **Desktop Chrome**: Click the install icon in the address bar

The app will open in standalone mode (no browser chrome), with the BAROS icon and theme color.
