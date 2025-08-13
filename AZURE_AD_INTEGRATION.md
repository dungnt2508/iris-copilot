# Azure AD Integration Guide

## Tổng quan

Tài liệu này mô tả cách tích hợp Azure Active Directory (Azure AD) vào hệ thống IRIS RAG Bot theo kiến trúc Domain-Driven Design (DDD).

## Kiến trúc Tích hợp

### Sơ đồ Luồng

```
[ Người dùng Teams ]
        │
        ▼
[ Microsoft Teams UI ]
        │  (sử dụng tài khoản Microsoft / Azure AD)
        ▼
[ Azure AD Service ]
        │  (OAuth2 / OpenID Connect)
        │  client_id + client_secret + tenant_id
        ▼
─────────────────────────────────────────────
[ Infrastructure Layer - AzureADAuthAdapter ]
    - Kết nối Azure AD
    - Lấy access token (Client Credentials / Auth Code)
    - Gọi Microsoft Graph API (Teams, User Info, ...)
        │
        ▼
[ Application Layer - Use Case ]
    - Ví dụ: SyncTeamsUsersUseCase
    - Gọi AzureADAuthAdapter để lấy token / data
    - Map data thành domain entity User
        │
        ▼
[ Domain Layer ]
    - Entity: User, Role
    - Repository Interface: UserRepository
        │
        ▼
[ Infrastructure Layer - UserRepositoryImpl ]
    - Lưu dữ liệu vào PostgreSQL / Redis
```

## Cài đặt

### 1. Dependencies

Thêm các dependencies sau vào `requirements.txt`:

```txt
# Azure AD Integration
msal==1.24.1
azure-identity==1.15.0
azure-graphrbac==0.61.1
```

### 2. Environment Variables

Tạo file `.env` với các biến môi trường sau:

```env
# Azure AD Configuration
AZURE_AD_CLIENT_ID=your-azure-ad-client-id
AZURE_AD_CLIENT_SECRET=your-azure-ad-client-secret
AZURE_AD_TENANT_ID=your-azure-ad-tenant-id
AZURE_AD_REDIRECT_URI=http://localhost:8000/api/v1/azure-ad/callback
AZURE_AD_AUTHORITY=https://login.microsoftonline.com
AZURE_AD_GRAPH_ENDPOINT=https://graph.microsoft.com/v1.0
AZURE_AD_CACHE_TTL=3600

# Azure AD Scopes (comma-separated)
AZURE_AD_SCOPES=https://graph.microsoft.com/User.Read,https://graph.microsoft.com/User.ReadBasic.All,https://graph.microsoft.com/Group.Read.All
```

### 3. Azure AD App Registration

1. Đăng nhập vào [Azure Portal](https://portal.azure.com)
2. Tạo App Registration mới
3. Cấu hình Redirect URI: `http://localhost:8000/api/v1/azure-ad/callback`
4. Thêm API permissions:
   - Microsoft Graph > User.Read
   - Microsoft Graph > User.ReadBasic.All
   - Microsoft Graph > Group.Read.All
5. Tạo Client Secret và lưu lại
6. Ghi chép Client ID, Tenant ID

## Cấu trúc Code

### 1. Infrastructure Layer - AzureADAdapter

**File**: `app/adapters/azure_ad_adapter.py`

```python
class AzureADAdapter:
    """Adapter for Azure AD integration"""
    
    async def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate OAuth2 authorization URL"""
        
    async def exchange_code_for_token(self, authorization_code: str) -> AzureADTokenResponse:
        """Exchange authorization code for access token"""
        
    async def get_user_info(self, access_token: str) -> AzureADUserInfo:
        """Get user information from Microsoft Graph API"""
```

### 2. Application Layer - Use Cases

**File**: `app/application/user/use_cases/azure_ad_login.py`

```python
class AzureADLoginUseCase:
    """Use case for Azure AD authentication"""
    
    async def execute(self, request: AzureADLoginRequest) -> AzureADLoginResponse:
        """Execute Azure AD login flow"""

class SyncAzureADUsersUseCase:
    """Use case for syncing users from Azure AD"""
    
    async def execute(self, query: str = "") -> Dict[str, Any]:
        """Sync users from Azure AD"""
```

### 3. API Layer - Routers

**File**: `app/api/v1/routers/azure_ad.py`

```python
@router.get("/auth")
async def get_azure_ad_auth_url():
    """Get Azure AD authorization URL"""

@router.get("/callback")
async def azure_ad_callback():
    """Handle OAuth2 callback"""

@router.post("/login")
async def azure_ad_login():
    """Azure AD login endpoint"""
```

## API Endpoints

### 1. OAuth2 Flow

#### GET `/api/v1/azure-ad/auth`
Lấy URL authorization cho OAuth2 flow.

**Response**:
```json
{
    "auth_url": "https://login.microsoftonline.com/...",
    "state": "random-state"
}
```

#### GET `/api/v1/azure-ad/callback`
Callback endpoint sau khi user authenticate với Azure AD.

**Parameters**:
- `code`: Authorization code từ Azure AD
- `state`: State parameter (optional)

### 2. Login

#### POST `/api/v1/azure-ad/login`
Đăng nhập bằng Azure AD authorization code.

**Request**:
```json
{
    "authorization_code": "auth-code-from-azure-ad",
    "state": "optional-state"
}
```

**Response**:
```json
{
    "user_id": "user-uuid",
    "email": "user@company.com",
    "username": "username",
    "full_name": "User Name",
    "role": "user",
    "is_new_user": false,
    "azure_ad_user": {
        "id": "azure-ad-user-id",
        "display_name": "User Name",
        "mail": "user@company.com"
    }
}
```

### 3. User Management

#### POST `/api/v1/azure-ad/sync-users`
Đồng bộ users từ Azure AD (Admin only).

**Request**:
```json
{
    "query": "optional-search-query"
}
```

**Response**:
```json
{
    "total_synced": 10,
    "created": 5,
    "updated": 5,
    "query": "search-query"
}
```

#### GET `/api/v1/azure-ad/validate-token`
Validate Azure AD access token.

#### GET `/api/v1/azure-ad/user-info`
Lấy thông tin user từ Azure AD.

#### GET `/api/v1/azure-ad/search-users`
Tìm kiếm users trong Azure AD.

## Luồng Hoạt động

### 1. User Login Flow

1. **Frontend** gọi `/api/v1/azure-ad/auth` để lấy authorization URL
2. **User** click vào URL và authenticate với Azure AD
3. **Azure AD** redirect về `/api/v1/azure-ad/callback` với authorization code
4. **Backend** exchange code thành access token
5. **Backend** lấy user info từ Microsoft Graph API
6. **Backend** tạo/cập nhật user trong database
7. **Backend** redirect về frontend với JWT token

### 2. User Sync Flow

1. **Admin** gọi `/api/v1/azure-ad/sync-users`
2. **Backend** lấy client credentials token
3. **Backend** search users trong Azure AD
4. **Backend** tạo/cập nhật users trong database
5. **Backend** trả về kết quả sync

## Mapping User Roles

Hệ thống tự động map Azure AD groups/roles thành user roles:

- **Admin**: Groups/roles chứa "admin", "administrator", "system admin"
- **User**: Mặc định cho tất cả users khác

## Security Considerations

1. **State Parameter**: Sử dụng state parameter để prevent CSRF attacks
2. **Token Validation**: Validate Azure AD tokens trước khi sử dụng
3. **HTTPS**: Luôn sử dụng HTTPS trong production
4. **Secret Management**: Lưu trữ client secret an toàn
5. **Scope Limitation**: Chỉ request những scope cần thiết

## Testing

### 1. Unit Tests

```python
# Test Azure AD Adapter
async def test_azure_ad_adapter_get_auth_url():
    adapter = AzureADAdapter()
    auth_url = await adapter.get_authorization_url("test-state")
    assert "login.microsoftonline.com" in auth_url

# Test Use Cases
async def test_azure_ad_login_use_case():
    use_case = AzureADLoginUseCase(mock_repo, mock_adapter)
    response = await use_case.execute(mock_request)
    assert response.user.email == "test@company.com"
```

### 2. Integration Tests

```python
# Test API Endpoints
async def test_azure_ad_auth_endpoint():
    response = await client.get("/api/v1/azure-ad/auth")
    assert response.status_code == 200
    assert "auth_url" in response.json()
```

## Troubleshooting

### Common Issues

1. **Invalid Client ID/Secret**: Kiểm tra Azure AD App Registration
2. **Redirect URI Mismatch**: Đảm bảo redirect URI khớp với Azure AD config
3. **Insufficient Permissions**: Kiểm tra API permissions trong Azure AD
4. **Token Expired**: Implement token refresh logic

### Debug Logs

Enable debug logging để troubleshoot:

```python
import logging
logging.getLogger("app.adapters.azure_ad_adapter").setLevel(logging.DEBUG)
```

## Production Deployment

1. **Environment Variables**: Sử dụng secure environment variables
2. **HTTPS**: Cấu hình HTTPS cho tất cả endpoints
3. **Monitoring**: Monitor Azure AD API calls và errors
4. **Rate Limiting**: Implement rate limiting cho Azure AD endpoints
5. **Caching**: Cache Azure AD user information để giảm API calls

## Migration từ Local Auth

1. **User Mapping**: Map existing users với Azure AD accounts
2. **Role Migration**: Migrate user roles từ local sang Azure AD
3. **Data Migration**: Migrate user metadata và preferences
4. **Testing**: Test migration với subset users trước
5. **Rollback Plan**: Có plan rollback nếu cần

## Tài liệu Tham khảo

- [Azure AD Documentation](https://docs.microsoft.com/en-us/azure/active-directory/)
- [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/)
- [MSAL Python](https://docs.microsoft.com/en-us/azure/active-directory/develop/msal-python)
- [OAuth2 Flow](https://tools.ietf.org/html/rfc6749)
