"""
Microsoft Copilot Plugin Handler
Xử lý các requests từ Microsoft Copilot và chuyển tiếp đến IRIS API
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="IRIS Copilot Plugin", version="1.0.0")

# Security
security = HTTPBearer()

# Configuration
IRIS_API_URL = os.getenv("IRIS_API_URL", "http://localhost:8000")
PLUGIN_SECRET = os.getenv("PLUGIN_SECRET", "your-secret-key")

class CopilotRequest(BaseModel):
    """Request model từ Microsoft Copilot"""
    user_id: str
    intent: str
    parameters: Dict[str, Any] = {}
    context: Dict[str, Any] = {}

class CopilotResponse(BaseModel):
    """Response model cho Microsoft Copilot"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None

class PluginHandler:
    """Handler chính cho Copilot Plugin"""
    
    def __init__(self):
        self.iris_api_url = IRIS_API_URL
        self.client = httpx.AsyncClient()
    
    async def handle_request(self, request: CopilotRequest, access_token: str) -> CopilotResponse:
        """Xử lý request từ Copilot dựa trên intent"""
        
        try:
            logger.info(f"Handling Copilot request: {request.intent}")
            
            # Map intent đến action
            if request.intent == "get_teams":
                return await self._get_teams(access_token)
            
            elif request.intent == "get_channels":
                team_id = request.parameters.get("team_id")
                if not team_id:
                    return CopilotResponse(
                        success=False,
                        error="team_id is required"
                    )
                return await self._get_channels(team_id, access_token)
            
            elif request.intent == "send_message":
                return await self._send_message(request.parameters, access_token)
            
            elif request.intent == "get_chats":
                return await self._get_chats(access_token)
            
            elif request.intent == "get_calendars":
                return await self._get_calendars(access_token)
            
            elif request.intent == "get_events":
                calendar_id = request.parameters.get("calendar_id")
                if not calendar_id:
                    return CopilotResponse(
                        success=False,
                        error="calendar_id is required"
                    )
                return await self._get_events(calendar_id, access_token)
            
            else:
                return CopilotResponse(
                    success=False,
                    error=f"Unknown intent: {request.intent}"
                )
                
        except Exception as e:
            logger.error(f"Error handling Copilot request: {e}")
            return CopilotResponse(
                success=False,
                error=str(e)
            )
    
    async def _get_teams(self, access_token: str) -> CopilotResponse:
        """Lấy danh sách teams"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await self.client.get(
                f"{self.iris_api_url}/api/v1/teams/teams",
                headers=headers
            )
            response.raise_for_status()
            
            teams = response.json()
            return CopilotResponse(
                success=True,
                data={"teams": teams},
                message=f"Found {len(teams)} teams"
            )
            
        except Exception as e:
            logger.error(f"Error getting teams: {e}")
            return CopilotResponse(
                success=False,
                error=f"Failed to get teams: {str(e)}"
            )
    
    async def _get_channels(self, team_id: str, access_token: str) -> CopilotResponse:
        """Lấy danh sách channels của team"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await self.client.get(
                f"{self.iris_api_url}/api/v1/teams/teams/{team_id}/channels",
                headers=headers
            )
            response.raise_for_status()
            
            channels = response.json()
            return CopilotResponse(
                success=True,
                data={"channels": channels},
                message=f"Found {len(channels)} channels in team {team_id}"
            )
            
        except Exception as e:
            logger.error(f"Error getting channels: {e}")
            return CopilotResponse(
                success=False,
                error=f"Failed to get channels: {str(e)}"
            )
    
    async def _send_message(self, parameters: Dict[str, Any], access_token: str) -> CopilotResponse:
        """Gửi tin nhắn"""
        try:
            team_id = parameters.get("team_id")
            channel_id = parameters.get("channel_id")
            chat_id = parameters.get("chat_id")
            content = parameters.get("content")
            
            if not content:
                return CopilotResponse(
                    success=False,
                    error="Message content is required"
                )
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "content": content,
                "content_type": "text"
            }
            
            # Gửi đến channel hoặc chat
            if team_id and channel_id:
                url = f"{self.iris_api_url}/api/v1/teams/teams/{team_id}/channels/{channel_id}/messages"
                message_type = "channel"
            elif chat_id:
                url = f"{self.iris_api_url}/api/v1/teams/chats/{chat_id}/messages"
                message_type = "chat"
            else:
                return CopilotResponse(
                    success=False,
                    error="Either team_id+channel_id or chat_id is required"
                )
            
            response = await self.client.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            message = response.json()
            return CopilotResponse(
                success=True,
                data={"message": message},
                message=f"Message sent successfully to {message_type}"
            )
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return CopilotResponse(
                success=False,
                error=f"Failed to send message: {str(e)}"
            )
    
    async def _get_chats(self, access_token: str) -> CopilotResponse:
        """Lấy danh sách group chats"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await self.client.get(
                f"{self.iris_api_url}/api/v1/teams/chats",
                headers=headers
            )
            response.raise_for_status()
            
            chats = response.json()
            return CopilotResponse(
                success=True,
                data={"chats": chats},
                message=f"Found {len(chats)} group chats"
            )
            
        except Exception as e:
            logger.error(f"Error getting chats: {e}")
            return CopilotResponse(
                success=False,
                error=f"Failed to get chats: {str(e)}"
            )
    
    async def _get_calendars(self, access_token: str) -> CopilotResponse:
        """Lấy danh sách calendars"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await self.client.get(
                f"{self.iris_api_url}/api/v1/calendar/calendars",
                headers=headers
            )
            response.raise_for_status()
            
            calendars = response.json()
            return CopilotResponse(
                success=True,
                data={"calendars": calendars},
                message=f"Found {len(calendars)} calendars"
            )
            
        except Exception as e:
            logger.error(f"Error getting calendars: {e}")
            return CopilotResponse(
                success=False,
                error=f"Failed to get calendars: {str(e)}"
            )
    
    async def _get_events(self, calendar_id: str, access_token: str) -> CopilotResponse:
        """Lấy events từ calendar"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await self.client.get(
                f"{self.iris_api_url}/api/v1/calendar/calendars/{calendar_id}/events",
                headers=headers
            )
            response.raise_for_status()
            
            events = response.json()
            return CopilotResponse(
                success=True,
                data={"events": events},
                message=f"Found {len(events)} events in calendar {calendar_id}"
            )
            
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return CopilotResponse(
                success=False,
                error=f"Failed to get events: {str(e)}"
            )

# Initialize handler
handler = PluginHandler()

@app.post("/copilot/process", response_model=CopilotResponse)
async def process_copilot_request(
    request: CopilotRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Endpoint chính để xử lý requests từ Microsoft Copilot"""
    
    try:
        # Validate plugin secret (optional additional security)
        # if credentials.credentials != PLUGIN_SECRET:
        #     raise HTTPException(status_code=401, detail="Invalid plugin secret")
        
        # Extract user's access token from context or use plugin token
        user_access_token = request.context.get("access_token", credentials.credentials)
        
        # Process request
        response = await handler.handle_request(request, user_access_token)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing Copilot request: {e}")
        return CopilotResponse(
            success=False,
            error=str(e)
        )

@app.get("/copilot/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "IRIS Copilot Plugin"}

@app.get("/copilot/capabilities")
async def get_capabilities():
    """Trả về danh sách capabilities của plugin"""
    return {
        "capabilities": [
            {
                "intent": "get_teams",
                "description": "Lấy danh sách teams của user",
                "parameters": []
            },
            {
                "intent": "get_channels",
                "description": "Lấy danh sách channels của team",
                "parameters": ["team_id"]
            },
            {
                "intent": "send_message",
                "description": "Gửi tin nhắn đến channel hoặc chat",
                "parameters": ["content", "team_id", "channel_id", "chat_id"]
            },
            {
                "intent": "get_chats",
                "description": "Lấy danh sách group chats",
                "parameters": []
            },
            {
                "intent": "get_calendars",
                "description": "Lấy danh sách calendars",
                "parameters": []
            },
            {
                "intent": "get_events",
                "description": "Lấy events từ calendar",
                "parameters": ["calendar_id"]
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
