# Odoo-MailMunch

Email-to-Purchase-Order automation for Odoo 18 Enterprise.

Upload vendor emails, let MailMunch parse them into Purchase Orders, review with one click, and push directly to Odoo. Track receipts and deliveries from the same dashboard.

## Features

- **Three email inputs** — M365 mailbox polling, webhook-based forwarding, direct upload/paste
- **Smart parsing** — Extracts line items, quantities, prices, and vendor info from emails and attachments (PDF, Excel, HTML)
- **Auto-matching** — Fuzzy matches vendors and products against your Odoo catalog
- **Human-in-the-loop** — Review and edit parsed POs before pushing to Odoo
- **Receipt tracking** — Track deliveries with carrier links (UPS, FedEx, USPS, DHL), partial and full receive
- **Sales Order linking** — Link POs to SOs for job-based cost tracking
- **Ignore rules** — Auto-filter spam and irrelevant emails
- **2FA support** — Authenticate through Odoo with TOTP

## Prerequisites

- Docker and Docker Compose
- Odoo 18.0+ Enterprise instance
- (Optional) Microsoft 365 tenant for mailbox polling

## Quick Start

```bash
# Clone the repo
git clone https://github.com/yourusername/odoo-mailmunch.git
cd odoo-mailmunch

# Generate secrets and configure
cp .env.example .env

# Generate FERNET_KEY:
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate SECRET_KEY:
python3 -c "import secrets; print(secrets.token_hex(32))"

# Paste both values into .env, then start:
docker compose up -d
```

Open http://localhost:8000 and log in with your Odoo credentials.

## Configuration

### Environment Variables (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `FERNET_KEY` | Yes | Fernet encryption key for secrets at rest |
| `SECRET_KEY` | Yes | JWT signing secret (min 32 bytes) |
| `DATABASE_URL` | No | PostgreSQL connection (default: internal postgres service) |
| `REDIS_URL` | No | Redis connection (default: internal redis service) |

### M365 Mailbox Polling

Configure via the Settings page after login:
1. Register an app in Azure AD
2. Grant `Mail.Read` permission (read-only)
3. Enter Tenant ID, Client ID, and Client Secret in Settings
4. Set the mailbox folder to monitor (default: Inbox)

### Email Forwarding

Forward vendor emails to the webhook endpoint:
```
POST http://your-server:8000/api/emails/inbound-email
Content-Type: application/json

{"sender": "vendor@acme.com", "subject": "Order Confirm", "body_plain": "..."}
```

## Architecture

```
Docker Compose
├── mailmunch    (FastAPI + React SPA)
├── worker       (ARQ background jobs)
├── postgres     (PostgreSQL 16)
└── redis        (Redis 7)
```

- **Backend:** Python 3.12, FastAPI, SQLAlchemy (async), ARQ
- **Frontend:** React 18, TypeScript, Vite, TailwindCSS
- **Auth:** JWT + Fernet encryption, proxied through Odoo JSON-RPC

### Background Workers

| Job | Schedule | Description |
|-----|----------|-------------|
| M365 Poller | Every 5 min | Polls configured M365 mailbox for new emails |
| Email Processor | Every 5 min | Classifies, parses, and creates PO drafts |
| PO Status Sync | Every 15 min | Syncs PO statuses from Odoo |
| Cache Refresh | Every 6 hrs | Refreshes product and vendor caches |

## Development

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
FERNET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())") \
SECRET_KEY=dev-secret \
pytest tests/ -v

# Frontend
cd frontend
npm install
npm run dev
```

## License

MIT - see [LICENSE](LICENSE)
