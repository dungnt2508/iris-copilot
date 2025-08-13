"""
Teams API Router
Handles Teams-related endpoints
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.application.teams.use_cases.teams_use_cases import (
    GetTeamsUseCase,
    GetChannelsUseCase,
    SendMessageUseCase,
    GetMessagesUseCase,
    ReplyToMessageUseCase,
    GetChatsUseCase,
    SendChatMessageUseCase,
    GetChatMessagesUseCase,
    GetTeamsRequest,
    GetChannelsRequest,
    SendMessageRequest,
    GetMessagesRequest,
    GetChatsRequest,
    SendChatMessageRequest,
    GetChatMessagesRequest
)
from app.adapters.teams_adapter import TeamsAdapter
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/teams", tags=["Teams"])


class TeamModel(BaseModel):
    """Team model for API responses"""
    id: str
    display_name: str
    description: Optional[str] = None
    visibility: Optional[str] = None
    created_datetime: Optional[str] = None


class ChannelModel(BaseModel):
    """Channel model for API responses"""
    id: str
    display_name: str
    description: Optional[str] = None
    is_default: bool = False
    membership_type: Optional[str] = None


class MessageModel(BaseModel):
    """Message model for API responses"""
    id: str
    content: str
    created_datetime: Optional[str] = None
    last_modified_datetime: Optional[str] = None
    from_user: Optional[dict] = None
    attachments: List[dict] = []


class SendMessageRequest(BaseModel):
    """Request model for sending message"""
    team_id: str
    channel_id: str
    content: str
    content_type: str = "text"


class ReplyMessageRequest(BaseModel):
    """Request model for replying to message"""
    reply_content: str


def get_teams_adapter() -> TeamsAdapter:
    """Dependency to get teams adapter"""
    return TeamsAdapter()

# Security scheme
security = HTTPBearer(description="Azure AD access token")


@router.get("/teams", response_model=List[TeamModel])
async def get_teams(
    credentials: HTTPAuthorizationCredentials = Security(security),
    teams_adapter: TeamsAdapter = Depends(get_teams_adapter)
):
    """
    Get user's teams
    
    This endpoint retrieves all teams that the authenticated user is a member of.
    """
    try:
        # Extract token from credentials
        access_token = credentials.credentials
        
        # Create use case and execute
        use_case = GetTeamsUseCase(teams_adapter)
        request = GetTeamsRequest(access_token=access_token)
        response = await use_case.execute(request)
        
        # Convert to API models
        teams = [
            TeamModel(
                id=team.id,
                display_name=team.display_name,
                description=team.description,
                visibility=team.visibility,
                created_datetime=team.created_datetime.isoformat() if team.created_datetime else None
            )
            for team in response.teams
        ]
        
        return teams
        
    except Exception as e:
        logger.error(f"Failed to get teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}/channels", response_model=List[ChannelModel])
async def get_team_channels(
    team_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security),
    teams_adapter: TeamsAdapter = Depends(get_teams_adapter)
):
    """
    Get channels for a specific team
    
    This endpoint retrieves all channels in the specified team.
    """
    try:
        # Extract token from credentials
        access_token = credentials.credentials
        
        # Create use case and execute
        use_case = GetChannelsUseCase(teams_adapter)
        request = GetChannelsRequest(access_token=access_token, team_id=team_id)
        response = await use_case.execute(request)
        
        # Convert to API models
        channels = [
            ChannelModel(
                id=channel.id,
                display_name=channel.display_name,
                description=channel.description,
                is_default=channel.is_default,
                membership_type=channel.membership_type
            )
            for channel in response.channels
        ]
        
        return channels
        
    except Exception as e:
        logger.error(f"Failed to get team channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams/{team_id}/channels/{channel_id}/messages", response_model=MessageModel)
async def send_message(
    team_id: str,
    channel_id: str,
    request: SendMessageRequest,
    credentials: HTTPAuthorizationCredentials = Security(security),
    teams_adapter: TeamsAdapter = Depends(get_teams_adapter)
):
    """
    Send message to a specific channel
    
    This endpoint sends a message to the specified channel in a team.
    """
    try:
        # Extract token from credentials
        access_token = credentials.credentials
        
        # Create use case and execute
        use_case = SendMessageUseCase(teams_adapter)
        send_request = SendMessageRequest(
            access_token=access_token,
            team_id=team_id,
            channel_id=channel_id,
            content=request.content,
            content_type=request.content_type
        )
        response = await use_case.execute(send_request)
        
        # Convert to API model
        message = MessageModel(
            id=response.message.id,
            content=response.message.content,
            created_datetime=response.message.created_datetime.isoformat() if response.message.created_datetime else None,
            last_modified_datetime=response.message.last_modified_datetime.isoformat() if response.message.last_modified_datetime else None,
            from_user=response.message.from_user,
            attachments=response.message.attachments or []
        )
        
        return message
        
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}/channels/{channel_id}/messages", response_model=List[MessageModel])
async def get_channel_messages(
    team_id: str,
    channel_id: str,
    max_results: int = Query(50, description="Maximum number of messages to return"),
    credentials: HTTPAuthorizationCredentials = Security(security),
    teams_adapter: TeamsAdapter = Depends(get_teams_adapter)
):
    """
    Get messages from a specific channel
    
    This endpoint retrieves messages from the specified channel in a team.
    """
    try:
        # Extract token from credentials
        access_token = credentials.credentials
        
        # Create use case and execute
        use_case = GetMessagesUseCase(teams_adapter)
        request = GetMessagesRequest(
            access_token=access_token,
            team_id=team_id,
            channel_id=channel_id,
            max_results=max_results
        )
        response = await use_case.execute(request)
        
        # Convert to API models
        messages = [
            MessageModel(
                id=message.id,
                content=message.content,
                created_datetime=message.created_datetime.isoformat() if message.created_datetime else None,
                last_modified_datetime=message.last_modified_datetime.isoformat() if message.last_modified_datetime else None,
                from_user=message.from_user,
                attachments=message.attachments or []
            )
            for message in response.messages
        ]
        
        return messages
        
    except Exception as e:
        logger.error(f"Failed to get channel messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams/{team_id}/channels/{channel_id}/messages/{message_id}/replies", response_model=MessageModel)
async def reply_to_message(
    team_id: str,
    channel_id: str,
    message_id: str,
    request: ReplyMessageRequest,
    credentials: HTTPAuthorizationCredentials = Security(security),
    teams_adapter: TeamsAdapter = Depends(get_teams_adapter)
):
    """
    Reply to a specific message in a channel
    
    This endpoint sends a reply to the specified message in a channel.
    """
    try:
        # Extract token from credentials
        access_token = credentials.credentials
        
        # Create use case and execute
        use_case = ReplyToMessageUseCase(teams_adapter)
        reply_message = await use_case.execute(
            access_token=access_token,
            team_id=team_id,
            channel_id=channel_id,
            message_id=message_id,
            reply_content=request.reply_content
        )
        
        # Convert to API model
        message = MessageModel(
            id=reply_message.id,
            content=reply_message.content,
            created_datetime=reply_message.created_datetime.isoformat() if reply_message.created_datetime else None,
            last_modified_datetime=reply_message.last_modified_datetime.isoformat() if reply_message.last_modified_datetime else None,
            from_user=reply_message.from_user,
            attachments=reply_message.attachments or []
        )
        
        return message
        
    except Exception as e:
        logger.error(f"Failed to reply to message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Group Chat Endpoints
@router.get("/chats", response_model=List[dict])
async def get_user_chats(
    credentials: HTTPAuthorizationCredentials = Security(security),
    teams_adapter: TeamsAdapter = Depends(get_teams_adapter)
):
    """
    Get user's group chats
    
    This endpoint retrieves all group chats that the authenticated user is a member of.
    """
    try:
        # Extract token from credentials
        access_token = credentials.credentials
        
        # Create use case and execute
        use_case = GetChatsUseCase(teams_adapter)
        request = GetChatsRequest(access_token=access_token)
        response = await use_case.execute(request)
        
        return response.chats
        
    except Exception as e:
        logger.error(f"Failed to get chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chats/{chat_id}/messages", response_model=MessageModel)
async def send_chat_message(
    chat_id: str,
    request: SendMessageRequest,
    credentials: HTTPAuthorizationCredentials = Security(security),
    teams_adapter: TeamsAdapter = Depends(get_teams_adapter)
):
    """
    Send message to a group chat
    
    This endpoint sends a message to the specified group chat.
    """
    try:
        # Extract token from credentials
        access_token = credentials.credentials
        
        # Create use case and execute
        use_case = SendChatMessageUseCase(teams_adapter)
        send_request = SendChatMessageRequest(
            access_token=access_token,
            chat_id=chat_id,
            content=request.content,
            content_type=request.content_type
        )
        response = await use_case.execute(send_request)
        
        # Convert to API model
        message = MessageModel(
            id=response.message.id,
            content=response.message.content,
            created_datetime=response.message.created_datetime.isoformat() if response.message.created_datetime else None,
            last_modified_datetime=response.message.last_modified_datetime.isoformat() if response.message.last_modified_datetime else None,
            from_user=response.message.from_user,
            attachments=response.message.attachments or []
        )
        
        return message
        
    except Exception as e:
        logger.error(f"Failed to send chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chats/{chat_id}/messages", response_model=List[MessageModel])
async def get_chat_messages(
    chat_id: str,
    max_results: int = Query(50, description="Maximum number of messages to return"),
    credentials: HTTPAuthorizationCredentials = Security(security),
    teams_adapter: TeamsAdapter = Depends(get_teams_adapter)
):
    """
    Get messages from a group chat
    
    This endpoint retrieves messages from the specified group chat.
    """
    try:
        # Extract token from credentials
        access_token = credentials.credentials
        
        # Create use case and execute
        use_case = GetChatMessagesUseCase(teams_adapter)
        request = GetChatMessagesRequest(
            access_token=access_token,
            chat_id=chat_id,
            max_results=max_results
        )
        response = await use_case.execute(request)
        
        # Convert to API models
        messages = [
            MessageModel(
                id=message.id,
                content=message.content,
                created_datetime=message.created_datetime.isoformat() if message.created_datetime else None,
                last_modified_datetime=message.last_modified_datetime.isoformat() if message.last_modified_datetime else None,
                from_user=message.from_user,
                attachments=message.attachments or []
            )
            for message in response.messages
        ]
        
        return messages
        
    except Exception as e:
        logger.error(f"Failed to get chat messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))
