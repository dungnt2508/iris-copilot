"""
Calendar Adapter
Handles Microsoft Graph Calendar API operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from dataclasses import dataclass

from ..core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CalendarEvent:
    """Calendar event data model"""
    id: str
    subject: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    attendees: List[Dict[str, Any]] = None
    is_all_day: bool = False
    organizer: Optional[Dict[str, Any]] = None
    created_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "subject": self.subject,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "location": self.location,
            "description": self.description,
            "attendees": self.attendees or [],
            "is_all_day": self.is_all_day,
            "organizer": self.organizer,
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "last_modified_date": self.last_modified_date.isoformat() if self.last_modified_date else None
        }


@dataclass
class Calendar:
    """Calendar data model"""
    id: str
    name: str
    color: Optional[str] = None
    is_default: bool = False
    can_edit: bool = True
    can_share: bool = True
    owner: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "is_default": self.is_default,
            "can_edit": self.can_edit,
            "can_share": self.can_share,
            "owner": self.owner
        }


class CalendarAdapter:
    """
    Adapter for Microsoft Graph Calendar API
    Handles calendar operations like listing calendars and events
    """
    
    def __init__(self, graph_endpoint: str = "https://graph.microsoft.com/v1.0"):
        self.graph_endpoint = graph_endpoint
    
    async def get_user_calendars(self, access_token: str) -> List[Calendar]:
        """
        Get user's calendars
        
        Args:
            access_token: Azure AD access token
            
        Returns:
            List of user calendars
        """
        try:
            url = f"{self.graph_endpoint}/me/calendars"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                calendars = []
                
                for cal_data in data.get("value", []):
                    calendar = Calendar(
                        id=cal_data.get("id"),
                        name=cal_data.get("name"),
                        color=cal_data.get("color"),
                        is_default=cal_data.get("isDefaultCalendar", False),
                        can_edit=cal_data.get("canEdit", True),
                        can_share=cal_data.get("canShare", True),
                        owner=cal_data.get("owner")
                    )
                    calendars.append(calendar)
                
                logger.info(f"Retrieved {len(calendars)} calendars for user")
                return calendars
                
        except Exception as e:
            logger.error(f"Failed to get user calendars: {e}")
            raise
    
    async def get_calendar_events(
        self, 
        access_token: str, 
        calendar_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_results: int = 50
    ) -> List[CalendarEvent]:
        """
        Get calendar events
        
        Args:
            access_token: Azure AD access token
            calendar_id: Calendar ID (None for default calendar)
            start_date: Start date for events
            end_date: End date for events
            max_results: Maximum number of events to return
            
        Returns:
            List of calendar events
        """
        try:
            # Use default calendar if no calendar_id provided
            if calendar_id:
                url = f"{self.graph_endpoint}/me/calendars/{calendar_id}/events"
            else:
                url = f"{self.graph_endpoint}/me/events"
            
            # Set default date range if not provided
            if not start_date:
                start_date = datetime.utcnow()
            if not end_date:
                end_date = start_date + timedelta(days=30)
            
            # Build query parameters
            params = {
                "$top": max_results,
                "$orderby": "start/dateTime",
                "$filter": f"start/dateTime ge '{start_date.isoformat()}' and end/dateTime le '{end_date.isoformat()}'"
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                events = []
                
                for event_data in data.get("value", []):
                    # Parse start time
                    start_time = None
                    if event_data.get("start"):
                        start_str = event_data["start"].get("dateTime")
                        if start_str:
                            start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    
                    # Parse end time
                    end_time = None
                    if event_data.get("end"):
                        end_str = event_data["end"].get("dateTime")
                        if end_str:
                            end_time = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                    
                    # Parse created date
                    created_date = None
                    if event_data.get("createdDateTime"):
                        created_date = datetime.fromisoformat(
                            event_data["createdDateTime"].replace('Z', '+00:00')
                        )
                    
                    # Parse last modified date
                    last_modified_date = None
                    if event_data.get("lastModifiedDateTime"):
                        last_modified_date = datetime.fromisoformat(
                            event_data["lastModifiedDateTime"].replace('Z', '+00:00')
                        )
                    
                    event = CalendarEvent(
                        id=event_data.get("id"),
                        subject=event_data.get("subject", "No Subject"),
                        start_time=start_time,
                        end_time=end_time,
                        location=event_data.get("location", {}).get("displayName"),
                        description=event_data.get("bodyPreview"),
                        attendees=event_data.get("attendees", []),
                        is_all_day=event_data.get("isAllDay", False),
                        organizer=event_data.get("organizer"),
                        created_date=created_date,
                        last_modified_date=last_modified_date
                    )
                    events.append(event)
                
                logger.info(f"Retrieved {len(events)} events from calendar")
                return events
                
        except Exception as e:
            logger.error(f"Failed to get calendar events: {e}")
            raise
    
    async def create_calendar_event(
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
    ) -> CalendarEvent:
        """
        Create a new calendar event
        
        Args:
            access_token: Azure AD access token
            subject: Event subject
            start_time: Event start time
            end_time: Event end time
            calendar_id: Calendar ID (None for default calendar)
            location: Event location
            description: Event description
            attendees: List of attendee email addresses
            is_all_day: Whether event is all day
            
        Returns:
            Created calendar event
        """
        try:
            # Use default calendar if no calendar_id provided
            if calendar_id:
                url = f"{self.graph_endpoint}/me/calendars/{calendar_id}/events"
            else:
                url = f"{self.graph_endpoint}/me/events"
            
            # Prepare event data
            event_data = {
                "subject": subject,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "UTC"
                },
                "isAllDay": is_all_day
            }
            
            if location:
                event_data["location"] = {
                    "displayName": location
                }
            
            if description:
                event_data["body"] = {
                    "contentType": "text",
                    "content": description
                }
            
            if attendees:
                event_data["attendees"] = [
                    {"emailAddress": {"address": email}} for email in attendees
                ]
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=event_data)
                response.raise_for_status()
                
                created_event = response.json()
                
                # Parse the created event
                start_time = datetime.fromisoformat(
                    created_event["start"]["dateTime"].replace('Z', '+00:00')
                )
                end_time = datetime.fromisoformat(
                    created_event["end"]["dateTime"].replace('Z', '+00:00')
                )
                
                event = CalendarEvent(
                    id=created_event.get("id"),
                    subject=created_event.get("subject", "No Subject"),
                    start_time=start_time,
                    end_time=end_time,
                    location=created_event.get("location", {}).get("displayName"),
                    description=created_event.get("bodyPreview"),
                    attendees=created_event.get("attendees", []),
                    is_all_day=created_event.get("isAllDay", False),
                    organizer=created_event.get("organizer")
                )
                
                logger.info(f"Created calendar event: {event.subject}")
                return event
                
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            raise
    
    async def update_calendar_event(
        self,
        access_token: str,
        event_id: str,
        calendar_id: Optional[str] = None,
        **updates
    ) -> CalendarEvent:
        """
        Update an existing calendar event
        
        Args:
            access_token: Azure AD access token
            event_id: Event ID to update
            calendar_id: Calendar ID (None for default calendar)
            **updates: Fields to update (subject, start_time, end_time, etc.)
            
        Returns:
            Updated calendar event
        """
        try:
            # Use default calendar if no calendar_id provided
            if calendar_id:
                url = f"{self.graph_endpoint}/me/calendars/{calendar_id}/events/{event_id}"
            else:
                url = f"{self.graph_endpoint}/me/events/{event_id}"
            
            # Prepare update data
            update_data = {}
            
            if "subject" in updates:
                update_data["subject"] = updates["subject"]
            
            if "start_time" in updates:
                update_data["start"] = {
                    "dateTime": updates["start_time"].isoformat(),
                    "timeZone": "UTC"
                }
            
            if "end_time" in updates:
                update_data["end"] = {
                    "dateTime": updates["end_time"].isoformat(),
                    "timeZone": "UTC"
                }
            
            if "location" in updates:
                update_data["location"] = {
                    "displayName": updates["location"]
                }
            
            if "description" in updates:
                update_data["body"] = {
                    "contentType": "text",
                    "content": updates["description"]
                }
            
            if "is_all_day" in updates:
                update_data["isAllDay"] = updates["is_all_day"]
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, headers=headers, json=update_data)
                response.raise_for_status()
                
                updated_event = response.json()
                
                # Parse the updated event
                start_time = datetime.fromisoformat(
                    updated_event["start"]["dateTime"].replace('Z', '+00:00')
                )
                end_time = datetime.fromisoformat(
                    updated_event["end"]["dateTime"].replace('Z', '+00:00')
                )
                
                event = CalendarEvent(
                    id=updated_event.get("id"),
                    subject=updated_event.get("subject", "No Subject"),
                    start_time=start_time,
                    end_time=end_time,
                    location=updated_event.get("location", {}).get("displayName"),
                    description=updated_event.get("bodyPreview"),
                    attendees=updated_event.get("attendees", []),
                    is_all_day=updated_event.get("isAllDay", False),
                    organizer=updated_event.get("organizer")
                )
                
                logger.info(f"Updated calendar event: {event.subject}")
                return event
                
        except Exception as e:
            logger.error(f"Failed to update calendar event: {e}")
            raise
    
    async def delete_calendar_event(
        self,
        access_token: str,
        event_id: str,
        calendar_id: Optional[str] = None
    ) -> bool:
        """
        Delete a calendar event
        
        Args:
            access_token: Azure AD access token
            event_id: Event ID to delete
            calendar_id: Calendar ID (None for default calendar)
            
        Returns:
            True if successful
        """
        try:
            # Use default calendar if no calendar_id provided
            if calendar_id:
                url = f"{self.graph_endpoint}/me/calendars/{calendar_id}/events/{event_id}"
            else:
                url = f"{self.graph_endpoint}/me/events/{event_id}"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=headers)
                response.raise_for_status()
                
                logger.info(f"Deleted calendar event: {event_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete calendar event: {e}")
            raise
