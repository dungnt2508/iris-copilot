"""
Teams Adapter
Handles Microsoft Teams API operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
from dataclasses import dataclass

from ..core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TeamsMessage:
    """Teams message data model"""
    id: str
    content: str
    created_datetime: Optional[datetime] = None
    last_modified_datetime: Optional[datetime] = None
    from_user: Optional[Dict[str, Any]] = None
    attachments: List[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "created_datetime": self.created_datetime.isoformat() if self.created_datetime else None,
            "last_modified_datetime": self.last_modified_datetime.isoformat() if self.last_modified_datetime else None,
            "from_user": self.from_user,
            "attachments": self.attachments or []
        }


@dataclass
class TeamsChannel:
    """Teams channel data model"""
    id: str
    display_name: str
    description: Optional[str] = None
    is_default: bool = False
    membership_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "description": self.description,
            "is_default": self.is_default,
            "membership_type": self.membership_type
        }


@dataclass
class TeamsTeam:
    """Teams team data model"""
    id: str
    display_name: str
    description: Optional[str] = None
    visibility: Optional[str] = None
    created_datetime: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "description": self.description,
            "visibility": self.visibility,
            "created_datetime": self.created_datetime.isoformat() if self.created_datetime else None
        }


class TeamsAdapter:
    """
    Adapter for Microsoft Teams API
    Handles teams, channels, and messaging operations
    """
    
    def __init__(self, graph_endpoint: str = "https://graph.microsoft.com/v1.0"):
        self.graph_endpoint = graph_endpoint
    
    async def get_user_teams(self, access_token: str) -> List[TeamsTeam]:
        """
        Get user's teams
        
        Args:
            access_token: Azure AD access token
            
        Returns:
            List of user's teams
        """
        try:
            url = f"{self.graph_endpoint}/me/joinedTeams"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Calling Teams API: {url}")
            logger.info(f"Token preview: {access_token[:20]}...")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response headers: {dict(response.headers)}")
                
                if response.status_code != 200:
                    logger.error(f"Response body: {response.text}")
                
                response.raise_for_status()
                
                data = response.json()
                teams = []
                
                for team_data in data.get("value", []):
                    # Parse created datetime
                    created_datetime = None
                    if team_data.get("createdDateTime"):
                        created_datetime = datetime.fromisoformat(
                            team_data["createdDateTime"].replace('Z', '+00:00')
                        )
                    
                    team = TeamsTeam(
                        id=team_data.get("id"),
                        display_name=team_data.get("displayName"),
                        description=team_data.get("description"),
                        visibility=team_data.get("visibility"),
                        created_datetime=created_datetime
                    )
                    teams.append(team)
                
                logger.info(f"Retrieved {len(teams)} teams for user")
                return teams
                
        except Exception as e:
            logger.error(f"Failed to get user teams: {e}")
            raise
    
    async def get_team_channels(
        self, 
        access_token: str, 
        team_id: str
    ) -> List[TeamsChannel]:
        """
        Get channels for a specific team
        
        Args:
            access_token: Azure AD access token
            team_id: Team ID
            
        Returns:
            List of team channels
        """
        try:
            url = f"{self.graph_endpoint}/teams/{team_id}/channels"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                channels = []
                
                for channel_data in data.get("value", []):
                    channel = TeamsChannel(
                        id=channel_data.get("id"),
                        display_name=channel_data.get("displayName"),
                        description=channel_data.get("description"),
                        is_default=channel_data.get("isDefault", False),
                        membership_type=channel_data.get("membershipType")
                    )
                    channels.append(channel)
                
                logger.info(f"Retrieved {len(channels)} channels for team {team_id}")
                return channels
                
        except Exception as e:
            logger.error(f"Failed to get team channels: {e}")
            raise
    
    async def send_message_to_channel(
        self,
        access_token: str,
        team_id: str,
        channel_id: str,
        content: str,
        content_type: str = "text"
    ) -> TeamsMessage:
        """
        Send message to a specific channel
        
        Args:
            access_token: Azure AD access token
            team_id: Team ID
            channel_id: Channel ID
            content: Message content
            content_type: Content type (text, html, etc.)
            
        Returns:
            Sent message
        """
        try:
            url = f"{self.graph_endpoint}/teams/{team_id}/channels/{channel_id}/messages"
            
            # Prepare message data
            message_data = {
                "body": {
                    "contentType": content_type,
                    "content": content
                }
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=message_data)
                response.raise_for_status()
                
                sent_message = response.json()
                
                # Parse timestamps
                created_datetime = None
                if sent_message.get("createdDateTime"):
                    created_datetime = datetime.fromisoformat(
                        sent_message["createdDateTime"].replace('Z', '+00:00')
                    )
                
                last_modified_datetime = None
                if sent_message.get("lastModifiedDateTime"):
                    last_modified_datetime = datetime.fromisoformat(
                        sent_message["lastModifiedDateTime"].replace('Z', '+00:00')
                    )
                
                message = TeamsMessage(
                    id=sent_message.get("id"),
                    content=sent_message.get("body", {}).get("content", ""),
                    created_datetime=created_datetime,
                    last_modified_datetime=last_modified_datetime,
                    from_user=sent_message.get("from"),
                    attachments=sent_message.get("attachments", [])
                )
                
                logger.info(f"Sent message to channel {channel_id}: {message.content[:50]}...")
                return message
                
        except Exception as e:
            logger.error(f"Failed to send message to channel: {e}")
            raise
    
    async def send_message_with_attachment(
        self,
        access_token: str,
        team_id: str,
        channel_id: str,
        content: str,
        attachment_name: str,
        attachment_content: str,
        attachment_content_type: str = "text/plain"
    ) -> TeamsMessage:
        """
        Send message with attachment to a channel
        
        Args:
            access_token: Azure AD access token
            team_id: Team ID
            channel_id: Channel ID
            content: Message content
            attachment_name: Name of the attachment
            attachment_content: Content of the attachment
            attachment_content_type: MIME type of attachment
            
        Returns:
            Sent message with attachment
        """
        try:
            url = f"{self.graph_endpoint}/teams/{team_id}/channels/{channel_id}/messages"
            
            # Prepare message data with attachment
            message_data = {
                "body": {
                    "contentType": "text",
                    "content": content
                },
                "attachments": [
                    {
                        "id": "0",
                        "contentType": attachment_content_type,
                        "contentUrl": f"data:{attachment_content_type};base64,{attachment_content}",
                        "name": attachment_name
                    }
                ]
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=message_data)
                response.raise_for_status()
                
                sent_message = response.json()
                
                # Parse timestamps
                created_datetime = None
                if sent_message.get("createdDateTime"):
                    created_datetime = datetime.fromisoformat(
                        sent_message["createdDateTime"].replace('Z', '+00:00')
                    )
                
                message = TeamsMessage(
                    id=sent_message.get("id"),
                    content=sent_message.get("body", {}).get("content", ""),
                    created_datetime=created_datetime,
                    from_user=sent_message.get("from"),
                    attachments=sent_message.get("attachments", [])
                )
                
                logger.info(f"Sent message with attachment to channel {channel_id}")
                return message
                
        except Exception as e:
            logger.error(f"Failed to send message with attachment: {e}")
            raise
    
    async def get_channel_messages(
        self,
        access_token: str,
        team_id: str,
        channel_id: str,
        max_results: int = 50
    ) -> List[TeamsMessage]:
        """
        Get messages from a channel
        
        Args:
            access_token: Azure AD access token
            team_id: Team ID
            channel_id: Channel ID
            max_results: Maximum number of messages to return
            
        Returns:
            List of channel messages
        """
        try:
            url = f"{self.graph_endpoint}/teams/{team_id}/channels/{channel_id}/messages"
            params = {
                "$top": max_results,
                "$orderby": "createdDateTime desc"
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                messages = []
                
                for message_data in data.get("value", []):
                    # Parse timestamps
                    created_datetime = None
                    if message_data.get("createdDateTime"):
                        created_datetime = datetime.fromisoformat(
                            message_data["createdDateTime"].replace('Z', '+00:00')
                        )
                    
                    last_modified_datetime = None
                    if message_data.get("lastModifiedDateTime"):
                        last_modified_datetime = datetime.fromisoformat(
                            message_data["lastModifiedDateTime"].replace('Z', '+00:00')
                        )
                    
                    message = TeamsMessage(
                        id=message_data.get("id"),
                        content=message_data.get("body", {}).get("content", ""),
                        created_datetime=created_datetime,
                        last_modified_datetime=last_modified_datetime,
                        from_user=message_data.get("from"),
                        attachments=message_data.get("attachments", [])
                    )
                    messages.append(message)
                
                logger.info(f"Retrieved {len(messages)} messages from channel {channel_id}")
                return messages
                
        except Exception as e:
            logger.error(f"Failed to get channel messages: {e}")
            raise
    
    async def get_user_chats(self, access_token: str) -> List[dict]:
        """
        Get user's group chats
        
        Args:
            access_token: Azure AD access token
            
        Returns:
            List of user's group chats
        """
        try:
            url = f"{self.graph_endpoint}/me/chats"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                chats = data.get("value", [])
                
                logger.info(f"Retrieved {len(chats)} group chats for user")
                return chats
                
        except Exception as e:
            logger.error(f"Failed to get user chats: {e}")
            raise

    async def send_message_to_chat(
        self,
        access_token: str,
        chat_id: str,
        content: str,
        content_type: str = "text"
    ) -> TeamsMessage:
        """
        Send message to a group chat
        
        Args:
            access_token: Azure AD access token
            chat_id: Chat ID
            content: Message content
            content_type: Content type (text, html, etc.)
            
        Returns:
            Sent message
        """
        try:
            url = f"{self.graph_endpoint}/chats/{chat_id}/messages"
            
            # Prepare message data
            message_data = {
                "body": {
                    "contentType": content_type,
                    "content": content
                }
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=message_data)
                response.raise_for_status()
                
                sent_message = response.json()
                
                # Parse timestamps
                created_datetime = None
                if sent_message.get("createdDateTime"):
                    created_datetime = datetime.fromisoformat(
                        sent_message["createdDateTime"].replace('Z', '+00:00')
                    )
                
                last_modified_datetime = None
                if sent_message.get("lastModifiedDateTime"):
                    last_modified_datetime = datetime.fromisoformat(
                        sent_message["lastModifiedDateTime"].replace('Z', '+00:00')
                    )
                
                message = TeamsMessage(
                    id=sent_message.get("id"),
                    content=sent_message.get("body", {}).get("content", ""),
                    created_datetime=created_datetime,
                    last_modified_datetime=last_modified_datetime,
                    from_user=sent_message.get("from"),
                    attachments=sent_message.get("attachments", [])
                )
                
                logger.info(f"Sent message to chat {chat_id}: {message.content[:50]}...")
                return message
                
        except Exception as e:
            logger.error(f"Failed to send message to chat: {e}")
            raise

    async def get_chat_messages(
        self,
        access_token: str,
        chat_id: str,
        max_results: int = 50
    ) -> List[TeamsMessage]:
        """
        Get messages from a group chat
        
        Args:
            access_token: Azure AD access token
            chat_id: Chat ID
            max_results: Maximum number of messages to return
            
        Returns:
            List of chat messages
        """
        try:
            url = f"{self.graph_endpoint}/chats/{chat_id}/messages"
            params = {
                "$top": max_results,
                "$orderby": "createdDateTime desc"
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                messages = []
                
                for message_data in data.get("value", []):
                    # Parse timestamps
                    created_datetime = None
                    if message_data.get("createdDateTime"):
                        created_datetime = datetime.fromisoformat(
                            message_data["createdDateTime"].replace('Z', '+00:00')
                        )
                    
                    last_modified_datetime = None
                    if message_data.get("lastModifiedDateTime"):
                        last_modified_datetime = datetime.fromisoformat(
                            message_data["lastModifiedDateTime"].replace('Z', '+00:00')
                        )
                    
                    message = TeamsMessage(
                        id=message_data.get("id"),
                        content=message_data.get("body", {}).get("content", ""),
                        created_datetime=created_datetime,
                        last_modified_datetime=last_modified_datetime,
                        from_user=message_data.get("from"),
                        attachments=message_data.get("attachments", [])
                    )
                    messages.append(message)
                
                logger.info(f"Retrieved {len(messages)} messages from chat {chat_id}")
                return messages
                
        except Exception as e:
            logger.error(f"Failed to get chat messages: {e}")
            raise

    async def reply_to_message(
        self,
        access_token: str,
        team_id: str,
        channel_id: str,
        message_id: str,
        reply_content: str
    ) -> TeamsMessage:
        """
        Reply to a specific message in a channel
        
        Args:
            access_token: Azure AD access token
            team_id: Team ID
            channel_id: Channel ID
            message_id: ID of the message to reply to
            reply_content: Reply content
            
        Returns:
            Reply message
        """
        try:
            url = f"{self.graph_endpoint}/teams/{team_id}/channels/{channel_id}/messages/{message_id}/replies"
            
            message_data = {
                "body": {
                    "contentType": "text",
                    "content": reply_content
                }
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=message_data)
                response.raise_for_status()
                
                reply_message = response.json()
                
                # Parse timestamps
                created_datetime = None
                if reply_message.get("createdDateTime"):
                    created_datetime = datetime.fromisoformat(
                        reply_message["createdDateTime"].replace('Z', '+00:00')
                    )
                
                message = TeamsMessage(
                    id=reply_message.get("id"),
                    content=reply_message.get("body", {}).get("content", ""),
                    created_datetime=created_datetime,
                    from_user=reply_message.get("from"),
                    attachments=reply_message.get("attachments", [])
                )
                
                logger.info(f"Replied to message {message_id} in channel {channel_id}")
                return message
                
        except Exception as e:
            logger.error(f"Failed to reply to message: {e}")
            raise
