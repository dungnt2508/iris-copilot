"""
Teams Use Cases
Handles Teams business logic
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ....adapters.teams_adapter import TeamsAdapter, TeamsTeam, TeamsChannel, TeamsMessage
from ....core.logger import get_logger

logger = get_logger(__name__)


class GetTeamsRequest:
    """Request model for getting teams"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token


class GetTeamsResponse:
    """Response model for getting teams"""
    
    def __init__(self, teams: List[TeamsTeam]):
        self.teams = teams


class GetChannelsRequest:
    """Request model for getting channels"""
    
    def __init__(self, access_token: str, team_id: str):
        self.access_token = access_token
        self.team_id = team_id


class GetChannelsResponse:
    """Response model for getting channels"""
    
    def __init__(self, channels: List[TeamsChannel]):
        self.channels = channels


class SendMessageRequest:
    """Request model for sending message"""
    
    def __init__(
        self,
        access_token: str,
        team_id: str,
        channel_id: str,
        content: str,
        content_type: str = "text"
    ):
        self.access_token = access_token
        self.team_id = team_id
        self.channel_id = channel_id
        self.content = content
        self.content_type = content_type


class SendMessageResponse:
    """Response model for sending message"""
    
    def __init__(self, message: TeamsMessage):
        self.message = message


class GetMessagesRequest:
    """Request model for getting messages"""
    
    def __init__(
        self,
        access_token: str,
        team_id: str,
        channel_id: str,
        max_results: int = 50
    ):
        self.access_token = access_token
        self.team_id = team_id
        self.channel_id = channel_id
        self.max_results = max_results


class GetMessagesResponse:
    """Response model for getting messages"""
    
    def __init__(self, messages: List[TeamsMessage]):
        self.messages = messages


class GetTeamsUseCase:
    """Use case for getting user teams"""
    
    def __init__(self, teams_adapter: TeamsAdapter):
        self.teams_adapter = teams_adapter
    
    async def execute(self, request: GetTeamsRequest) -> GetTeamsResponse:
        """
        Get user's teams
        
        Args:
            request: Request with access token
            
        Returns:
            Response with list of teams
        """
        try:
            logger.info("Getting user teams")
            teams = await self.teams_adapter.get_user_teams(request.access_token)
            
            logger.info(f"Retrieved {len(teams)} teams")
            return GetTeamsResponse(teams=teams)
            
        except Exception as e:
            logger.error(f"Failed to get teams: {e}")
            raise


class GetChannelsUseCase:
    """Use case for getting team channels"""
    
    def __init__(self, teams_adapter: TeamsAdapter):
        self.teams_adapter = teams_adapter
    
    async def execute(self, request: GetChannelsRequest) -> GetChannelsResponse:
        """
        Get channels for a team
        
        Args:
            request: Request with access token and team ID
            
        Returns:
            Response with list of channels
        """
        try:
            logger.info(f"Getting channels for team: {request.team_id}")
            channels = await self.teams_adapter.get_team_channels(
                request.access_token, 
                request.team_id
            )
            
            logger.info(f"Retrieved {len(channels)} channels")
            return GetChannelsResponse(channels=channels)
            
        except Exception as e:
            logger.error(f"Failed to get channels: {e}")
            raise


class SendMessageUseCase:
    """Use case for sending message to channel"""
    
    def __init__(self, teams_adapter: TeamsAdapter):
        self.teams_adapter = teams_adapter
    
    async def execute(self, request: SendMessageRequest) -> SendMessageResponse:
        """
        Send message to channel
        
        Args:
            request: Request with message details
            
        Returns:
            Response with sent message
        """
        try:
            logger.info(f"Sending message to channel: {request.channel_id}")
            message = await self.teams_adapter.send_message_to_channel(
                access_token=request.access_token,
                team_id=request.team_id,
                channel_id=request.channel_id,
                content=request.content,
                content_type=request.content_type
            )
            
            logger.info(f"Sent message: {message.content[:50]}...")
            return SendMessageResponse(message=message)
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise


class GetMessagesUseCase:
    """Use case for getting channel messages"""
    
    def __init__(self, teams_adapter: TeamsAdapter):
        self.teams_adapter = teams_adapter
    
    async def execute(self, request: GetMessagesRequest) -> GetMessagesResponse:
        """
        Get messages from channel
        
        Args:
            request: Request with channel details
            
        Returns:
            Response with list of messages
        """
        try:
            logger.info(f"Getting messages from channel: {request.channel_id}")
            messages = await self.teams_adapter.get_channel_messages(
                access_token=request.access_token,
                team_id=request.team_id,
                channel_id=request.channel_id,
                max_results=request.max_results
            )
            
            logger.info(f"Retrieved {len(messages)} messages")
            return GetMessagesResponse(messages=messages)
            
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            raise


class ReplyToMessageUseCase:
    """Use case for replying to a message"""
    
    def __init__(self, teams_adapter: TeamsAdapter):
        self.teams_adapter = teams_adapter
    
    async def execute(
        self,
        access_token: str,
        team_id: str,
        channel_id: str,
        message_id: str,
        reply_content: str
    ) -> TeamsMessage:
        """
        Reply to a message
        
        Args:
            access_token: Azure AD access token
            team_id: Team ID
            channel_id: Channel ID
            message_id: Message ID to reply to
            reply_content: Reply content
            
        Returns:
            Reply message
        """
        try:
            logger.info(f"Replying to message: {message_id}")
            message = await self.teams_adapter.reply_to_message(
                access_token=access_token,
                team_id=team_id,
                channel_id=channel_id,
                message_id=message_id,
                reply_content=reply_content
            )
            
            logger.info(f"Replied to message: {message.content[:50]}...")
            return message
            
        except Exception as e:
            logger.error(f"Failed to reply to message: {e}")
            raise


# Group Chat Use Cases
class GetChatsRequest(BaseModel):
    """Request model for getting user chats"""
    access_token: str


class GetChatsResponse(BaseModel):
    """Response model for getting user chats"""
    chats: List[dict]


class GetChatsUseCase:
    """Use case for getting user's group chats"""
    
    def __init__(self, teams_adapter: TeamsAdapter):
        self.teams_adapter = teams_adapter
    
    async def execute(self, request: GetChatsRequest) -> GetChatsResponse:
        """Execute the use case"""
        try:
            logger.info("Getting user's group chats")
            chats = await self.teams_adapter.get_user_chats(request.access_token)
            
            logger.info(f"Retrieved {len(chats)} group chats")
            return GetChatsResponse(chats=chats)
            
        except Exception as e:
            logger.error(f"Failed to get chats: {e}")
            raise


class SendChatMessageRequest(BaseModel):
    """Request model for sending message to chat"""
    access_token: str
    chat_id: str
    content: str
    content_type: str = "text"


class SendChatMessageResponse(BaseModel):
    """Response model for sending message to chat"""
    message: TeamsMessage


class SendChatMessageUseCase:
    """Use case for sending message to a group chat"""
    
    def __init__(self, teams_adapter: TeamsAdapter):
        self.teams_adapter = teams_adapter
    
    async def execute(self, request: SendChatMessageRequest) -> SendChatMessageResponse:
        """Execute the use case"""
        try:
            logger.info(f"Sending message to chat: {request.chat_id}")
            message = await self.teams_adapter.send_message_to_chat(
                access_token=request.access_token,
                chat_id=request.chat_id,
                content=request.content,
                content_type=request.content_type
            )
            
            logger.info(f"Sent message to chat: {message.content[:50]}...")
            return SendChatMessageResponse(message=message)
            
        except Exception as e:
            logger.error(f"Failed to send message to chat: {e}")
            raise


class GetChatMessagesRequest(BaseModel):
    """Request model for getting chat messages"""
    access_token: str
    chat_id: str
    max_results: int = 50


class GetChatMessagesResponse(BaseModel):
    """Response model for getting chat messages"""
    messages: List[TeamsMessage]


class GetChatMessagesUseCase:
    """Use case for getting messages from a group chat"""
    
    def __init__(self, teams_adapter: TeamsAdapter):
        self.teams_adapter = teams_adapter
    
    async def execute(self, request: GetChatMessagesRequest) -> GetChatMessagesResponse:
        """Execute the use case"""
        try:
            logger.info(f"Getting messages from chat: {request.chat_id}")
            messages = await self.teams_adapter.get_chat_messages(
                access_token=request.access_token,
                chat_id=request.chat_id,
                max_results=request.max_results
            )
            
            logger.info(f"Retrieved {len(messages)} messages from chat")
            return GetChatMessagesResponse(messages=messages)
            
        except Exception as e:
            logger.error(f"Failed to get chat messages: {e}")
            raise
