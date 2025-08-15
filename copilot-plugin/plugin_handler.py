"""
Microsoft Copilot Plugin Handler
Handles Copilot plugin operations and integrations
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class CopilotPluginHandler:
    """Handler for Microsoft Copilot plugin operations"""
    
    def __init__(self, base_url: str = None):
        # Use localhost for development, production URL for production
        import os
        if base_url is None:
            if os.getenv("ENVIRONMENT", "development") == "development":
                self.base_url = "http://localhost:8000"  # IRIS backend local port
            else:
                self.base_url = "https://iris.pnj.com.vn"  # Production URL
        else:
            self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def authenticate_user(self, access_token: str) -> Dict[str, Any]:
        """
        Authenticate user with Azure AD token
        
        Args:
            access_token: Azure AD access token
            
        Returns:
            User authentication info
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await self.client.get(
                f"{self.base_url}/api/v1/auth/me",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Authentication failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid access token")
    
    async def get_user_teams(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Get user's teams
        
        Args:
            access_token: Azure AD access token
            
        Returns:
            List of user's teams
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await self.client.get(
                f"{self.base_url}/api/v1/teams/teams",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            # Validate response structure
            if not isinstance(data, list):
                logger.warning(f"Unexpected response format for teams: {type(data)}")
                return []
            
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get teams: {e}")
            if e.response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid access token")
            elif e.response.status_code == 403:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            else:
                raise HTTPException(status_code=500, detail="Failed to retrieve teams")
    
    async def get_team_channels(self, access_token: str, team_id: str) -> List[Dict[str, Any]]:
        """
        Get channels for a specific team
        
        Args:
            access_token: Azure AD access token
            team_id: Team ID
            
        Returns:
            List of team channels
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await self.client.get(
                f"{self.base_url}/api/v1/teams/teams/{team_id}/channels",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get channels: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve channels")
    
    async def send_team_message(
        self, 
        access_token: str, 
        team_id: str, 
        channel_id: str, 
        content: str
    ) -> Dict[str, Any]:
        """
        Send message to Teams channel
        
        Args:
            access_token: Azure AD access token
            team_id: Team ID
            channel_id: Channel ID
            content: Message content
            
        Returns:
            Sent message info
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            payload = {
                "team_id": team_id,
                "channel_id": channel_id,
                "content": content,
                "content_type": "text"
            }
            response = await self.client.post(
                f"{self.base_url}/api/v1/teams/teams/{team_id}/channels/{channel_id}/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send message: {e}")
            raise HTTPException(status_code=500, detail="Failed to send message")
    
    async def process_chat_query(
        self, 
        access_token: str, 
        query: str, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process chat query with RAG
        
        Args:
            access_token: Azure AD access token
            query: User query
            session_id: Chat session ID
            context: Additional context
            
        Returns:
            Chat response with sources
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            payload = {
                "query": query,
                "session_id": session_id,
                "context": context,
                "use_rag": True,
                "max_sources": 5
            }
            response = await self.client.post(
                f"{self.base_url}/api/v1/copilot/chat",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to process chat query: {e}")
            raise HTTPException(status_code=500, detail="Failed to process query")
    
    async def search_documents(
        self, 
        access_token: str, 
        query: str, 
        search_type: str = "semantic",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search documents using semantic search
        
        Args:
            access_token: Azure AD access token
            query: Search query
            search_type: Type of search (semantic, keyword, hybrid)
            limit: Number of results
            
        Returns:
            Search results
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            payload = {
                "query": query,
                "search_type": search_type,
                "limit": limit,
                "threshold": 0.7
            }
            response = await self.client.post(
                f"{self.base_url}/api/v1/copilot/search",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to search documents: {e}")
            raise HTTPException(status_code=500, detail="Failed to search documents")
    
    async def get_chat_history(
        self, 
        access_token: str, 
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get chat history
        
        Args:
            access_token: Azure AD access token
            session_id: Chat session ID
            
        Returns:
            Chat history
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {"session_id": session_id} if session_id else {}
            response = await self.client.get(
                f"{self.base_url}/api/v1/chat/history",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get chat history: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve chat history")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Health check for the plugin
        
        Returns:
            Health status
        """
        try:
            # Check if we're in development mode
            import os
            if os.getenv("ENVIRONMENT", "development") == "development":
                # Mock health check for development
                return {
                    "status": "healthy",
                    "message": "Plugin running in development mode",
                    "iris_api": "mock",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Real health check for production
            response = await self.client.get(f"{self.base_url}/api/v1/copilot/health")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global plugin handler instance
plugin_handler = CopilotPluginHandler()
