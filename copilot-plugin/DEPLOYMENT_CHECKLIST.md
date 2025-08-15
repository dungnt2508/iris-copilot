# ✅ CHECKLIST TRIỂN KHAI MICROSOFT COPILOT PLUGIN

## 📋 **PRE-DEPLOYMENT CHECKLIST**

### **Azure AD Configuration**
- [ ] **App Registration created**
  - [ ] Application ID noted
  - [ ] Tenant ID noted
  - [ ] Redirect URI configured
- [ ] **API Permissions configured**
  - [ ] User.Read
  - [ ] Team.ReadBasic.All
  - [ ] Channel.ReadBasic.All
  - [ ] ChannelMessage.Send
  - [ ] Group.Read.All
  - [ ] Calendars.Read
  - [ ] Events.Read
  - [ ] Admin consent granted
- [ ] **Client Secret created**
  - [ ] Secret value copied
  - [ ] Expiration date noted

### **Plugin Configuration**
- [ ] **manifest.json updated**
  - [ ] App ID replaced with actual value
  - [ ] Valid domains configured
  - [ ] Permissions set correctly
- [ ] **plugin.json updated**
  - [ ] Authentication URLs configured
  - [ ] API endpoints set correctly
  - [ ] Scopes defined properly
- [ ] **openapi.json validated**
  - [ ] All endpoints documented
  - [ ] Authentication schemes defined
  - [ ] Response schemas complete

### **Infrastructure Setup**
- [ ] **IRIS Backend deployed**
  - [ ] API accessible at https://iris.pnj.com.vn
  - [ ] All endpoints responding
  - [ ] Authentication working
- [ ] **Plugin server ready**
  - [ ] Docker image built
  - [ ] Environment variables configured
  - [ ] Health check passing

## 🚀 **DEPLOYMENT STEPS**

### **Step 1: Local Testing**
```bash
# 1. Install dependencies
cd copilot-plugin
pip install -r requirements.txt

# 2. Set environment variables
cp env.example .env
# Edit .env with your actual values

# 3. Start plugin server
python server.py

# 4. Run tests
python test_plugin.py
```

### **Step 2: Docker Deployment**
```bash
# 1. Build Docker image
docker build -t iris-copilot-plugin .

# 2. Run with Docker Compose
docker-compose up -d

# 3. Check logs
docker-compose logs -f iris-copilot-plugin

# 4. Test health endpoint
curl http://localhost:8001/health
```

### **Step 3: Production Deployment**
```bash
# 1. Deploy to production server
# (Azure App Service, AWS ECS, etc.)

# 2. Configure environment variables
# Set all required environment variables

# 3. Start the service
# Use your preferred deployment method

# 4. Verify deployment
curl https://your-domain.com/health
```

### **Step 4: Microsoft Copilot Studio**

#### **4.1 Access Copilot Studio**
1. Go to https://web.powerva.microsoft.com/
2. Sign in with Microsoft 365 admin account
3. Navigate to "Plugins" section

#### **4.2 Create Plugin Package**
```bash
# Run packaging script
python package_plugin.py

# This will create:
# - iris-copilot-plugin.zip
# - DEPLOYMENT_GUIDE.md
```

#### **4.3 Upload Plugin**
1. Click "Add plugin"
2. Select "Upload plugin"
3. Choose `iris-copilot-plugin.zip`
4. Click "Upload"

#### **4.4 Configure Authentication**
1. In plugin settings, go to "Authentication"
2. Configure OAuth2 settings:
   ```
   Client ID: [Your Azure AD App ID]
   Client Secret: [Your Azure AD Client Secret]
   Authorization URL: https://login.microsoftonline.com/common/oauth2/v2.0/authorize
   Token URL: https://login.microsoftonline.com/common/oauth2/v2.0/token
   Scope: https://graph.microsoft.com/User.Read https://graph.microsoft.com/Team.ReadBasic.All https://graph.microsoft.com/Channel.ReadBasic.All https://graph.microsoft.com/ChannelMessage.Send
   ```

#### **4.5 Test Plugin**
1. Go to "Test" section
2. Try these sample queries:
   ```
   "Show me my teams"
   "Search for AI documents"
   "Help me understand machine learning"
   "Send a message to General channel"
   ```

#### **4.6 Publish Plugin**
1. Review all settings
2. Click "Publish"
3. Plugin will be available to users

## 🧪 **TESTING CHECKLIST**

### **Functional Testing**
- [ ] **Health check endpoint**
  - [ ] Returns 200 OK
  - [ ] Shows plugin status
  - [ ] Shows IRIS API status
- [ ] **Authentication**
  - [ ] Valid token accepted
  - [ ] Invalid token rejected
  - [ ] Missing token rejected
- [ ] **Teams integration**
  - [ ] Get teams works
  - [ ] Get channels works
  - [ ] Send messages works
- [ ] **Document search**
  - [ ] Semantic search works
  - [ ] Results returned correctly
  - [ ] Error handling works
- [ ] **Chat/RAG**
  - [ ] Query processing works
  - [ ] Response generation works
  - [ ] Source attribution works

### **Performance Testing**
- [ ] **Response time**
  - [ ] < 200ms for simple queries
  - [ ] < 2s for complex queries
  - [ ] Graceful timeout handling
- [ ] **Concurrent requests**
  - [ ] Handles multiple requests
  - [ ] No resource conflicts
  - [ ] Proper error handling
- [ ] **Load testing**
  - [ ] 100+ concurrent users
  - [ ] Memory usage stable
  - [ ] CPU usage reasonable

### **Security Testing**
- [ ] **Input validation**
  - [ ] SQL injection prevention
  - [ ] XSS prevention
  - [ ] Path traversal prevention
- [ ] **Authentication**
  - [ ] Token validation
  - [ ] Permission checking
  - [ ] Session management
- [ ] **API security**
  - [ ] Rate limiting
  - [ ] CORS configuration
  - [ ] Security headers

## 📊 **MONITORING SETUP**

### **Application Monitoring**
- [ ] **Health checks**
  - [ ] Endpoint monitoring
  - [ ] Dependency monitoring
  - [ ] Alert configuration
- [ ] **Performance monitoring**
  - [ ] Response time tracking
  - [ ] Error rate tracking
  - [ ] Throughput monitoring
- [ ] **Logging**
  - [ ] Structured logging
  - [ ] Log aggregation
  - [ ] Log retention

### **Business Metrics**
- [ ] **Usage tracking**
  - [ ] User adoption
  - [ ] Feature usage
  - [ ] Query patterns
- [ ] **Quality metrics**
  - [ ] Response quality
  - [ ] User satisfaction
  - [ ] Error rates

## 🔧 **TROUBLESHOOTING**

### **Common Issues**

#### **Authentication Errors**
```
Error: Invalid token
Solution: Check Azure AD configuration and token validation
```

#### **API Connection Errors**
```
Error: Cannot connect to IRIS API
Solution: Verify IRIS API is accessible and network connectivity
```

#### **Plugin Loading Errors**
```
Error: Plugin not loading in Copilot Studio
Solution: Check manifest.json validation and file structure
```

#### **Permission Errors**
```
Error: Insufficient permissions
Solution: Verify API permissions are granted in Azure AD
```

### **Debug Commands**
```bash
# Check plugin server status
curl http://localhost:8001/health

# Check IRIS API status
curl https://iris.pnj.com.vn/api/v1/health

# Check Docker container logs
docker-compose logs iris-copilot-plugin

# Test authentication
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8001/teams
```

## 📞 **SUPPORT CONTACTS**

### **Technical Support**
- **Email:** support@iris.pnj.com.vn
- **Teams:** IRIS Support Channel
- **Documentation:** https://iris.pnj.com.vn/docs

### **Microsoft Support**
- **Copilot Studio:** https://docs.microsoft.com/en-us/microsoft-copilot-studio/
- **Azure AD:** https://docs.microsoft.com/en-us/azure/active-directory/
- **Teams API:** https://docs.microsoft.com/en-us/graph/api/resources/teams-api-overview

## ✅ **POST-DEPLOYMENT VERIFICATION**

### **Immediate Checks**
- [ ] Plugin loads in Copilot Studio
- [ ] Authentication flow works
- [ ] All endpoints respond correctly
- [ ] Error handling works properly
- [ ] Logging is functional

### **User Acceptance Testing**
- [ ] End users can access plugin
- [ ] Common queries work correctly
- [ ] Response quality is acceptable
- [ ] Performance meets expectations
- [ ] User feedback is positive

### **Production Readiness**
- [ ] Monitoring is active
- [ ] Alerts are configured
- [ ] Backup procedures in place
- [ ] Rollback plan ready
- [ ] Documentation complete

---

**Last Updated:** 2025-01-27  
**Status:** Ready for Deployment  
**Next Review:** After deployment
