"""
Microsoft Copilot Plugin Server
FastAPI server để xử lý requests từ Microsoft Copilot
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

from plugin_handler import CopilotPluginHandler
from oauth2_handler import oauth2_handler, OAuth2CallbackRequest, OAuth2TokenResponse
from agent_handler import agent_handler

# Load environment variables
# Try to load .env first, then env.local for development
load_dotenv()
load_dotenv("env.local", override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="IRIS Copilot Plugin",
    description="Plugin server cho Microsoft Copilot integration",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=json.loads(os.getenv("CORS_ORIGINS", '["https://iris.pnj.com.vn", "https://copilot.microsoft.com"]')),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize plugin handler
plugin_handler = CopilotPluginHandler()

# Request/Response Models
class CopilotRequest(BaseModel):
    """Request model từ Microsoft Copilot"""
    query: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class AgentRequest(BaseModel):
    """Request model từ Microsoft Copilot Agent"""
    intent: str
    parameters: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

class CopilotResponse(BaseModel):
    """Response model cho Microsoft Copilot"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]

# Dependency để validate token
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Validate access token"""
    try:
        # Check if we're in development mode
        import os
        if os.getenv("ENVIRONMENT", "development") == "development":
            # Allow mock token for development
            if credentials.credentials == "mock-token":
                return "mock-token"
        
        # Trong production, bạn nên validate token với Azure AD
        # Hiện tại chỉ kiểm tra token có tồn tại
        if not credentials.credentials:
            raise HTTPException(status_code=401, detail="Invalid token")
        return credentials.credentials
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check IRIS API health
        iris_health = await plugin_handler.health_check()
        
        return HealthResponse(
            status="healthy" if iris_health.get("status") == "healthy" else "unhealthy",
            version=os.getenv("PLUGIN_VERSION", "1.0.0"),
            timestamp=datetime.utcnow(),
            services={
                "plugin": "healthy",
                "iris_api": iris_health.get("status", "unknown")
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version=os.getenv("PLUGIN_VERSION", "1.0.0"),
            timestamp=datetime.utcnow(),
            services={
                "plugin": "unhealthy",
                "iris_api": "unreachable"
            }
        )

# Main Copilot endpoint
@app.post("/copilot/process", response_model=CopilotResponse)
async def process_copilot_request(
    request: CopilotRequest,
    access_token: str = Depends(validate_token)
):
    """Main endpoint để xử lý requests từ Microsoft Copilot"""
    
    try:
        logger.info(f"Processing Copilot request: {request.query}")
        
        # Process request based on query type
        if "team" in request.query.lower() or "teams" in request.query.lower():
            # Teams-related request
            if "list" in request.query.lower() or "show" in request.query.lower():
                teams = await plugin_handler.get_user_teams(access_token)
                return CopilotResponse(
                    success=True,
                    data={"teams": teams},
                    message=f"Found {len(teams)} teams"
                )
            elif "send" in request.query.lower() and "message" in request.query.lower():
                # Extract team and channel info from context
                context = request.context or {}
                team_id = context.get("team_id")
                channel_id = context.get("channel_id")
                message = context.get("message", request.query)
                
                if team_id and channel_id:
                    result = await plugin_handler.send_team_message(
                        access_token, team_id, channel_id, message
                    )
                    return CopilotResponse(
                        success=True,
                        data={"message": result},
                        message="Message sent successfully"
                    )
                else:
                    return CopilotResponse(
                        success=False,
                        error="Team ID and Channel ID are required for sending messages"
                    )
        
        elif "search" in request.query.lower() or "find" in request.query.lower():
            # Document search request
            results = await plugin_handler.search_documents(
                access_token, request.query, "semantic", 10
            )
            return CopilotResponse(
                success=True,
                data={"search_results": results},
                message=f"Found {results.get('total_count', 0)} documents"
            )
        
        elif "chat" in request.query.lower() or "help" in request.query.lower():
            # Chat/RAG request
            response = await plugin_handler.process_chat_query(
                access_token, request.query, request.session_id, request.context
            )
            return CopilotResponse(
                success=True,
                data={"chat_response": response},
                message="Chat response generated"
            )
        
        else:
            # Default to chat processing
            response = await plugin_handler.process_chat_query(
                access_token, request.query, request.session_id, request.context
            )
            return CopilotResponse(
                success=True,
                data={"response": response},
                message="Request processed successfully"
            )
    
    except Exception as e:
        logger.error(f"Error processing Copilot request: {e}")
        return CopilotResponse(
            success=False,
            error=str(e)
        )

# Teams endpoints
@app.get("/teams", response_model=CopilotResponse)
async def get_teams(access_token: str = Depends(validate_token)):
    """Get user's teams"""
    try:
        teams = await plugin_handler.get_user_teams(access_token)
        return CopilotResponse(
            success=True,
            data={"teams": teams},
            message=f"Found {len(teams)} teams"
        )
    except Exception as e:
        logger.error(f"Error getting teams: {e}")
        return CopilotResponse(
            success=False,
            error=str(e)
        )

@app.get("/teams/{team_id}/channels", response_model=CopilotResponse)
async def get_channels(
    team_id: str,
    access_token: str = Depends(validate_token)
):
    """Get channels for a team"""
    try:
        channels = await plugin_handler.get_team_channels(access_token, team_id)
        return CopilotResponse(
            success=True,
            data={"channels": channels},
            message=f"Found {len(channels)} channels"
        )
    except Exception as e:
        logger.error(f"Error getting channels: {e}")
        return CopilotResponse(
            success=False,
            error=str(e)
        )

# Search endpoint
@app.post("/search", response_model=CopilotResponse)
async def search_documents(
    request: CopilotRequest,
    access_token: str = Depends(validate_token)
):
    """Search documents"""
    try:
        results = await plugin_handler.search_documents(
            access_token, request.query, "semantic", 10
        )
        return CopilotResponse(
            success=True,
            data={"search_results": results},
            message=f"Found {results.get('total_count', 0)} documents"
        )
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return CopilotResponse(
            success=False,
            error=str(e)
        )

# Chat endpoint
@app.post("/chat", response_model=CopilotResponse)
async def chat(
    request: CopilotRequest,
    access_token: str = Depends(validate_token)
):
    """Chat with RAG"""
    try:
        response = await plugin_handler.process_chat_query(
            access_token, request.query, request.session_id, request.context
        )
        return CopilotResponse(
            success=True,
            data={"chat_response": response},
            message="Chat response generated"
        )
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        return CopilotResponse(
            success=False,
            error=str(e)
        )

# Agent endpoint
@app.post("/agent/process", response_model=CopilotResponse)
async def process_agent_request(
    request: AgentRequest,
    access_token: str = Depends(validate_token)
):
    """Process agent request with intent recognition"""
    try:
        logger.info(f"Processing agent request: {request.intent}")
        
        # Process with agent handler
        result = await agent_handler.process_agent_request(
            access_token, {
                "intent": request.intent,
                "parameters": request.parameters or {},
                "context": request.context or {}
            }
        )
        
        return CopilotResponse(
            success=result.get("success", False),
            data=result,
            message=result.get("message", "Agent request processed")
        )
        
    except Exception as e:
        logger.error(f"Error processing agent request: {e}")
        return CopilotResponse(
            success=False,
            error=str(e)
        )

# OAuth2 Callback endpoint
@app.get("/api/v1/azure-ad/callback")
async def oauth2_callback(
    code: str,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None
):
    """OAuth2 callback endpoint for Azure AD authentication"""
    try:
        logger.info(f"OAuth2 callback received: code={code[:10]}..., state={state}")
        
        # Check for OAuth2 errors
        if error:
            logger.error(f"OAuth2 error: {error} - {error_description}")
            return {
                "success": False,
                "error": error,
                "error_description": error_description
            }
        
        # Exchange code for token
        token_response = await oauth2_handler.exchange_code_for_token(code)
        
        # Get user information
        user_info = await oauth2_handler.get_user_info(token_response.access_token)
        
        # Store token securely (in production, use Redis/database)
        # For now, return token info
        return {
            "success": True,
            "access_token": token_response.access_token,
            "token_type": token_response.token_type,
            "expires_in": token_response.expires_in,
            "user_info": user_info,
            "message": "Authentication successful"
        }
        
    except Exception as e:
        logger.error(f"OAuth2 callback error: {e}")
        return {
            "success": False,
            "error": "Authentication failed",
            "error_description": str(e)
        }

# OAuth2 Token validation endpoint
@app.post("/api/v1/azure-ad/validate")
async def validate_token(request: Request):
    """Validate OAuth2 access token"""
    try:
        body = await request.json()
        access_token = body.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Access token required")
        
        # Validate token
        is_valid = await oauth2_handler.validate_token(access_token)
        
        if is_valid:
            # Get user info
            user_info = await oauth2_handler.get_user_info(access_token)
            return {
                "success": True,
                "valid": True,
                "user_info": user_info
            }
        else:
            return {
                "success": True,
                "valid": False,
                "message": "Token is invalid or expired"
            }
            
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return {
            "success": False,
            "error": "Token validation failed",
            "error_description": str(e)
        }

# OAuth2 Token refresh endpoint
@app.post("/api/v1/azure-ad/refresh")
async def refresh_token(request: Request):
    """Refresh OAuth2 access token"""
    try:
        body = await request.json()
        refresh_token_value = body.get("refresh_token")
        
        if not refresh_token_value:
            raise HTTPException(status_code=400, detail="Refresh token required")
        
        # Refresh token
        token_response = await oauth2_handler.refresh_token(refresh_token_value)
        
        return {
            "success": True,
            "access_token": token_response.access_token,
            "token_type": token_response.token_type,
            "expires_in": token_response.expires_in,
            "refresh_token": token_response.refresh_token,
            "message": "Token refreshed successfully"
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return {
            "success": False,
            "error": "Token refresh failed",
            "error_description": str(e)
        }

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    # Implement metrics collection here
    return {"status": "metrics endpoint"}

# Error handling middleware
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}")
    return CopilotResponse(
        success=False,
        error=str(exc)
    )

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting IRIS Copilot Plugin server on {host}:{port}")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
