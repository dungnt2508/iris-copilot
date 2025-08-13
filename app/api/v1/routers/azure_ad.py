"""
Azure AD API Router
Handles Azure AD authentication endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.application.user.use_cases.azure_ad_login import (
    AzureADLoginUseCase,
    AzureADLoginRequest,
    SyncAzureADUsersUseCase
)
from app.adapters.azure_ad_adapter import AzureADAdapter
from app.domain.user.repository import UserRepository
from app.core.logger import get_logger
from ..dependencies import get_user_repository, get_azure_ad_adapter

logger = get_logger(__name__)

router = APIRouter(prefix="/azure-ad", tags=["Azure AD"])


class AzureADLoginRequestModel(BaseModel):
    """Request model for Azure AD login"""
    authorization_code: str
    state: Optional[str] = None


class AzureADLoginResponseModel(BaseModel):
    """Response model for Azure AD login"""
    user_id: str
    email: str
    username: str
    full_name: str
    role: str
    is_new_user: bool
    azure_ad_user: dict
    jwt_tokens: dict
    access_token: Optional[str] = None  # Azure AD access token for Graph API calls


class SyncUsersRequestModel(BaseModel):
    """Request model for syncing users"""
    query: Optional[str] = ""


class SyncUsersResponseModel(BaseModel):
    """Response model for syncing users"""
    total_synced: int
    created: int
    updated: int
    query: str


@router.get("/auth")
async def get_azure_ad_auth_url(
    state: Optional[str] = Query(None, description="State parameter for security"),
    azure_ad_adapter: AzureADAdapter = Depends(get_azure_ad_adapter)
):
    """
    Get Azure AD authorization URL for OAuth2 flow
    
    This endpoint returns the URL that users should visit to authenticate with Azure AD.
    After successful authentication, Azure AD will redirect back to the callback endpoint.
    """
    try:
        auth_url = await azure_ad_adapter.get_authorization_url(state)
        return {
            "auth_url": auth_url,
            "state": state
        }
    except Exception as e:
        logger.error(f"Failed to generate Azure AD auth URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate authorization URL")


@router.get("/callback")
async def azure_ad_callback(
    code: Optional[str] = Query(None, description="Authorization code from Azure AD"),
    state: Optional[str] = Query(None, description="State parameter"),
    error: Optional[str] = Query(None, description="Error from Azure AD"),
    error_description: Optional[str] = Query(None, description="Error description from Azure AD"),
    request: Request = None,
    user_repository: UserRepository = Depends(get_user_repository),
    azure_ad_adapter: AzureADAdapter = Depends(get_azure_ad_adapter)
):
    """
    Azure AD OAuth2 callback endpoint
    
    This endpoint handles the redirect from Azure AD after successful authentication.
    It exchanges the authorization code for an access token and creates/updates the user.
    """
    # Check if there's an error from Azure AD
    if error:
        logger.error(f"Azure AD returned error: {error} - {error_description}")
        frontend_url = "https://infra-inno.pnj.com.vn/rest/oauth2-credential/callback"
        error_url = f"{frontend_url}?error={error}&message={error_description}&status=error"
        return RedirectResponse(url=error_url)
    
    # Check if we have the required authorization code
    if not code:
        logger.error("No authorization code received from Azure AD")
        frontend_url = "https://infra-inno.pnj.com.vn/rest/oauth2-credential/callback"
        error_url = f"{frontend_url}?error=missing_code&message=No authorization code received&status=error"
        return RedirectResponse(url=error_url)
    
    try:
        # Create use case
        login_use_case = AzureADLoginUseCase(user_repository, azure_ad_adapter)
        
        # Execute login
        login_request = AzureADLoginRequest(authorization_code=code, state=state)
        login_response = await login_use_case.execute(login_request)
        
        # Generate JWT token for our system
        # Note: In a real implementation, you would use your JWT service here
        jwt_token = "your-jwt-token-generation-logic"
        
        # Redirect to frontend with token
        frontend_url = "https://infra-inno.pnj.com.vn/rest/oauth2-credential/callback"
        redirect_url = f"{frontend_url}?token={jwt_token}&user_id={login_response.user.id}&status=success&email={login_response.user.email}"
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"Azure AD callback failed: {e}")
        # Redirect to frontend with error
        frontend_url = "https://infra-inno.pnj.com.vn/rest/oauth2-credential/callback"
        error_url = f"{frontend_url}?error=azure_ad_auth_failed&message={str(e)}&status=error"
        return RedirectResponse(url=error_url)


@router.post("/login", response_model=AzureADLoginResponseModel)
async def azure_ad_login(
    request: AzureADLoginRequestModel,
    user_repository: UserRepository = Depends(get_user_repository),
    azure_ad_adapter: AzureADAdapter = Depends(get_azure_ad_adapter)
):
    """
    Azure AD login endpoint
    
    This endpoint handles the OAuth2 authorization code exchange and user creation/update.
    It's typically called by the frontend after receiving the authorization code.
    """
    try:
        # Create use case
        login_use_case = AzureADLoginUseCase(user_repository, azure_ad_adapter)
        
        # Execute login
        login_request = AzureADLoginRequest(
            authorization_code=request.authorization_code,
            state=request.state
        )
        login_response = await login_use_case.execute(login_request)
        
        return AzureADLoginResponseModel(
            user_id=login_response.user.id,
            email=login_response.user.email,
            username=login_response.user.username,
            full_name=login_response.user.full_name,
            role=login_response.user.role.value if hasattr(login_response.user.role, 'value') else str(login_response.user.role),
            is_new_user=login_response.is_new_user,
            azure_ad_user=login_response.azure_ad_user.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Azure AD login failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync-users", response_model=SyncUsersResponseModel)
async def sync_azure_ad_users(
    request: SyncUsersRequestModel,
    user_repository: UserRepository = Depends(get_user_repository),
    azure_ad_adapter: AzureADAdapter = Depends(get_azure_ad_adapter)
):
    """
    Sync users from Azure AD
    
    This endpoint allows administrators to bulk sync users from Azure AD.
    It can be used to import users or update existing user information.
    """
    try:
        # Create use case
        sync_use_case = SyncAzureADUsersUseCase(user_repository, azure_ad_adapter)
        
        # Execute sync
        result = await sync_use_case.execute(request.query)
        
        return SyncUsersResponseModel(
            total_synced=result["total_synced"],
            created=result["created"],
            updated=result["updated"],
            query=result["query"]
        )
        
    except Exception as e:
        logger.error(f"Azure AD sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exchange-code", response_model=AzureADLoginResponseModel)
async def exchange_authorization_code(
    request: AzureADLoginRequestModel,
    user_repository: UserRepository = Depends(get_user_repository),
    azure_ad_adapter: AzureADAdapter = Depends(get_azure_ad_adapter)
):
    """
    Exchange authorization code for user information
    
    This endpoint is called by the frontend after receiving the authorization code
    from Azure AD callback. It exchanges the code for user information and creates/updates the user.
    """
    try:
        # Get token service from dependencies
        from app.services.token_service import TokenService
        from app.core.config import settings
        
        token_service = TokenService(
            secret_key=settings.secret_key,
            access_token_expire_minutes=settings.access_token_expire_minutes,
            refresh_token_expire_days=settings.refresh_token_expire_days
        )
        
        # Create use case
        login_use_case = AzureADLoginUseCase(user_repository, azure_ad_adapter, token_service)
        
        # Execute login
        login_request = AzureADLoginRequest(
            authorization_code=request.authorization_code,
            state=request.state
        )
        login_response = await login_use_case.execute(login_request)
        
        return AzureADLoginResponseModel(
            user_id=login_response.user.id,
            email=login_response.user.email,
            username=login_response.user.username,
            full_name=login_response.user.full_name,
            role=login_response.user.role.value if hasattr(login_response.user.role, 'value') else str(login_response.user.role),
            is_new_user=login_response.is_new_user,
            azure_ad_user=login_response.azure_ad_user.to_dict(),
            jwt_tokens=login_response.jwt_tokens,
            access_token=login_response.access_token  # Azure AD access token
        )
        
    except Exception as e:
        logger.error(f"Authorization code exchange failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/validate-token")
async def validate_azure_ad_token(
    token: str = Query(..., description="Azure AD access token to validate"),
    azure_ad_adapter: AzureADAdapter = Depends(get_azure_ad_adapter)
):
    """
    Validate Azure AD access token
    
    This endpoint validates an Azure AD access token by calling the Microsoft Graph API.
    """
    try:
        is_valid = await azure_ad_adapter.validate_token(token)
        return {
            "valid": is_valid,
            "token": token[:20] + "..." if len(token) > 20 else token
        }
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user-info")
async def get_azure_ad_user_info(
    token: str = Query(..., description="Azure AD access token"),
    azure_ad_adapter: AzureADAdapter = Depends(get_azure_ad_adapter)
):
    """
    Get user information from Azure AD
    
    This endpoint retrieves the current user's information from Azure AD using the provided token.
    """
    try:
        user_info = await azure_ad_adapter.get_user_info(token)
        return user_info.to_dict()
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search-users")
async def search_azure_ad_users(
    query: str = Query(..., description="Search query for users"),
    token: str = Query(..., description="Azure AD access token"),
    azure_ad_adapter: AzureADAdapter = Depends(get_azure_ad_adapter)
):
    """
    Search users in Azure AD
    
    This endpoint searches for users in Azure AD based on the provided query.
    """
    try:
        users = await azure_ad_adapter.search_users(query, token)
        return {
            "users": [user.to_dict() for user in users],
            "count": len(users),
            "query": query
        }
    except Exception as e:
        logger.error(f"Failed to search users: {e}")
        raise HTTPException(status_code=400, detail=str(e))
