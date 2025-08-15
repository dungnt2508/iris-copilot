"""
OAuth2 Callback Handler for Microsoft Copilot Plugin
Handles OAuth2 authentication flow with Azure AD
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from fastapi import HTTPException, Request, Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OAuth2CallbackRequest(BaseModel):
    """OAuth2 callback request model"""
    code: str
    state: Optional[str] = None
    error: Optional[str] = None
    error_description: Optional[str] = None


class OAuth2TokenResponse(BaseModel):
    """OAuth2 token response model"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: str
    id_token: Optional[str] = None


class OAuth2Handler:
    """Handler for OAuth2 authentication flow"""
    
    def __init__(self):
        self.client_id = os.getenv("AZURE_AD_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_AD_CLIENT_SECRET")
        self.tenant_id = os.getenv("AZURE_AD_TENANT_ID")
        self.redirect_uri = os.getenv("AZURE_AD_REDIRECT_URI")
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Validate required environment variables
        if not all([self.client_id, self.client_secret, self.tenant_id, self.redirect_uri]):
            logger.warning("Missing Azure AD configuration. OAuth2 will not work properly.")
    
    async def exchange_code_for_token(self, code: str) -> OAuth2TokenResponse:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from Azure AD
            
        Returns:
            OAuth2TokenResponse with access token
        """
        try:
            # Check if this is an enterprise SSO code
            if code.startswith("enterprise_"):
                return await self.exchange_enterprise_code_for_token(code)
            
            # Standard Azure AD flow
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code",
                "scope": "https://graph.microsoft.com/User.Read https://graph.microsoft.com/Team.ReadBasic.All https://graph.microsoft.com/Channel.ReadBasic.All https://graph.microsoft.com/ChannelMessage.Send"
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = await self.client.post(token_url, data=payload, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            return OAuth2TokenResponse(**token_data)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Token exchange failed: {e}")
            logger.error(f"Response: {e.response.text}")
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def exchange_enterprise_code_for_token(self, enterprise_code: str) -> OAuth2TokenResponse:
        """
        Exchange enterprise SSO code for access token
        
        Args:
            enterprise_code: Enterprise SSO authorization code
            
        Returns:
            OAuth2TokenResponse with access token
        """
        try:
            # Call enterprise SSO endpoint
            enterprise_sso_url = "https://infra-inno.pnj.com.vn/rest/oauth2-credential/exchange"
            
            payload = {
                "code": enterprise_code,
                "client_id": self.client_id,
                "grant_type": "authorization_code"
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = await self.client.post(enterprise_sso_url, json=payload, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            return OAuth2TokenResponse(**token_data)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Enterprise token exchange failed: {e}")
            logger.error(f"Response: {e.response.text}")
            raise HTTPException(status_code=400, detail="Failed to exchange enterprise code for token")
        except Exception as e:
            logger.error(f"Enterprise token exchange error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Microsoft Graph API
        
        Args:
            access_token: Valid access token
            
        Returns:
            User information
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = await self.client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=headers
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get user info: {e}")
            raise HTTPException(status_code=401, detail="Invalid access token")
        except Exception as e:
            logger.error(f"User info error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def validate_token(self, access_token: str) -> bool:
        """
        Validate access token with Microsoft Graph API
        
        Args:
            access_token: Access token to validate
            
        Returns:
            True if token is valid
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = await self.client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False
    
    async def refresh_token(self, refresh_token: str) -> OAuth2TokenResponse:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New OAuth2TokenResponse
        """
        try:
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": "https://graph.microsoft.com/User.Read https://graph.microsoft.com/Team.ReadBasic.All https://graph.microsoft.com/Channel.ReadBasic.All https://graph.microsoft.com/ChannelMessage.Send"
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = await self.client.post(token_url, data=payload, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            return OAuth2TokenResponse(**token_data)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Token refresh failed: {e}")
            raise HTTPException(status_code=400, detail="Failed to refresh token")
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global OAuth2 handler instance
oauth2_handler = OAuth2Handler()
