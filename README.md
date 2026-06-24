# BAROS: Verifiable Trust for Local Work

BAROS is a hyper-local services marketplace with a cryptographically secured trust and escrow layer. It solves the dual-sided trust deficit in the informal economy:
- **Clients** hold money securely in an on-chain escrow until the job is completed to satisfaction.
- **Providers** get guaranteed payment without risk of non-payment, and build permanent, verifiable reputation.

All blockchain interactions are hidden from the user, providing a Web2-like seamless experience (via mobile or PWA) while maintaining Web3 guarantees.

> Demo : https://drive.google.com/file/d/142SPSW5hQhXhXTih6y6WjjrJDyXC0_xb/view
---

## 🏗 Architecture

BAROS operates on a split architecture:

- **Frontend**: A Progressive Web App (PWA) built with **React**, **Vite**, **TypeScript**, and **TailwindCSS**. Configured for deployment on **Render** (or Vercel). Uses `react-query` for server state and `zustand` for local auth state. Includes `react-leaflet` for hyper-local Neighborhood Maps.
- **Backend**: A **FastAPI** Python application acting as the orchestrator. Uses **PostgreSQL** + **PostGIS** for database and geospatial proximity queries. Integrates natively with the Solana blockchain using Anchor and `solders`. Configured for deployment on **Northflank** (or Render).
- **Blockchain**: A custom **Solana Anchor Smart Contract** deployed on Devnet that handles atomic escrow funding, releasing, and refunding.
- **Reputation**: Uses the **Underdog Protocol API** to mint compressed NFTs (cNFTs) to provider wallets as "Vouches", acting as on-chain verifiable reputation.

---

## 🚀 Environment Setup

### 1. Backend Setup

The backend relies on PostgreSQL, Solana, and external APIs.

```bash
cd backend
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

**Required Environment Variables (`backend/.env`)**:
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5444/baros

# Security
SECRET_KEY=your_super_secret_jwt_key
WALLET_ENCRYPTION_KEY=a_fernet_encryption_key_base64_encoded

# Solana & Underdog
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_ESCROW_PROGRAM_ID=H3ETmNRWqkfFZmiZio2KsKpuntZ1X3awUwY8QUiGVAqA
SOLANA_USDC_MINT=4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU # Devnet USDC
UNDERDOG_API_KEY=your_underdog_api_key

# OAuth (Google)
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
```

**Run Backend Server**:
```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

The frontend connects to the backend and external services like Cloudinary.

```bash
cd frontend
npm install
```

**Required Environment Variables (`frontend/.env`)**:
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_CLOUDINARY_CLOUD_NAME=your_cloudinary_name
VITE_CLOUDINARY_UPLOAD_PRESET=your_preset
VITE_GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
```

**Run Frontend Server**:
```bash
npm run dev
```

---

## 💡 Key Features

### 1. Escrow Smart Contract Integration
The backend securely orchestrates SOL and USDC transactions on behalf of users. When a job is funded, USDC is transferred into a Program Derived Address (PDA). The backend signs the transaction using the client's decrypted base58 keypair.

### 2. Non-Blocking Vouching (cNFTs)
Minting reputation NFTs via the Underdog Protocol can be slow during Devnet congestion. BAROS uses `asyncio.create_task` to handle minting optimistically in the background, keeping the user interface lightning fast.

### 3. Hyper-Local Discoverability
BAROS utilizes PostgreSQL PostGIS features (`ST_DWithin`, `ST_DistanceSphere`) to match clients with providers inside a specified radius, rendering the results visually on a `react-leaflet` map.

### 4. Rich Media & Communication
Users can post jobs with images, showcase service portfolios, and exchange photo attachments within the secure Contract Room messaging system via Cloudinary.

### 5. Google OAuth + Profile Sync
Frictionless onboarding using Google OAuth, which automatically pulls and syncs the user's Google profile picture to their BAROS account.

---
