#!/usr/bin/env python3
"""
IRIS Teams API Commands for GitHub Copilot CLI
Usage: copilot teams <command> [options]
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, Dict, Any

# Configuration
API_URL = os.getenv('IRIS_API_URL', 'http://localhost:8000')
ACCESS_TOKEN = os.getenv('IRIS_ACCESS_TOKEN')

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_colored(text: str, color: str):
    """Print colored text"""
    print(f"{color}{text}{Colors.NC}")

def check_token():
    """Check if access token is set"""
    if not ACCESS_TOKEN:
        print_colored("Error: IRIS_ACCESS_TOKEN environment variable is not set", Colors.RED)
        print_colored("Please set it with: export IRIS_ACCESS_TOKEN='your_azure_ad_token'", Colors.YELLOW)
        sys.exit(1)

def api_call(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make API call to IRIS Teams API"""
    check_token()
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    url = f"{API_URL}{endpoint}"
    
    try:
        if data:
            response = requests.request(method, url, headers=headers, json=data)
        else:
            response = requests.request(method, url, headers=headers)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print_colored(f"API Error: {e}", Colors.RED)
        if hasattr(e, 'response') and e.response is not None:
            print_colored(f"Response: {e.response.text}", Colors.RED)
        sys.exit(1)

def get_teams():
    """Get user's teams"""
    print_colored("Fetching user teams...", Colors.BLUE)
    result = api_call("GET", "/api/v1/teams/teams")
    print(json.dumps(result, indent=2))

def get_channels(team_id: str):
    """Get channels for a team"""
    print_colored(f"Fetching channels for team: {team_id}", Colors.BLUE)
    result = api_call("GET", f"/api/v1/teams/teams/{team_id}/channels")
    print(json.dumps(result, indent=2))

def get_chats():
    """Get user's group chats"""
    print_colored("Fetching user group chats...", Colors.BLUE)
    result = api_call("GET", "/api/v1/teams/chats")
    print(json.dumps(result, indent=2))

def send_message(team_id: str, channel_id: str, message: str = "Hello from Copilot CLI!"):
    """Send message to channel"""
    print_colored(f"Sending message to channel: {channel_id}", Colors.BLUE)
    data = {
        "content": message,
        "content_type": "text"
    }
    result = api_call("POST", f"/api/v1/teams/teams/{team_id}/channels/{channel_id}/messages", data)
    print(json.dumps(result, indent=2))

def send_chat_message(chat_id: str, message: str):
    """Send message to group chat"""
    print_colored(f"Sending message to chat: {chat_id}", Colors.BLUE)
    data = {
        "content": message,
        "content_type": "text"
    }
    result = api_call("POST", f"/api/v1/teams/chats/{chat_id}/messages", data)
    print(json.dumps(result, indent=2))

def get_messages(team_id: str, channel_id: str, max_results: int = 50):
    """Get messages from channel"""
    print_colored(f"Fetching messages from channel: {channel_id}", Colors.BLUE)
    result = api_call("GET", f"/api/v1/teams/teams/{team_id}/channels/{channel_id}/messages?max_results={max_results}")
    print(json.dumps(result, indent=2))

def get_chat_messages(chat_id: str, max_results: int = 50):
    """Get messages from group chat"""
    print_colored(f"Fetching messages from chat: {chat_id}", Colors.BLUE)
    result = api_call("GET", f"/api/v1/teams/chats/{chat_id}/messages?max_results={max_results}")
    print(json.dumps(result, indent=2))

def get_calendars():
    """Get user's calendars"""
    print_colored("Fetching user calendars...", Colors.BLUE)
    result = api_call("GET", "/api/v1/calendar/calendars")
    print(json.dumps(result, indent=2))

def get_events(calendar_id: str, max_results: int = 50):
    """Get events from calendar"""
    print_colored(f"Fetching events from calendar: {calendar_id}", Colors.BLUE)
    result = api_call("GET", f"/api/v1/calendar/calendars/{calendar_id}/events?max_results={max_results}")
    print(json.dumps(result, indent=2))

def show_help():
    """Show help information"""
    print_colored("IRIS Teams API Commands for GitHub Copilot CLI", Colors.GREEN)
    print()
    print_colored("Available commands:", Colors.YELLOW)
    print("  teams                    - Get user's teams")
    print("  channels <team_id>       - Get channels for a team")
    print("  chats                    - Get user's group chats")
    print("  send-message <team_id> <channel_id> [message] - Send message to channel")
    print("  send-chat <chat_id> <message>                - Send message to group chat")
    print("  messages <team_id> <channel_id> [max_results] - Get channel messages")
    print("  chat-messages <chat_id> [max_results]         - Get chat messages")
    print("  calendars                - Get user's calendars")
    print("  events <calendar_id> [max_results]           - Get calendar events")
    print("  help                     - Show this help")
    print()
    print_colored("Environment variables:", Colors.YELLOW)
    print("  IRIS_API_URL            - API base URL (default: http://localhost:8000)")
    print("  IRIS_ACCESS_TOKEN       - Azure AD access token (required)")
    print()
    print_colored("Examples:", Colors.YELLOW)
    print("  export IRIS_ACCESS_TOKEN='your_token_here'")
    print("  copilot teams teams")
    print("  copilot teams send-message team123 channel456 'Hello from Copilot!'")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="IRIS Teams API Commands for GitHub Copilot CLI")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("param1", nargs="?", help="First parameter")
    parser.add_argument("param2", nargs="?", help="Second parameter")
    parser.add_argument("param3", nargs="?", help="Third parameter")
    
    args = parser.parse_args()
    
    if args.command == "teams":
        get_teams()
    elif args.command == "channels":
        if not args.param1:
            print_colored("Error: Team ID is required", Colors.RED)
            print_colored("Usage: copilot teams channels <team_id>", Colors.YELLOW)
            sys.exit(1)
        get_channels(args.param1)
    elif args.command == "chats":
        get_chats()
    elif args.command == "send-message":
        if not args.param1 or not args.param2:
            print_colored("Error: Team ID and Channel ID are required", Colors.RED)
            print_colored("Usage: copilot teams send-message <team_id> <channel_id> <message>", Colors.YELLOW)
            sys.exit(1)
        send_message(args.param1, args.param2, args.param3)
    elif args.command == "send-chat":
        if not args.param1 or not args.param2:
            print_colored("Error: Chat ID and message are required", Colors.RED)
            print_colored("Usage: copilot teams send-chat <chat_id> <message>", Colors.YELLOW)
            sys.exit(1)
        send_chat_message(args.param1, args.param2)
    elif args.command == "messages":
        if not args.param1 or not args.param2:
            print_colored("Error: Team ID and Channel ID are required", Colors.RED)
            print_colored("Usage: copilot teams messages <team_id> <channel_id> [max_results]", Colors.YELLOW)
            sys.exit(1)
        max_results = int(args.param3) if args.param3 else 50
        get_messages(args.param1, args.param2, max_results)
    elif args.command == "chat-messages":
        if not args.param1:
            print_colored("Error: Chat ID is required", Colors.RED)
            print_colored("Usage: copilot teams chat-messages <chat_id> [max_results]", Colors.YELLOW)
            sys.exit(1)
        max_results = int(args.param2) if args.param2 else 50
        get_chat_messages(args.param1, max_results)
    elif args.command == "calendars":
        get_calendars()
    elif args.command == "events":
        if not args.param1:
            print_colored("Error: Calendar ID is required", Colors.RED)
            print_colored("Usage: copilot teams events <calendar_id> [max_results]", Colors.YELLOW)
            sys.exit(1)
        max_results = int(args.param2) if args.param2 else 50
        get_events(args.param1, max_results)
    elif args.command in ["help", "-h", "--help"]:
        show_help()
    else:
        print_colored(f"Unknown command: {args.command}", Colors.RED)
        print_colored("Use 'copilot teams help' for available commands", Colors.YELLOW)
        sys.exit(1)

if __name__ == "__main__":
    main()

