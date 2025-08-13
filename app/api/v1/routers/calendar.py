"""
Calendar API Router
Handles calendar-related endpoints
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.application.calendar.use_cases.calendar_use_cases import (
    GetCalendarsUseCase,
    GetCalendarEventsUseCase,
    CreateCalendarEventUseCase,
    UpdateCalendarEventUseCase,
    DeleteCalendarEventUseCase,
    GetCalendarsRequest,
    GetCalendarEventsRequest,
    CreateCalendarEventRequest
)
from app.adapters.calendar_adapter import CalendarAdapter
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/calendar", tags=["Calendar"])


class CalendarModel(BaseModel):
    """Calendar model for API responses"""
    id: str
    name: str
    color: Optional[str] = None
    is_default: bool = False
    can_edit: bool = True
    can_share: bool = True
    owner: Optional[dict] = None


class CalendarEventModel(BaseModel):
    """Calendar event model for API responses"""
    id: str
    subject: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    attendees: List[dict] = []
    is_all_day: bool = False
    organizer: Optional[dict] = None
    created_date: Optional[str] = None
    last_modified_date: Optional[str] = None


class CreateEventRequest(BaseModel):
    """Request model for creating calendar event"""
    subject: str
    start_time: datetime
    end_time: datetime
    calendar_id: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    attendees: Optional[List[str]] = None
    is_all_day: bool = False


class UpdateEventRequest(BaseModel):
    """Request model for updating calendar event"""
    subject: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_all_day: Optional[bool] = None


def get_calendar_adapter() -> CalendarAdapter:
    """Dependency to get calendar adapter"""
    return CalendarAdapter()

# Security scheme
security = HTTPBearer(description="Azure AD access token")


@router.get("/calendars", response_model=List[CalendarModel])
async def get_calendars(
    authorization: str = Header(..., alias="Authorization", description="Azure AD access token (format: Bearer <token>)"),
    calendar_adapter: CalendarAdapter = Depends(get_calendar_adapter)
):
    """
    Get user's calendars
    
    This endpoint retrieves all calendars accessible to the authenticated user.
    """
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        access_token = authorization.replace("Bearer ", "")
        
        # Create use case and execute
        use_case = GetCalendarsUseCase(calendar_adapter)
        request = GetCalendarsRequest(access_token=access_token)
        response = await use_case.execute(request)
        
        # Convert to API models
        calendars = [
            CalendarModel(
                id=cal.id,
                name=cal.name,
                color=cal.color,
                is_default=cal.is_default,
                can_edit=cal.can_edit,
                can_share=cal.can_share,
                owner=cal.owner
            )
            for cal in response.calendars
        ]
        
        return calendars
        
    except Exception as e:
        logger.error(f"Failed to get calendars: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events", response_model=List[CalendarEventModel])
async def get_calendar_events(
    calendar_id: Optional[str] = Query(None, description="Calendar ID (default calendar if not provided)"),
    start_date: Optional[datetime] = Query(None, description="Start date for events"),
    end_date: Optional[datetime] = Query(None, description="End date for events"),
    max_results: int = Query(50, description="Maximum number of events to return"),
    authorization: str = Header(..., alias="Authorization", description="Azure AD access token (format: Bearer <token>)"),
    calendar_adapter: CalendarAdapter = Depends(get_calendar_adapter)
):
    """
    Get calendar events
    
    This endpoint retrieves events from a specific calendar or the default calendar.
    """
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        access_token = authorization.replace("Bearer ", "")
        
        # Create use case and execute
        use_case = GetCalendarEventsUseCase(calendar_adapter)
        request = GetCalendarEventsRequest(
            access_token=access_token,
            calendar_id=calendar_id,
            start_date=start_date,
            end_date=end_date,
            max_results=max_results
        )
        response = await use_case.execute(request)
        
        # Convert to API models
        events = [
            CalendarEventModel(
                id=event.id,
                subject=event.subject,
                start_time=event.start_time.isoformat() if event.start_time else None,
                end_time=event.end_time.isoformat() if event.end_time else None,
                location=event.location,
                description=event.description,
                attendees=event.attendees or [],
                is_all_day=event.is_all_day,
                organizer=event.organizer,
                created_date=event.created_date.isoformat() if event.created_date else None,
                last_modified_date=event.last_modified_date.isoformat() if event.last_modified_date else None
            )
            for event in response.events
        ]
        
        return events
        
    except Exception as e:
        logger.error(f"Failed to get calendar events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events", response_model=CalendarEventModel)
async def create_calendar_event(
    request: CreateEventRequest,
    authorization: str = Header(..., alias="Authorization", description="Azure AD access token (format: Bearer <token>)"),
    calendar_adapter: CalendarAdapter = Depends(get_calendar_adapter)
):
    """
    Create a new calendar event
    
    This endpoint creates a new event in the specified calendar or default calendar.
    """
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        access_token = authorization.replace("Bearer ", "")
        
        # Create use case and execute
        use_case = CreateCalendarEventUseCase(calendar_adapter)
        create_request = CreateCalendarEventRequest(
            access_token=access_token,
            subject=request.subject,
            start_time=request.start_time,
            end_time=request.end_time,
            calendar_id=request.calendar_id,
            location=request.location,
            description=request.description,
            attendees=request.attendees,
            is_all_day=request.is_all_day
        )
        response = await use_case.execute(create_request)
        
        # Convert to API model
        event = CalendarEventModel(
            id=response.event.id,
            subject=response.event.subject,
            start_time=response.event.start_time.isoformat() if response.event.start_time else None,
            end_time=response.event.end_time.isoformat() if response.event.end_time else None,
            location=response.event.location,
            description=response.event.description,
            attendees=response.event.attendees or [],
            is_all_day=response.event.is_all_day,
            organizer=response.event.organizer,
            created_date=response.event.created_date.isoformat() if response.event.created_date else None,
            last_modified_date=response.event.last_modified_date.isoformat() if response.event.last_modified_date else None
        )
        
        return event
        
    except Exception as e:
        logger.error(f"Failed to create calendar event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/events/{event_id}", response_model=CalendarEventModel)
async def update_calendar_event(
    event_id: str,
    request: UpdateEventRequest,
    calendar_id: Optional[str] = Query(None, description="Calendar ID (default calendar if not provided)"),
    authorization: str = Header(..., alias="Authorization", description="Azure AD access token (format: Bearer <token>)"),
    calendar_adapter: CalendarAdapter = Depends(get_calendar_adapter)
):
    """
    Update an existing calendar event
    
    This endpoint updates an existing event in the specified calendar.
    """
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        access_token = authorization.replace("Bearer ", "")
        
        # Prepare updates
        updates = {}
        if request.subject is not None:
            updates["subject"] = request.subject
        if request.start_time is not None:
            updates["start_time"] = request.start_time
        if request.end_time is not None:
            updates["end_time"] = request.end_time
        if request.location is not None:
            updates["location"] = request.location
        if request.description is not None:
            updates["description"] = request.description
        if request.is_all_day is not None:
            updates["is_all_day"] = request.is_all_day
        
        # Create use case and execute
        use_case = UpdateCalendarEventUseCase(calendar_adapter)
        updated_event = await use_case.execute(
            access_token=access_token,
            event_id=event_id,
            calendar_id=calendar_id,
            **updates
        )
        
        # Convert to API model
        event = CalendarEventModel(
            id=updated_event.id,
            subject=updated_event.subject,
            start_time=updated_event.start_time.isoformat() if updated_event.start_time else None,
            end_time=updated_event.end_time.isoformat() if updated_event.end_time else None,
            location=updated_event.location,
            description=updated_event.description,
            attendees=updated_event.attendees or [],
            is_all_day=updated_event.is_all_day,
            organizer=updated_event.organizer,
            created_date=updated_event.created_date.isoformat() if updated_event.created_date else None,
            last_modified_date=updated_event.last_modified_date.isoformat() if updated_event.last_modified_date else None
        )
        
        return event
        
    except Exception as e:
        logger.error(f"Failed to update calendar event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/events/{event_id}")
async def delete_calendar_event(
    event_id: str,
    calendar_id: Optional[str] = Query(None, description="Calendar ID (default calendar if not provided)"),
    authorization: str = Header(..., alias="Authorization", description="Azure AD access token (format: Bearer <token>)"),
    calendar_adapter: CalendarAdapter = Depends(get_calendar_adapter)
):
    """
    Delete a calendar event
    
    This endpoint deletes an existing event from the specified calendar.
    """
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        access_token = authorization.replace("Bearer ", "")
        
        # Create use case and execute
        use_case = DeleteCalendarEventUseCase(calendar_adapter)
        result = await use_case.execute(
            access_token=access_token,
            event_id=event_id,
            calendar_id=calendar_id
        )
        
        if result:
            return {"message": "Event deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Event not found")
        
    except Exception as e:
        logger.error(f"Failed to delete calendar event: {e}")
        raise HTTPException(status_code=500, detail=str(e))
