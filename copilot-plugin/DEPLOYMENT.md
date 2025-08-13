# Hướng dẫn triển khai Microsoft Copilot Plugin

## **Tổng quan**

Microsoft Copilot Plugin cho phép users tương tác với IRIS Teams API thông qua các nền tảng M365 như Teams, Outlook, Word, Excel, PowerPoint, SharePoint, và Windows 11 Copilot.

## **Kiến trúc**

```
User → Microsoft Copilot → IRIS Plugin → IRIS API → Microsoft Graph API
```

## **Bước 1: Chuẩn bị Infrastructure**

### **1.1. Deploy IRIS API**
```bash
# Deploy IRIS API lên production
# Ví dụ: Azure App Service, AWS ECS, Google Cloud Run
```

### **1.2. Deploy Copilot Plugin**
```bash
# Deploy plugin handler
cd copilot-plugin
pip install -r requirements.txt
python plugin_handler.py
```

### **1.3. Cấu hình Domain và SSL**
```bash
# Cần có domain với SSL certificate
# Ví dụ: https://iris.pnj.com.vn
# Ví dụ: https://copilot.iris.pnj.com.vn
```

## **Bước 2: Cấu hình Azure AD**

### **2.1. Tạo App Registration cho Plugin**
1. Vào Azure Portal → Azure Active Directory → App registrations
2. Click "New registration"
3. Điền thông tin:
   - **Name**: IRIS Copilot Plugin
   - **Supported account types**: Accounts in this organizational directory only
   - **Redirect URI**: https://iris.pnj.com.vn/auth/callback

### **2.2. Cấu hình API Permissions**
Thêm các permissions:
- `User.Read`
- `Team.ReadBasic.All`
- `Channel.ReadBasic.All`
- `ChannelMessage.Send`
- `Chat.Read`
- `ChatMessage.Send`
- `Calendars.Read`
- `Calendars.ReadWrite`

### **2.3. Tạo Client Secret**
1. Certificates & secrets → New client secret
2. Lưu secret value

## **Bước 3: Cấu hình Plugin**

### **3.1. Cập nhật manifest.json**
```json
{
  "id": "YOUR_APP_ID",
  "validDomains": [
    "iris.pnj.com.vn"
  ]
}
```

### **3.2. Cập nhật plugin.json**
```json
{
  "auth": {
    "client_url": "https://iris.pnj.com.vn/auth",
    "authorization_url": "https://login.microsoftonline.com/YOUR_TENANT_ID/oauth2/v2.0/authorize",
    "token_url": "https://login.microsoftonline.com/YOUR_TENANT_ID/oauth2/v2.0/token"
  },
  "api": {
    "url": "https://iris.pnj.com.vn/api/v1/openapi.json"
  }
}
```

### **3.3. Cập nhật OpenAPI spec**
```json
{
  "servers": [
    {
      "url": "https://iris.pnj.com.vn/api/v1",
      "description": "Production server"
    }
  ]
}
```

## **Bước 4: Deploy lên Microsoft**

### **4.1. Package Plugin**
```bash
# Tạo package cho Teams app
npm install -g @microsoft/teamsfx-cli
teamsfx package --env prod
```

### **4.2. Submit to Microsoft**
1. Vào [Microsoft Teams Admin Center](https://admin.teams.microsoft.com/)
2. Teams apps → Manage apps
3. Upload custom app
4. Upload file .zip đã tạo

### **4.3. Publish to App Store (Optional)**
1. Vào [Microsoft AppSource](https://appsource.microsoft.com/)
2. Submit app để review
3. Sau khi approved, app sẽ có sẵn cho tất cả users

## **Bước 5: Cấu hình cho Users**

### **5.1. Admin Configuration**
```powershell
# PowerShell script để cấu hình cho organization
Connect-MicrosoftTeams

# Enable plugin cho organization
Set-TeamsAppPermissionPolicy -Identity "Global" -AllowedAppIds @("YOUR_APP_ID")

# Assign plugin cho users
Grant-CsTeamsAppPermissionPolicy -Identity "user@domain.com" -PolicyName "Global"
```

### **5.2. User Setup**
1. User mở Teams
2. Apps → Browse all apps
3. Tìm "IRIS Teams Copilot"
4. Click "Add"

## **Bước 6: Testing**

### **6.1. Test Plugin Endpoints**
```bash
# Test health check
curl https://iris.pnj.com.vn/copilot/health

# Test capabilities
curl https://iris.pnj.com.vn/copilot/capabilities

# Test plugin processing
curl -X POST https://iris.pnj.com.vn/copilot/process \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "intent": "get_teams",
    "parameters": {},
    "context": {}
  }'
```

### **6.2. Test trong Teams**
1. Mở Teams chat
2. Gõ "@IRIS Teams Copilot"
3. Thử các commands:
   - "Show my teams"
   - "Send message to General channel: Hello from Copilot!"
   - "Show my calendars"

## **Bước 7: Monitoring và Analytics**

### **7.1. Logging**
```python
# Cấu hình logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('copilot-plugin.log'),
        logging.StreamHandler()
    ]
)
```

### **7.2. Metrics**
```python
# Track usage metrics
from prometheus_client import Counter, Histogram

request_counter = Counter('copilot_requests_total', 'Total requests', ['intent', 'status'])
request_duration = Histogram('copilot_request_duration_seconds', 'Request duration')
```

### **7.3. Alerting**
```yaml
# Prometheus alert rules
groups:
  - name: copilot_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(copilot_requests_total{status="error"}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate in Copilot plugin"
```

## **Bước 8: Security**

### **8.1. Authentication**
```python
# Validate tokens
async def validate_token(token: str) -> bool:
    try:
        # Verify JWT token
        decoded = jwt.decode(token, options={"verify_signature": False})
        return True
    except:
        return False
```

### **8.2. Rate Limiting**
```python
# Implement rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/copilot/process")
@limiter.limit("10/minute")
async def process_copilot_request(request: Request):
    # ...
```

### **8.3. Input Validation**
```python
# Validate input parameters
from pydantic import validator

class CopilotRequest(BaseModel):
    user_id: str
    intent: str
    parameters: Dict[str, Any] = {}
    
    @validator('intent')
    def validate_intent(cls, v):
        allowed_intents = ['get_teams', 'send_message', 'get_calendars']
        if v not in allowed_intents:
            raise ValueError(f'Invalid intent: {v}')
        return v
```

## **Troubleshooting**

### **Common Issues**

1. **Plugin không hiển thị trong Teams**
   - Kiểm tra app đã được approve chưa
   - Kiểm tra permissions policy
   - Kiểm tra domain validation

2. **Authentication errors**
   - Kiểm tra Azure AD configuration
   - Kiểm tra redirect URIs
   - Kiểm tra client secret

3. **API calls failing**
   - Kiểm tra IRIS API status
   - Kiểm tra network connectivity
   - Kiểm tra CORS configuration

### **Debug Commands**
```bash
# Check plugin status
curl -X GET https://iris.pnj.com.vn/copilot/health

# Check API status
curl -X GET https://iris.pnj.com.vn/api/v1/teams/teams \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check logs
tail -f copilot-plugin.log
```

## **Performance Optimization**

### **8.1. Caching**
```python
# Implement caching
import redis
from functools import lru_cache

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@lru_cache(maxsize=100)
async def get_teams_cached(user_id: str):
    # Cache teams data for 5 minutes
    cache_key = f"teams:{user_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Fetch from API
    teams = await fetch_teams_from_api(user_id)
    redis_client.setex(cache_key, 300, json.dumps(teams))
    return teams
```

### **8.2. Connection Pooling**
```python
# Use connection pooling
import httpx

async with httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
) as client:
    # Use client for API calls
```

## **Scaling**

### **8.1. Horizontal Scaling**
```yaml
# Docker Compose for scaling
version: '3.8'
services:
  copilot-plugin:
    image: iris/copilot-plugin:latest
    deploy:
      replicas: 3
    environment:
      - IRIS_API_URL=https://iris.pnj.com.vn
    ports:
      - "8001:8001"
```

### **8.2. Load Balancing**
```nginx
# Nginx configuration
upstream copilot_backend {
    server copilot1:8001;
    server copilot2:8001;
    server copilot3:8001;
}

server {
    listen 443 ssl;
    server_name iris.pnj.com.vn;
    
    location /copilot/ {
        proxy_pass http://copilot_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## **Maintenance**

### **8.1. Regular Updates**
- Update dependencies monthly
- Monitor security advisories
- Update plugin manifest khi có thay đổi

### **8.2. Backup Strategy**
- Backup configuration files
- Backup logs và metrics
- Test recovery procedures

### **8.3. Documentation**
- Maintain user documentation
- Update API documentation
- Keep deployment guides current

