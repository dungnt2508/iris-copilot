"""
Azure AD Adapter
Handles communication with Azure Active Directory
"""
import os
import json
import time
from typing import Optional, List
from dataclasses import dataclass
from msal import ConfidentialClientApplication
import httpx

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AzureADTokenResponse:
    """Azure AD token response"""
    access_token: str
    token_type: str
    expires_in: int
    scope: str
    refresh_token: Optional[str] = None


@dataclass
class AzureADUserInfo:
    """Azure AD user information"""
    id: str
    display_name: str
    given_name: str
    surname: str
    user_principal_name: str
    mail: str
    job_title: Optional[str] = None
    department: Optional[str] = None
    office_location: Optional[str] = None
    mobile_phone: Optional[str] = None
    business_phones: Optional[List[str]] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "given_name": self.given_name,
            "surname": self.surname,
            "user_principal_name": self.user_principal_name,
            "mail": self.mail,
            "job_title": self.job_title,
            "department": self.department,
            "office_location": self.office_location,
            "mobile_phone": self.mobile_phone,
            "business_phones": self.business_phones
        }


class AzureADAdapter:
    """Azure AD Adapter for authentication and user management"""
    
    def __init__(self):
        # Read configuration directly from environment variables
        self.client_id = os.getenv("AZURE_AD_CLIENT_ID", "")
        self.client_secret = os.getenv("AZURE_AD_CLIENT_SECRET", "")
        self.tenant_id = os.getenv("AZURE_AD_TENANT_ID", "")
        self.redirect_uri = os.getenv("AZURE_AD_REDIRECT_URI", "http://localhost:8000/api/v1/azure-ad/callback")
        self.authority = os.getenv("AZURE_AD_AUTHORITY", "https://login.microsoftonline.com")
        self.graph_endpoint = os.getenv("AZURE_AD_GRAPH_ENDPOINT", "https://graph.microsoft.com/v1.0")
        self.cache_ttl = int(os.getenv("AZURE_AD_CACHE_TTL", "3600"))
        
        # Parse scopes from environment variable
        scopes_str = os.getenv("AZURE_AD_SCOPES", "")
        if scopes_str:
            self.scopes = [scope.strip() for scope in scopes_str.split(",")]
        else:
            self.scopes = [
                "https://graph.microsoft.com/User.Read",
                # "https://graph.microsoft.com/User.ReadBasic.All",
                # "https://graph.microsoft.com/Group.Read.All"
            ]
        
        # Check if Azure AD is configured
        if not self.is_configured():
            logger.warning("Azure AD is not properly configured. Please set AZURE_AD_CLIENT_ID, AZURE_AD_CLIENT_SECRET, and AZURE_AD_TENANT_ID")
            self.client = None
        else:
            # Initialize MSAL client
            authority_url = f"{self.authority}/{self.tenant_id}"
            self.client = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=authority_url
            )
        
        self._token_cache: Optional[AzureADTokenResponse] = None
        self._token_cache_time = 0
    
    def is_configured(self) -> bool:
        """Check if Azure AD is properly configured"""
        return bool(self.client_id and self.client_secret and self.tenant_id)
    
    def _check_configuration(self):
        """Check if Azure AD is properly configured"""
        if not self.is_configured():
            raise Exception("Azure AD is not properly configured. Please set AZURE_AD_CLIENT_ID, AZURE_AD_CLIENT_SECRET, and AZURE_AD_TENANT_ID")
        if not self.client:
            raise Exception("Azure AD client is not initialized")
    
    async def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get Azure AD authorization URL for OAuth2 flow"""
        self._check_configuration()
        
        auth_url = self.client.get_authorization_request_url(
            scopes=self.scopes,
            state=state,
            redirect_uri=self.redirect_uri
        )
        
        return auth_url
    
    async def exchange_code_for_token(self, authorization_code: str) -> AzureADTokenResponse:
        """Exchange authorization code for access token"""
        self._check_configuration()
        
        result = self.client.acquire_token_by_authorization_code(
            code=authorization_code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        if "error" in result:
            raise Exception(f"Token exchange failed: {result.get('error_description', result['error'])}")
        
        return AzureADTokenResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            scope=result.get("scope", ""),
            refresh_token=result.get("refresh_token")
        )
    
    async def get_client_credentials_token(self) -> AzureADTokenResponse:
        """Get access token using client credentials flow"""
        self._check_configuration()
        
        # Check cache first
        if self._token_cache and time.time() - self._token_cache_time < self.cache_ttl:
            return self._token_cache
        
        # For client credentials flow, use .default scope
        client_credentials_scopes = ["https://graph.microsoft.com/.default"]
        
        result = self.client.acquire_token_for_client(scopes=client_credentials_scopes)
        
        if "error" in result:
            raise Exception(f"Client credentials token failed: {result.get('error_description', result['error'])}")
        
        token_response = AzureADTokenResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            scope=result.get("scope", "")
        )
        
        # Cache the token
        self._token_cache = token_response
        self._token_cache_time = time.time()
        
        return token_response
    
    async def get_user_info(self, access_token: str) -> AzureADUserInfo:
        """Get current user information from Microsoft Graph API"""
        self._check_configuration()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.graph_endpoint}/me",
                headers=headers
            )
            response.raise_for_status()
            user_data = response.json()
        
        return AzureADUserInfo(
            id=user_data["id"],
            display_name=user_data.get("displayName", ""),
            given_name=user_data.get("givenName", ""),
            surname=user_data.get("surname", ""),
            user_principal_name=user_data.get("userPrincipalName", ""),
            mail=user_data.get("mail", ""),
            job_title=user_data.get("jobTitle"),
            department=user_data.get("department"),
            office_location=user_data.get("officeLocation"),
            mobile_phone=user_data.get("mobilePhone"),
            business_phones=user_data.get("businessPhones")
        )
    
    async def get_user_by_id(self, user_id: str, access_token: str) -> AzureADUserInfo:
        """Get user information by ID from Microsoft Graph API"""
        self._check_configuration()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.graph_endpoint}/users/{user_id}",
                headers=headers
            )
            response.raise_for_status()
            user_data = response.json()
        
        return AzureADUserInfo(
            id=user_data["id"],
            display_name=user_data.get("displayName", ""),
            given_name=user_data.get("givenName", ""),
            surname=user_data.get("surname", ""),
            user_principal_name=user_data.get("userPrincipalName", ""),
            mail=user_data.get("mail", ""),
            job_title=user_data.get("jobTitle"),
            department=user_data.get("department"),
            office_location=user_data.get("officeLocation"),
            mobile_phone=user_data.get("mobilePhone"),
            business_phones=user_data.get("businessPhones")
        )
    
    async def get_user_groups(self, user_id: str, access_token: str) -> List[dict]:
        """Get user's groups from Microsoft Graph API"""
        self._check_configuration()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.graph_endpoint}/users/{user_id}/memberOf",
                headers=headers
            )
            response.raise_for_status()
            groups_data = response.json()
        
        return groups_data.get("value", [])
    
    async def search_users(self, query: str, access_token: str) -> List[AzureADUserInfo]:
        """Search users in Azure AD"""
        self._check_configuration()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "$search": f'"{query}"',
            "$select": "id,displayName,givenName,surname,userPrincipalName,mail,jobTitle,department,officeLocation,mobilePhone,businessPhones"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.graph_endpoint}/users",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            users_data = response.json()
        
        users = []
        for user_data in users_data.get("value", []):
            user = AzureADUserInfo(
                id=user_data["id"],
                display_name=user_data.get("displayName", ""),
                given_name=user_data.get("givenName", ""),
                surname=user_data.get("surname", ""),
                user_principal_name=user_data.get("userPrincipalName", ""),
                mail=user_data.get("mail", ""),
                job_title=user_data.get("jobTitle"),
                department=user_data.get("department"),
                office_location=user_data.get("officeLocation"),
                mobile_phone=user_data.get("mobilePhone"),
                business_phones=user_data.get("businessPhones")
            )
            users.append(user)
        
        return users
    
    async def validate_token(self, access_token: str) -> bool:
        """Validate Azure AD access token"""
        self._check_configuration()
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.graph_endpoint}/me",
                    headers=headers
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False
