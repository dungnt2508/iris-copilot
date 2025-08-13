#!/bin/bash

# IRIS Teams API Commands for GitHub Copilot CLI
# Usage: copilot teams <command> [options]

API_URL="${IRIS_API_URL:-http://localhost:8000}"
ACCESS_TOKEN="${IRIS_ACCESS_TOKEN}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if token is set
check_token() {
    if [ -z "$ACCESS_TOKEN" ]; then
        echo -e "${RED}Error: IRIS_ACCESS_TOKEN environment variable is not set${NC}"
        echo "Please set it with: export IRIS_ACCESS_TOKEN='your_azure_ad_token'"
        exit 1
    fi
}

# Function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    check_token
    
    if [ -n "$data" ]; then
        curl -s -X "$method" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_URL$endpoint"
    else
        curl -s -X "$method" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" \
            "$API_URL$endpoint"
    fi
}

# Function to format JSON output
format_json() {
    if command -v jq &> /dev/null; then
        jq '.'
    else
        cat
    fi
}

# Main command handler
case "$1" in
    "teams")
        echo -e "${BLUE}Fetching user teams...${NC}"
        api_call "GET" "/api/v1/teams/teams" | format_json
        ;;
    
    "channels")
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Team ID is required${NC}"
            echo "Usage: copilot teams channels <team_id>"
            exit 1
        fi
        echo -e "${BLUE}Fetching channels for team: $2${NC}"
        api_call "GET" "/api/v1/teams/teams/$2/channels" | format_json
        ;;
    
    "chats")
        echo -e "${BLUE}Fetching user group chats...${NC}"
        api_call "GET" "/api/v1/teams/chats" | format_json
        ;;
    
    "send-message")
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo -e "${RED}Error: Team ID and Channel ID are required${NC}"
            echo "Usage: copilot teams send-message <team_id> <channel_id> <message>"
            exit 1
        fi
        
        local team_id=$2
        local channel_id=$3
        local message=${4:-"Hello from Copilot CLI!"}
        
        echo -e "${BLUE}Sending message to channel: $channel_id${NC}"
        local data="{\"content\": \"$message\", \"content_type\": \"text\"}"
        api_call "POST" "/api/v1/teams/teams/$team_id/channels/$channel_id/messages" "$data" | format_json
        ;;
    
    "send-chat")
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo -e "${RED}Error: Chat ID and message are required${NC}"
            echo "Usage: copilot teams send-chat <chat_id> <message>"
            exit 1
        fi
        
        local chat_id=$2
        local message=$3
        
        echo -e "${BLUE}Sending message to chat: $chat_id${NC}"
        local data="{\"content\": \"$message\", \"content_type\": \"text\"}"
        api_call "POST" "/api/v1/teams/chats/$chat_id/messages" "$data" | format_json
        ;;
    
    "messages")
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo -e "${RED}Error: Team ID and Channel ID are required${NC}"
            echo "Usage: copilot teams messages <team_id> <channel_id> [max_results]"
            exit 1
        fi
        
        local team_id=$2
        local channel_id=$3
        local max_results=${4:-50}
        
        echo -e "${BLUE}Fetching messages from channel: $channel_id${NC}"
        api_call "GET" "/api/v1/teams/teams/$team_id/channels/$channel_id/messages?max_results=$max_results" | format_json
        ;;
    
    "chat-messages")
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Chat ID is required${NC}"
            echo "Usage: copilot teams chat-messages <chat_id> [max_results]"
            exit 1
        fi
        
        local chat_id=$2
        local max_results=${3:-50}
        
        echo -e "${BLUE}Fetching messages from chat: $chat_id${NC}"
        api_call "GET" "/api/v1/teams/chats/$chat_id/messages?max_results=$max_results" | format_json
        ;;
    
    "calendars")
        echo -e "${BLUE}Fetching user calendars...${NC}"
        api_call "GET" "/api/v1/calendar/calendars" | format_json
        ;;
    
    "events")
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Calendar ID is required${NC}"
            echo "Usage: copilot teams events <calendar_id> [max_results]"
            exit 1
        fi
        
        local calendar_id=$2
        local max_results=${3:-50}
        
        echo -e "${BLUE}Fetching events from calendar: $calendar_id${NC}"
        api_call "GET" "/api/v1/calendar/calendars/$calendar_id/events?max_results=$max_results" | format_json
        ;;
    
    "help"|"-h"|"--help")
        echo -e "${GREEN}IRIS Teams API Commands for GitHub Copilot CLI${NC}"
        echo ""
        echo "Available commands:"
        echo "  teams                    - Get user's teams"
        echo "  channels <team_id>       - Get channels for a team"
        echo "  chats                    - Get user's group chats"
        echo "  send-message <team_id> <channel_id> [message] - Send message to channel"
        echo "  send-chat <chat_id> <message>                - Send message to group chat"
        echo "  messages <team_id> <channel_id> [max_results] - Get channel messages"
        echo "  chat-messages <chat_id> [max_results]         - Get chat messages"
        echo "  calendars                - Get user's calendars"
        echo "  events <calendar_id> [max_results]           - Get calendar events"
        echo "  help                     - Show this help"
        echo ""
        echo "Environment variables:"
        echo "  IRIS_API_URL            - API base URL (default: http://localhost:8000)"
        echo "  IRIS_ACCESS_TOKEN       - Azure AD access token (required)"
        echo ""
        echo "Examples:"
        echo "  export IRIS_ACCESS_TOKEN='your_token_here'"
        echo "  copilot teams teams"
        echo "  copilot teams send-message team123 channel456 'Hello from Copilot!'"
        ;;
    
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Use 'copilot teams help' for available commands"
        exit 1
        ;;
esac
