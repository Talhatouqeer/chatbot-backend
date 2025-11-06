# 🤖 Chatbot Application Backend

A production-ready AI chatbot backend built with FastAPI, PostgreSQL, and Google Gemini AI. Supports multi-language conversations (English & Roman Urdu) and image analysis.

## ✨ Features

- 🔐 Complete Authentication (Register, Login, JWT, Password Reset)
- 💬 AI Chat in English and Roman Urdu
- 📸 Image Upload and Analysis
- 📧 Email Service (SendGrid)
- 🗄️ PostgreSQL Database
- 🚀 Production Ready

---

## 📁 Project Structure

```
chatbot_app_backend/
├── app/
│   ├── models/           # Database models (User, Chat)
│   ├── routes/           # API endpoints (auth, chat)
│   ├── schemas/          # Pydantic validation schemas
│   ├── services/         # Business logic (auth, email, AI)
│   ├── utils/            # Security & validators
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration
│   ├── database.py       # Database setup
│   └── dependencies.py   # JWT authentication
│
├── alembic/              # Database migrations
├── uploads/              # User uploaded images
├── requirements.txt      # Python dependencies
├── alembic.ini          # Alembic configuration
├── render.yaml          # Render deployment config
└── DOT_ENV_FILE.txt     # Environment variables template
```

---

## 🚀 Quick Setup

### Step 1: Install Dependencies

```bash
# Activate virtual environment (if you have one)
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 2: Setup Environment Variables

**Create `.env` file in the root directory:**

```bash
# Rename DOT_ENV_FILE.txt to .env
# Windows:
rename DOT_ENV_FILE.txt .env
# Mac/Linux:
mv DOT_ENV_FILE.txt .env
```

**Then edit `.env` and update:**

1. **DATABASE_URL** - Change `password` to your PostgreSQL password
2. **SENDGRID_API_KEY** - Get from https://sendgrid.com/ (free account)
3. **FROM_EMAIL** - Your verified email in SendGrid
4. **GEMINI_API_KEY** - Get from https://makersuite.google.com/app/apikey (free)

**Note:** SECRET_KEY is already provided in the file (secure and ready to use)

### Step 3: Create Database

```bash
# Create PostgreSQL database
createdb chatbot_db

# Or using psql:
psql -U postgres
CREATE DATABASE chatbot_db;
\q
```

### Step 4: Run Database Migrations

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### Step 5: Start Server

```bash
uvicorn app.main:app --reload
```

**Server will run at:** http://localhost:8000

**API Documentation:** http://localhost:8000/docs

---

## 🔑 Getting API Keys

### SendGrid (Email Service - FREE)
1. Go to https://sendgrid.com/
2. Sign up for free account
3. Go to Settings → API Keys
4. Click "Create API Key"
5. Copy the key to your `.env` file as `SENDGRID_API_KEY`
6. Verify a sender email in Settings → Sender Authentication

**Free Tier:** 100 emails/day

### Google Gemini (AI Service - FREE)
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Get API Key" or "Create API Key"
4. Copy the key to your `.env` file as `GEMINI_API_KEY`

**Free Tier:** 60 requests/minute, 1500 requests/day

---

## 🔌 API Endpoints

### Public Routes (No Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API root |
| GET | `/health` | Health check |
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login & get JWT token |
| POST | `/api/auth/forgot-password` | Request password reset |
| POST | `/api/auth/reset-password` | Reset password with token |

### Protected Routes (Requires JWT Token)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/me` | Get current user info |
| GET | `/api/auth/verify-token` | Verify token validity |
| POST | `/api/chat/message` | Send text message to AI |
| POST | `/api/chat/upload-image` | Upload image with message |
| GET | `/api/chat/history` | Get chat history |
| GET | `/api/chat/history/{id}` | Get specific chat |
| DELETE | `/api/chat/history/{id}` | Delete specific chat |
| DELETE | `/api/chat/history` | Delete all chats |

---

## 🧪 Testing the API

### Using Swagger UI (Easiest)

1. Start the server: `uvicorn app.main:app --reload`
2. Open: http://localhost:8000/docs
3. Try these steps:
   - **Register**: POST `/api/auth/register`
   - **Login**: POST `/api/auth/login` (copy the `access_token`)
   - **Authorize**: Click the 🔒 Authorize button, paste: `Bearer YOUR_TOKEN`
   - **Chat**: POST `/api/chat/message` with your message

### Test Messages

**English:**
```json
{"message": "Hello! How are you?"}
{"message": "What's the weather like today?"}
```

**Roman Urdu:**
```json
{"message": "Assalam o Alaikum"}
{"message": "Aap kaise hain?"}
{"message": "Mujhe Pakistani food recipes batayein"}
```

---

## 📝 Environment Variables

Your `.env` file should contain:

```env
# Database
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/chatbot_db

# JWT (Already provided - no need to change)
SECRET_KEY=X8Kp9mN2vB5qW7rT4jL6hD3fG8sA1cZ9yU4xE7nM5bV2wR6tQ3pK8oJ1iH4gF7e

# Email Service (Get from sendgrid.com)
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=your-verified-email@example.com

# AI Service (Get from makersuite.google.com)
GEMINI_API_KEY=your-gemini-api-key

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

---

## 🗄️ Database Schema

### Tables

1. **users**
   - id (UUID)
   - email (unique)
   - username (unique)
   - hashed_password
   - is_active
   - created_at, updated_at

2. **chat_history**
   - id (UUID)
   - user_id (foreign key)
   - message
   - response
   - message_type (text/image)
   - image_url
   - created_at

3. **password_reset_tokens**
   - id (UUID)
   - user_id (foreign key)
   - token (unique)
   - expires_at
   - is_used
   - created_at

---

## 🚀 Deploy to Render

### Prerequisites
- GitHub account
- Render account (render.com)
- Push your code to GitHub

### Steps

1. **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

2. **Deploy on Render**
   - Go to https://dashboard.render.com/
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will read `render.yaml` automatically
   - Click "Apply"

3. **Add Environment Variables in Render**
   - Go to your web service → Environment
   - Add:
     - `SENDGRID_API_KEY`
     - `FROM_EMAIL`
     - `GEMINI_API_KEY`
     - `FRONTEND_URL` (your frontend URL)

4. **Done!** Your API will be live at: `https://your-app.onrender.com`

---

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check if PostgreSQL is running
psql -U postgres -l

# Verify DATABASE_URL in .env
# Make sure password is correct
```

### Module Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Migration Errors
```bash
# Reset migrations (CAUTION: deletes data)
alembic downgrade base
alembic upgrade head
```

### SendGrid Email Not Sending
- Verify API key is correct
- Verify sender email is verified in SendGrid dashboard
- Check SendGrid activity feed for errors

### Gemini API Error
- Verify API key is correct
- Check quota at https://makersuite.google.com
- Make sure you're using the correct model names

---

## 📦 Dependencies

Main packages used:
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **PostgreSQL** - Database (psycopg2-binary)
- **Pydantic** - Data validation
- **python-jose** - JWT tokens
- **passlib** - Password hashing
- **SendGrid** - Email service
- **google-generativeai** - Gemini AI
- **python-multipart** - File uploads
- **aiofiles** - Async file handling
- **Pillow** - Image processing

---

## 🔒 Security Features

- ✅ Password hashing (bcrypt)
- ✅ JWT authentication
- ✅ Token expiration (7 days)
- ✅ One-time password reset tokens (1 hour expiry)
- ✅ Input validation
- ✅ SQL injection prevention
- ✅ CORS configuration
- ✅ File type & size validation

---

## 📊 Tech Stack

- **Backend:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Auth:** JWT (JSON Web Tokens)
- **Email:** SendGrid
- **AI:** Google Gemini
- **Deployment:** Render

---

## ✅ What's Included

- [x] User registration with validation
- [x] Login with JWT tokens
- [x] Password reset via email
- [x] AI chat (English & Roman Urdu)
- [x] Image upload & analysis
- [x] Chat history persistence
- [x] Email notifications
- [x] Database migrations
- [x] API documentation (Swagger)
- [x] Production-ready configuration
- [x] Deployment setup (Render)

---

## 🎯 Next Steps After Setup

1. ✅ Test all endpoints in Swagger UI
2. 🎨 Build React frontend
3. 🌐 Deploy to Render
4. 📱 Add mobile app (optional)
5. 📊 Add analytics (optional)

---

## 📞 Support

For issues:
1. Check error messages in terminal
2. Verify environment variables
3. Check API documentation at `/docs`
4. Review troubleshooting section above

---

## 📄 License

MIT License

---

**Built with FastAPI, PostgreSQL, and Google Gemini AI** ❤️
