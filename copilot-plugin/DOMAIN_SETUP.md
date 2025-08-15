# 🌐 DOMAIN SETUP CHO MICROSOFT COPILOT PLUGIN

## 📋 **YÊU CẦU DOMAIN**

Microsoft Copilot Studio yêu cầu:
- ✅ **Public domain** với HTTPS
- ✅ **SSL certificate** hợp lệ
- ✅ **Publicly accessible** từ internet
- ❌ **KHÔNG** chấp nhận localhost

## 🚀 **CÁC LỰA CHỌN DEPLOYMENT**

### **Option 1: Sử dụng Domain hiện có (Khuyến nghị)**

#### **1.1 Subdomain cho Plugin**
```
https://copilot.iris.pnj.com.vn
```

**Cấu hình DNS:**
```
Type: A
Name: copilot
Value: [Your Server IP]
TTL: 300
```

#### **1.2 Path-based routing**
```
https://iris.pnj.com.vn/copilot-plugin/
```

### **Option 2: Cloud Services**

#### **2.1 Azure App Service**
```bash
# Deploy lên Azure App Service
az webapp create --name iris-copilot-plugin --resource-group iris-rg --plan iris-plan --runtime "PYTHON|3.11"

# Configure custom domain
az webapp config hostname add --webapp-name iris-copilot-plugin --resource-group iris-rg --hostname copilot.iris.pnj.com.vn
```

#### **2.2 AWS Elastic Beanstalk**
```bash
# Deploy lên AWS EB
eb init iris-copilot-plugin --platform python-3.11
eb create production
eb deploy
```

#### **2.3 Google Cloud Run**
```bash
# Deploy lên Cloud Run
gcloud run deploy iris-copilot-plugin --source . --platform managed --region asia-southeast1 --allow-unauthenticated
```

### **Option 3: VPS/Server**

#### **3.1 Nginx Configuration**
```nginx
server {
    listen 80;
    server_name copilot.iris.pnj.com.vn;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name copilot.iris.pnj.com.vn;
    
    ssl_certificate /etc/letsencrypt/live/copilot.iris.pnj.com.vn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/copilot.iris.pnj.com.vn/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### **3.2 SSL Certificate với Let's Encrypt**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d copilot.iris.pnj.com.vn

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔧 **CẬP NHẬT CONFIGURATION**

### **1. Update manifest.json**
```json
{
  "validDomains": [
    "copilot.iris.pnj.com.vn"
  ],
  "webApplicationInfo": {
    "id": "YOUR_ACTUAL_APP_ID_HERE",
    "resource": "https://copilot.iris.pnj.com.vn"
  }
}
```

### **2. Update plugin.json**
```json
{
  "auth": {
    "client_url": "https://copilot.iris.pnj.com.vn/auth"
  },
  "api": {
    "url": "https://copilot.iris.pnj.com.vn/api/v1/openapi.json"
  }
}
```

### **3. Update environment variables**
```bash
# .env
IRIS_API_URL=https://iris.pnj.com.vn
IRIS_API_BASE_URL=https://iris.pnj.com.vn/api/v1
PLUGIN_DOMAIN=https://copilot.iris.pnj.com.vn
```

## 🧪 **TESTING DOMAIN**

### **1. Health Check**
```bash
curl https://copilot.iris.pnj.com.vn/health
```

### **2. SSL Test**
```bash
# Test SSL certificate
openssl s_client -connect copilot.iris.pnj.com.vn:443 -servername copilot.iris.pnj.com.vn

# Online SSL checker
# https://www.ssllabs.com/ssltest/
```

### **3. Accessibility Test**
```bash
# Test từ external network
curl -I https://copilot.iris.pnj.com.vn/health

# Test với different locations
# https://tools.keycdn.com/performance
```

## 📊 **MONITORING DOMAIN**

### **1. Uptime Monitoring**
```bash
# Setup monitoring với UptimeRobot hoặc Pingdom
# Monitor: https://copilot.iris.pnj.com.vn/health
# Expected: 200 OK
```

### **2. SSL Certificate Monitoring**
```bash
# Monitor SSL expiration
# Alert when < 30 days remaining
```

### **3. Performance Monitoring**
```bash
# Monitor response times
# Alert when > 2 seconds
```

## 🔒 **SECURITY CONSIDERATIONS**

### **1. SSL/TLS Configuration**
```nginx
# Modern SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
```

### **2. Security Headers**
```nginx
# Add security headers
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### **3. Rate Limiting**
```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=copilot:10m rate=10r/s;
limit_req zone=copilot burst=20 nodelay;
```

## 🚀 **DEPLOYMENT CHECKLIST**

### **Pre-Deployment**
- [ ] Domain registered và configured
- [ ] DNS records updated
- [ ] SSL certificate installed
- [ ] Server accessible từ internet
- [ ] Firewall configured

### **Deployment**
- [ ] Application deployed
- [ ] Environment variables set
- [ ] Health check passing
- [ ] SSL certificate valid
- [ ] Performance acceptable

### **Post-Deployment**
- [ ] Monitoring configured
- [ ] Alerts setup
- [ ] Backup procedures
- [ ] Documentation updated
- [ ] Team notified

## 📞 **SUPPORT**

### **Domain Issues**
- **DNS Provider:** Check DNS propagation
- **SSL Provider:** Verify certificate installation
- **Hosting Provider:** Check server configuration

### **Performance Issues**
- **CDN:** Consider using Cloudflare
- **Caching:** Implement Redis caching
- **Load Balancing:** For high traffic

---

**Lưu ý:** Microsoft Copilot Studio sẽ validate domain accessibility trước khi approve plugin. Đảm bảo domain hoạt động ổn định và có SSL certificate hợp lệ.
