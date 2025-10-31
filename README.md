# 🚀 Marketing Automation Platform

A comprehensive, AI-powered marketing automation platform built for startups and small businesses. Streamline your email campaigns, social media management, and customer engagement with cutting-edge AI technology.

## ✨ Features

### 🤖 AI-Powered Content Generation
- Generate email campaigns, social media posts, blog content, and ad copy using OpenAI GPT-4 or Anthropic Claude
- Optimize email subject lines for better open rates
- Create multiple variations with different tones and styles

### 📧 Email Marketing
- Create and manage email campaigns
- Schedule campaigns for optimal send times
- Track opens, clicks, and conversions
- Personalize content with dynamic variables
- SendGrid integration for reliable delivery

### 🔄 Workflow Automation
- Visual workflow builder
- Trigger-based automations (signups, purchases, page visits)
- Conditional logic and branching
- Wait steps and time delays
- Automated tagging and segmentation

### 📊 Analytics & Reporting (NEW ✨)
- **Real-time interactive charts** with Recharts
- Campaign performance timeline visualization
- Lead growth tracking with cumulative metrics
- Engagement heatmap by day and hour
- AI-powered insights and recommendations
- Channel-wise ROI tracking
- Period comparison (7, 14, 30, 90 days)
- Recent activity feed

### 👥 Lead Management & CRM (NEW ✨)
- **Full CRUD operations** for leads
- Lead scoring and prioritization (Hot/Warm/Cold)
- Activity tracking and logging
- Custom fields and tags
- Advanced search and filtering
- Bulk lead import
- Lead statistics and summaries
- Hot leads identification (score >= 70)

### 📱 Social Media Management
- Schedule posts across Facebook, Instagram, Twitter
- Unified content calendar
- Performance analytics
- AI-generated captions

## 🏗️ Tech Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL
- **Cache:** Redis
- **Task Queue:** Celery
- **AI:** OpenAI API, Anthropic API
- **Email:** SendGrid
- **Authentication:** JWT

### Frontend
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **Charts:** Recharts (Line, Area, Bar charts)
- **State Management:** Zustand
- **API Client:** Axios + React Query
- **Routing:** React Router v6

### Infrastructure
- **Containerization:** Docker + Docker Compose
- **Database:** PostgreSQL 15
- **Cache:** Redis 7

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose installed
- (Optional) Node.js 20+ and Python 3.11+ for local development

### Quick Start with Docker

1. **Clone the repository**
```bash
git clone <repository-url>
cd automaketing
```

2. **Set up environment variables**

Backend:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env and add your API keys
```

Frontend:
```bash
cp frontend/.env.example frontend/.env
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
# (First time setup - create tables)

# Start the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env

# Start development server
npm run dev
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 🔑 Key API Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get tokens
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/refresh` - Refresh access token

#### AI Content
- `POST /api/ai/generate` - Generate marketing content
- `POST /api/ai/optimize-subject` - Optimize email subject lines
- `POST /api/ai/social-captions` - Generate social media captions

#### Campaigns
- `POST /api/campaigns/` - Create email campaign
- `GET /api/campaigns/` - List all campaigns
- `GET /api/campaigns/{id}` - Get campaign details
- `POST /api/campaigns/{id}/send` - Send campaign
- `POST /api/campaigns/{id}/track/open` - Track email open
- `POST /api/campaigns/{id}/track/click` - Track email click

#### Leads (NEW ✨)
- `POST /api/leads/` - Create new lead
- `GET /api/leads/` - List leads (with filtering)
- `GET /api/leads/{id}` - Get lead details
- `PUT /api/leads/{id}` - Update lead
- `DELETE /api/leads/{id}` - Delete lead
- `GET /api/leads/{id}/activities` - Get lead activities
- `POST /api/leads/{id}/activities` - Add activity
- `GET /api/leads/stats/summary` - Get leads summary
- `POST /api/leads/import` - Bulk import leads

#### Analytics (NEW ✨)
- `GET /api/analytics/overview` - Get overview metrics
- `GET /api/analytics/campaigns/performance` - Campaign performance
- `GET /api/analytics/campaigns/timeline` - Campaign timeline data
- `GET /api/analytics/leads/growth` - Lead growth over time
- `GET /api/analytics/activities/recent` - Recent activities
- `GET /api/analytics/engagement/heatmap` - Engagement heatmap
- `GET /api/analytics/insights` - AI-powered insights

#### Workflows (NEW ✨)
- `POST /api/workflows/` - Create workflow
- `GET /api/workflows/` - List workflows
- `GET /api/workflows/{id}` - Get workflow details
- `PUT /api/workflows/{id}` - Update workflow
- `DELETE /api/workflows/{id}` - Delete workflow
- `POST /api/workflows/{id}/activate` - Activate workflow
- `POST /api/workflows/{id}/deactivate` - Deactivate workflow
- `POST /api/workflows/{id}/trigger` - Manually trigger workflow
- `GET /api/workflows/templates/list` - Get workflow templates

## 🔑 Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/marketing_automation

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# AI APIs (Optional - platform works without them in demo mode)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Email (Optional - simulated if not configured)
SENDGRID_API_KEY=SG.your-sendgrid-key

# Social Media (Optional)
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
```

## 📖 Usage Guide

### 1. Create an Account
Visit http://localhost:3000/register and create your account.

### 2. Generate AI Content
- Navigate to "AI Content" in the menu
- Select content type (Email, Social Media, Blog, Ad)
- Enter your target audience and main message
- Choose tone and style
- Click "Generate with AI"

### 3. Create Email Campaign
- Go to "Campaigns"
- Click "New Campaign"
- Design your email or use AI-generated content
- Select recipients
- Schedule or send immediately

### 4. View Analytics
- Dashboard shows overview of all metrics
- Campaign-specific analytics available in campaign detail view
- AI provides optimization suggestions

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React)                     │
│  ┌─────────┐  ┌──────────┐  ┌────────────────────┐    │
│  │Dashboard│  │Campaigns │  │ AI Content Gen     │    │
│  └─────────┘  └──────────┘  └────────────────────┘    │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP/REST
┌─────────────────────▼───────────────────────────────────┐
│                 Backend (FastAPI)                        │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐   │
│  │Auth API  │  │Campaign  │  │ AI Service         │   │
│  │          │  │API       │  │                    │   │
│  └──────────┘  └──────────┘  └────────────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬──────────────┐
        ▼             ▼             ▼              ▼
   ┌────────┐   ┌────────┐   ┌──────────┐   ┌──────────┐
   │        │   │        │   │          │   │          │
   │ PostgreSQL│  Redis  │   │ SendGrid │   │  OpenAI  │
   │        │   │        │   │          │   │  Claude  │
   └────────┘   └────────┘   └──────────┘   └──────────┘
```

## 🔒 Security Features

- JWT-based authentication with refresh tokens
- Password hashing with bcrypt
- CORS configuration
- SQL injection prevention via SQLAlchemy ORM
- Rate limiting on API endpoints
- Secure API key storage

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📦 Building for Production

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run build
# Serve the dist/ folder with a static file server
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Open an issue on GitHub
- Check the API documentation at `/docs`
- Review this README

## 🗺️ Roadmap

### Phase 1 (Completed ✅)
- ✅ User authentication
- ✅ AI content generation
- ✅ Email campaigns
- ✅ Basic workflow automation
- ✅ Dashboard and analytics

### Phase 2 (Completed ✅)
- ✅ **Lead Management CRM** - Full CRUD, scoring, filtering
- ✅ **Advanced Analytics API** - Timeline, growth, heatmaps
- ✅ **Interactive Charts** - Real-time data visualization with Recharts
- ✅ **Workflow Management UI** - Templates and activation controls
- ✅ **Enhanced Dashboard** - Period selection, AI insights
- ✅ **Activity Tracking** - Lead engagement monitoring

### Phase 3 (Future)
- [ ] SMS campaigns
- [ ] WhatsApp integration
- [ ] Multi-language support
- [ ] Team collaboration features
- [ ] White-label options

## 💡 Tips

1. **AI Content Generation:** The platform works in demo mode even without API keys. To enable full AI features, add your OpenAI or Anthropic API keys.

2. **Email Sending:** Without SendGrid configured, campaigns will be simulated. Add your SendGrid API key for actual email delivery.

3. **Database:** For production, use a managed PostgreSQL instance with regular backups.

4. **Performance:** Use Redis caching to improve API response times for frequently accessed data.

## 📊 Project Stats

- **Lines of Code:** ~20,000+
- **API Endpoints:** 45+
- **React Components:** 15+
- **React Pages:** 8
- **Database Tables:** 7
- **Interactive Charts:** 3 (Recharts)

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Anthropic for Claude API
- FastAPI team for the excellent framework
- React team for the UI library
- Tailwind CSS for styling utilities

---

Built with ❤️ for startups and small businesses looking to automate their marketing efforts.
