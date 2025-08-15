# 🚀 HƯỚNG DẪN DEPLOYMENT MICROSOFT COPILOT PLUGIN

## 📋 Tổng quan

Hướng dẫn này sẽ giúp bạn deploy IRIS Copilot Plugin lên Microsoft Copilot và tích hợp với hệ thống IRIS.

## 🎯 Yêu cầu hệ thống

### Prerequisites
- ✅ Azure AD tenant đã được cấu hình
- ✅ IRIS Backend API đã được deploy
- ✅ Domain name (iris.pnj.com.vn) đã được cấu hình
- ✅ SSL certificate cho HTTPS
- ✅ Microsoft Copilot Studio access

### Azure AD Configuration
```bash
# Các permission cần thiết cho Azure AD App
- User.Read
- Team.ReadBasic.All
- Channel.ReadBasic.All
- ChannelMessage.Send
- Group.Read.All
- Calendars.Read
- Events.Read
```

## 🏗️ Cấu trúc Plugin

```
copilot-plugin/
├── manifest.json          # Teams app manifest
├── plugin.json            # Copilot plugin config
├── openapi.json           # API specification
├── plugin_handler.py      # Plugin logic
├── DEPLOYMENT.md          # This file
└── icons/                 # App icons
    ├── outline.png
    └── color.png
```

## 📦 Bước 1: Chuẩn bị Plugin Files

### 1.1 Cập nhật manifest.json
```json
{
  "manifestVersion": "1.14",
  "version": "1.0.0",
  "id": "{{TEAMS_APP_ID}}",
  "packageName": "com.iris.teams.copilot",
  "developer": {
    "name": "IRIS Team",
    "websiteUrl": "https://iris.pnj.com.vn",
    "privacyUrl": "https://iris.pnj.com.vn/privacy",
    "termsOfUseUrl": "https://iris.pnj.com.vn/terms"
  },
  "name": {
    "short": "IRIS Teams Copilot",
    "full": "IRIS Teams Integration for Microsoft Copilot"
  },
  "description": {
    "short": "Tích hợp IRIS Teams với Microsoft Copilot",
    "full": "Plugin cho phép Microsoft Copilot tương tác với IRIS Teams API để quản lý teams, channels, và gửi tin nhắn."
  },
  "icons": {
    "outline": "outline.png",
    "color": "color.png"
  },
  "accentColor": "#FFFFFF",
  "permissions": [
    "identity",
    "messageTeamMembers"
  ],
  "validDomains": [
    "iris.pnj.com.vn"
  ],
  "webApplicationInfo": {
    "id": "{{TEAMS_APP_ID}}",
    "resource": "https://iris.pnj.com.vn"
  },
  "copilotExtensions": {
    "plugins": [
      {
        "file": "plugin.json",
        "id": "iris-teams-plugin"
      }
    ]
  }
}
```

### 1.2 Cập nhật plugin.json
```json
{
  "schema": "https://raw.githubusercontent.com/microsoft/OpenAPI.NET.OData/main/schemas/v4.0.0/OpenAPI.json",
  "apiVersion": "1.0.0",
  "nameForHuman": "IRIS Teams Copilot",
  "nameForModel": "iris_teams_copilot",
  "descriptionForHuman": "Plugin để tương tác với IRIS Teams API, cho phép quản lý teams, channels, và gửi tin nhắn.",
  "descriptionForModel": "Plugin này cung cấp các chức năng để tương tác với Microsoft Teams thông qua IRIS API. Bao gồm: lấy danh sách teams, channels, gửi tin nhắn, và quản lý group chats.",
  "auth": {
    "type": "oauth2",
    "instructions": "Sử dụng Azure AD để xác thực với IRIS Teams API",
    "client_url": "https://iris.pnj.com.vn/auth",
    "scope": "https://graph.microsoft.com/User.Read https://graph.microsoft.com/Team.ReadBasic.All https://graph.microsoft.com/Channel.ReadBasic.All https://graph.microsoft.com/ChannelMessage.Send",
    "authorization_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token"
  },
  "api": {
    "type": "openapi",
    "url": "https://iris.pnj.com.vn/api/v1/openapi.json",
    "isUserAuthenticated": true
  },
  "logo_url": "https://iris.pnj.com.vn/logo.png",
  "contact_email": "support@iris.pnj.com.vn",
  "legal_info_url": "https://iris.pnj.com.vn/legal"
}
```

## 🔧 Bước 2: Cấu hình Azure AD

### 2.1 Tạo Azure AD App Registration
```bash
# 1. Truy cập Azure Portal > App registrations
# 2. Click "New registration"
# 3. Điền thông tin:
#    - Name: IRIS Copilot Plugin
#    - Supported account types: Accounts in this organizational directory only
#    - Redirect URI: https://iris.pnj.com.vn/auth/callback

# 4. Lưu lại Application (client) ID và Directory (tenant) ID
```

### 2.2 Cấu hình API Permissions
```bash
# 1. Vào "API permissions"
# 2. Click "Add a permission"
# 3. Chọn "Microsoft Graph"
# 4. Chọn "Delegated permissions"
# 5. Thêm các permissions:
#    - User.Read
#    - Team.ReadBasic.All
#    - Channel.ReadBasic.All
#    - ChannelMessage.Send
#    - Group.Read.All
#    - Calendars.Read
#    - Events.Read

# 6. Click "Grant admin consent"
```

### 2.3 Tạo Client Secret
```bash
# 1. Vào "Certificates & secrets"
# 2. Click "New client secret"
# 3. Điền description và chọn expiration
# 4. Copy và lưu secret value
```

## 🌐 Bước 3: Deploy IRIS Backend

### 3.1 Cấu hình Environment Variables
```bash
# .env file
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_CLIENT_SECRET=your-client-secret
AZURE_AD_TENANT_ID=your-tenant-id
AZURE_AD_REDIRECT_URI=https://iris.pnj.com.vn/api/v1/azure-ad/callback
AZURE_AD_AUTHORITY=https://login.microsoftonline.com
AZURE_AD_GRAPH_ENDPOINT=https://graph.microsoft.com/v1.0
AZURE_AD_SCOPES=https://graph.microsoft.com/User.Read,https://graph.microsoft.com/Team.ReadBasic.All,https://graph.microsoft.com/Channel.ReadBasic.All,https://graph.microsoft.com/ChannelMessage.Send

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/iris_db

# OpenAI
OPENAI_API_KEY=your-openai-key

# Security
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
```

### 3.2 Deploy với Docker
```bash
# Build image
docker build -t iris-backend:latest .

# Run container
docker run -d \
  --name iris-backend \
  -p 8000:8000 \
  --env-file .env \
  iris-backend:latest
```

### 3.3 Cấu hình Nginx (Optional)
```nginx
server {
    listen 80;
    server_name iris.pnj.com.vn;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name iris.pnj.com.vn;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🤖 Bước 4: Deploy lên Microsoft Copilot

### 4.1 Tạo Plugin Package
```bash
# 1. Tạo ZIP file chứa plugin files
zip -r iris-copilot-plugin.zip copilot-plugin/

# 2. Files cần có trong ZIP:
#    - manifest.json
#    - plugin.json
#    - openapi.json
#    - icons/outline.png
#    - icons/color.png
```

### 4.2 Upload lên Microsoft Copilot Studio
```bash
# 1. Truy cập Microsoft Copilot Studio
# 2. Vào "Plugins" section
# 3. Click "Add plugin"
# 4. Upload ZIP file
# 5. Cấu hình authentication
# 6. Test plugin functionality
```

### 4.3 Cấu hình Authentication
```bash
# 1. Trong Copilot Studio, cấu hình OAuth2:
#    - Client ID: Azure AD App ID
#    - Client Secret: Azure AD Client Secret
#    - Authorization URL: https://login.microsoftonline.com/common/oauth2/v2.0/authorize
#    - Token URL: https://login.microsoftonline.com/common/oauth2/v2.0/token
#    - Scope: https://graph.microsoft.com/User.Read https://graph.microsoft.com/Team.ReadBasic.All https://graph.microsoft.com/Channel.ReadBasic.All https://graph.microsoft.com/ChannelMessage.Send

# 2. Test authentication flow
```

## 🧪 Bước 5: Testing

### 5.1 Test API Endpoints
```bash
# Test health check
curl https://iris.pnj.com.vn/api/v1/copilot/health

# Test authentication
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://iris.pnj.com.vn/api/v1/auth/me

# Test teams endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://iris.pnj.com.vn/api/v1/teams/teams
```

### 5.2 Test Copilot Integration
```bash
# 1. Trong Copilot Studio, test các scenarios:
#    - "Show me my teams"
#    - "Send a message to General channel"
#    - "Search for documents about AI"
#    - "Get my calendar events"

# 2. Verify responses và error handling
```

## 🔍 Bước 6: Monitoring & Troubleshooting

### 6.1 Logging Configuration
```python
# app/core/logger.py
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

### 6.2 Health Check Endpoints
```bash
# Health check
GET /api/v1/copilot/health

# Metrics
GET /api/v1/metrics

# OpenAPI docs
GET /api/v1/docs
```

### 6.3 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Authentication failed | Invalid token | Check Azure AD configuration |
| Teams API errors | Missing permissions | Grant admin consent |
| Plugin not loading | Invalid manifest | Validate JSON schema |
| CORS errors | Missing headers | Configure CORS middleware |

## 📊 Bước 7: Production Deployment

### 7.1 Production Checklist
- [ ] SSL certificate installed
- [ ] Environment variables configured
- [ ] Database migrations completed
- [ ] Monitoring setup
- [ ] Backup strategy implemented
- [ ] Load testing completed
- [ ] Security audit passed

### 7.2 Performance Optimization
```python
# Caching configuration
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# Database connection pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### 7.3 Security Hardening
```python
# Security headers
SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
}

# CORS configuration
CORS_ORIGINS = [
    "https://iris.pnj.com.vn",
    "https://copilot.microsoft.com"
]
```

## 📈 Bước 8: Post-Deployment

### 8.1 User Training
- [ ] Create user documentation
- [ ] Conduct training sessions
- [ ] Provide troubleshooting guide
- [ ] Set up support channels

### 8.2 Monitoring Setup
- [ ] Application performance monitoring
- [ ] Error tracking and alerting
- [ ] Usage analytics
- [ ] Cost monitoring

### 8.3 Maintenance Plan
- [ ] Regular security updates
- [ ] Performance monitoring
- [ ] Backup verification
- [ ] Plugin updates

## 🎯 Success Metrics

### Technical Metrics
- [ ] API response time < 200ms (p95)
- [ ] 99.9% uptime
- [ ] Zero security incidents
- [ ] < 1% error rate

### Business Metrics
- [ ] User adoption rate
- [ ] Feature usage statistics
- [ ] User satisfaction scores
- [ ] Support ticket reduction

## 📞 Support & Resources

### Documentation
- [Microsoft Copilot Plugin Documentation](https://docs.microsoft.com/en-us/microsoft-copilot-studio/)
- [Azure AD Authentication](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [Teams API Reference](https://docs.microsoft.com/en-us/graph/api/resources/teams-api-overview)

### Support Channels
- Email: support@iris.pnj.com.vn
- Teams: IRIS Support Channel
- Documentation: https://iris.pnj.com.vn/docs

---

**Last Updated:** 2025-01-27
**Version:** 1.0.0
**Status:** Ready for Deployment


