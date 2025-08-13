"""
Calendar Use Cases
Handles calendar business logic
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ....adapters.calendar_adapter import CalendarAdapter, Calendar, CalendarEvent
from ....core.logger import get_logger

logger = get_logger(__name__)


class GetCalendarsRequest:
    """Request model for getting calendars"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token


class GetCalendarsResponse:
    """Response model for getting calendars"""
    
    def __init__(self, calendars: List[Calendar]):
        self.calendars = calendars


class GetCalendarEventsRequest:
    """Request model for getting calendar events"""
    
    def __init__(
        self,
        access_token: str,
        calendar_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_results: int = 50
    ):
        self.access_token = access_token
        self.calendar_id = calendar_id
        self.start_date = start_date
        self.end_date = end_date
        self.max_results = max_results


class GetCalendarEventsResponse:
    """Response model for getting calendar events"""
    
    def __init__(self, events: List[CalendarEvent]):
        self.events = events


class CreateCalendarEventRequest:
    """Request model for creating calendar event"""
    
    def __init__(
        self,
        access_token: str,
        subject: str,
        start_time: datetime,
        end_time: datetime,
        calendar_id: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        is_all_day: bool = False
    ):
        self.access_token = access_token
        self.subject = subject
        self.start_time = start_time
        self.end_time = end_time
        self.calendar_id = calendar_id
        self.location = location
        self.description = description
        self.attendees = attendees
        self.is_all_day = is_all_day


class CreateCalendarEventResponse:
    """Response model for creating calendar event"""
    
    def __init__(self, event: CalendarEvent):
        self.event = event


class GetCalendarsUseCase:
    """Use case for getting user calendars"""
    
    def __init__(self, calendar_adapter: CalendarAdapter):
        self.calendar_adapter = calendar_adapter
    
    async def execute(self, request: GetCalendarsRequest) -> GetCalendarsResponse:
        """
        Get user's calendars
        
        Args:
            request: Request with access token
            
        Returns:
            Response with list of calendars
        """
        try:
            logger.info("Getting user calendars")
            calendars = await self.calendar_adapter.get_user_calendars(request.access_token)
            
            logger.info(f"Retrieved {len(calendars)} calendars")
            return GetCalendarsResponse(calendars=calendars)
            
        except Exception as e:
            logger.error(f"Failed to get calendars: {e}")
            raise


class GetCalendarEventsUseCase:
    """Use case for getting calendar events"""
    
    def __init__(self, calendar_adapter: CalendarAdapter):
        self.calendar_adapter = calendar_adapter
    
    async def execute(self, request: GetCalendarEventsRequest) -> GetCalendarEventsResponse:
        """
        Get calendar events
        
        Args:
            request: Request with access token and filters
            
        Returns:
            Response with list of events
        """
        try:
            logger.info(f"Getting calendar events for calendar: {request.calendar_id}")
            events = await self.calendar_adapter.get_calendar_events(
                access_token=request.access_token,
                calendar_id=request.calendar_id,
                start_date=request.start_date,
                end_date=request.end_date,
                max_results=request.max_results
            )
            
            logger.info(f"Retrieved {len(events)} events")
            return GetCalendarEventsResponse(events=events)
            
        except Exception as e:
            logger.error(f"Failed to get calendar events: {e}")
            raise


class CreateCalendarEventUseCase:
    """Use case for creating calendar event"""
    
    def __init__(self, calendar_adapter: CalendarAdapter):
        self.calendar_adapter = calendar_adapter
    
    async def execute(self, request: CreateCalendarEventRequest) -> CreateCalendarEventResponse:
        """
        Create calendar event
        
        Args:
            request: Request with event details
            
        Returns:
            Response with created event
        """
        try:
            logger.info(f"Creating calendar event: {request.subject}")
            event = await self.calendar_adapter.create_calendar_event(
                access_token=request.access_token,
                subject=request.subject,
                start_time=request.start_time,
                end_time=request.end_time,
                calendar_id=request.calendar_id,
                location=request.location,
                description=request.description,
                attendees=request.attendees,
                is_all_day=request.is_all_day
            )
            
            logger.info(f"Created calendar event: {event.subject}")
            return CreateCalendarEventResponse(event=event)
            
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            raise


class UpdateCalendarEventUseCase:
    """Use case for updating calendar event"""
    
    def __init__(self, calendar_adapter: CalendarAdapter):
        self.calendar_adapter = calendar_adapter
    
    async def execute(
        self,
        access_token: str,
        event_id: str,
        calendar_id: Optional[str] = None,
        **updates
    ) -> CalendarEvent:
        """
        Update calendar event
        
        Args:
            access_token: Azure AD access token
            event_id: Event ID to update
            calendar_id: Calendar ID (None for default)
            **updates: Fields to update
            
        Returns:
            Updated event
        """
        try:
            logger.info(f"Updating calendar event: {event_id}")
            event = await self.calendar_adapter.update_calendar_event(
                access_token=access_token,
                event_id=event_id,
                calendar_id=calendar_id,
                **updates
            )
            
            logger.info(f"Updated calendar event: {event.subject}")
            return event
            
        except Exception as e:
            logger.error(f"Failed to update calendar event: {e}")
            raise


class DeleteCalendarEventUseCase:
    """Use case for deleting calendar event"""
    
    def __init__(self, calendar_adapter: CalendarAdapter):
        self.calendar_adapter = calendar_adapter
    
    async def execute(
        self,
        access_token: str,
        event_id: str,
        calendar_id: Optional[str] = None
    ) -> bool:
        """
        Delete calendar event
        
        Args:
            access_token: Azure AD access token
            event_id: Event ID to delete
            calendar_id: Calendar ID (None for default)
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Deleting calendar event: {event_id}")
            result = await self.calendar_adapter.delete_calendar_event(
                access_token=access_token,
                event_id=event_id,
                calendar_id=calendar_id
            )
            
            logger.info(f"Deleted calendar event: {event_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete calendar event: {e}")
            raise
