# IRIS Teams API Commands for GitHub Copilot CLI (PowerShell)
# Usage: copilot teams <command> [options]

param(
    [Parameter(Position=0)]
    [string]$Command,
    
    [Parameter(Position=1)]
    [string]$Param1,
    
    [Parameter(Position=2)]
    [string]$Param2,
    
    [Parameter(Position=3)]
    [string]$Param3
)

# Configuration
$API_URL = if ($env:IRIS_API_URL) { $env:IRIS_API_URL } else { "http://localhost:8000" }
$ACCESS_TOKEN = $env:IRIS_ACCESS_TOKEN

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

# Function to check if token is set
function Test-Token {
    if (-not $ACCESS_TOKEN) {
        Write-Host "Error: IRIS_ACCESS_TOKEN environment variable is not set" -ForegroundColor $Red
        Write-Host "Please set it with: `$env:IRIS_ACCESS_TOKEN='your_azure_ad_token'" -ForegroundColor $Yellow
        exit 1
    }
}

# Function to make API calls
function Invoke-IRISAPI {
    param(
        [string]$Method,
        [string]$Endpoint,
        [string]$Data
    )
    
    Test-Token
    
    $headers = @{
        "Authorization" = "Bearer $ACCESS_TOKEN"
        "Content-Type" = "application/json"
    }
    
    $uri = "$API_URL$Endpoint"
    
    try {
        if ($Data) {
            $response = Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers -Body $Data
        } else {
            $response = Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers
        }
        
        return $response | ConvertTo-Json -Depth 10
    }
    catch {
        Write-Host "API Error: $($_.Exception.Message)" -ForegroundColor $Red
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "Response: $responseBody" -ForegroundColor $Red
        }
        exit 1
    }
}

# Main command handler
switch ($Command) {
    "teams" {
        Write-Host "Fetching user teams..." -ForegroundColor $Blue
        Invoke-IRISAPI -Method "GET" -Endpoint "/api/v1/teams/teams"
    }
    
    "channels" {
        if (-not $Param1) {
            Write-Host "Error: Team ID is required" -ForegroundColor $Red
            Write-Host "Usage: copilot teams channels <team_id>" -ForegroundColor $Yellow
            exit 1
        }
        Write-Host "Fetching channels for team: $Param1" -ForegroundColor $Blue
        Invoke-IRISAPI -Method "GET" -Endpoint "/api/v1/teams/teams/$Param1/channels"
    }
    
    "chats" {
        Write-Host "Fetching user group chats..." -ForegroundColor $Blue
        Invoke-IRISAPI -Method "GET" -Endpoint "/api/v1/teams/chats"
    }
    
    "send-message" {
        if (-not $Param1 -or -not $Param2) {
            Write-Host "Error: Team ID and Channel ID are required" -ForegroundColor $Red
            Write-Host "Usage: copilot teams send-message <team_id> <channel_id> <message>" -ForegroundColor $Yellow
            exit 1
        }
        
        $message = if ($Param3) { $Param3 } else { "Hello from Copilot CLI!" }
        Write-Host "Sending message to channel: $Param2" -ForegroundColor $Blue
        
        $data = @{
            content = $message
            content_type = "text"
        } | ConvertTo-Json
        
        Invoke-IRISAPI -Method "POST" -Endpoint "/api/v1/teams/teams/$Param1/channels/$Param2/messages" -Data $data
    }
    
    "send-chat" {
        if (-not $Param1 -or -not $Param2) {
            Write-Host "Error: Chat ID and message are required" -ForegroundColor $Red
            Write-Host "Usage: copilot teams send-chat <chat_id> <message>" -ForegroundColor $Yellow
            exit 1
        }
        
        Write-Host "Sending message to chat: $Param1" -ForegroundColor $Blue
        
        $data = @{
            content = $Param2
            content_type = "text"
        } | ConvertTo-Json
        
        Invoke-IRISAPI -Method "POST" -Endpoint "/api/v1/teams/chats/$Param1/messages" -Data $data
    }
    
    "messages" {
        if (-not $Param1 -or -not $Param2) {
            Write-Host "Error: Team ID and Channel ID are required" -ForegroundColor $Red
            Write-Host "Usage: copilot teams messages <team_id> <channel_id> [max_results]" -ForegroundColor $Yellow
            exit 1
        }
        
        $maxResults = if ($Param3) { $Param3 } else { 50 }
        Write-Host "Fetching messages from channel: $Param2" -ForegroundColor $Blue
        
        Invoke-IRISAPI -Method "GET" -Endpoint "/api/v1/teams/teams/$Param1/channels/$Param2/messages?max_results=$maxResults"
    }
    
    "chat-messages" {
        if (-not $Param1) {
            Write-Host "Error: Chat ID is required" -ForegroundColor $Red
            Write-Host "Usage: copilot teams chat-messages <chat_id> [max_results]" -ForegroundColor $Yellow
            exit 1
        }
        
        $maxResults = if ($Param2) { $Param2 } else { 50 }
        Write-Host "Fetching messages from chat: $Param1" -ForegroundColor $Blue
        
        Invoke-IRISAPI -Method "GET" -Endpoint "/api/v1/teams/chats/$Param1/messages?max_results=$maxResults"
    }
    
    "calendars" {
        Write-Host "Fetching user calendars..." -ForegroundColor $Blue
        Invoke-IRISAPI -Method "GET" -Endpoint "/api/v1/calendar/calendars"
    }
    
    "events" {
        if (-not $Param1) {
            Write-Host "Error: Calendar ID is required" -ForegroundColor $Red
            Write-Host "Usage: copilot teams events <calendar_id> [max_results]" -ForegroundColor $Yellow
            exit 1
        }
        
        $maxResults = if ($Param2) { $Param2 } else { 50 }
        Write-Host "Fetching events from calendar: $Param1" -ForegroundColor $Blue
        
        Invoke-IRISAPI -Method "GET" -Endpoint "/api/v1/calendar/calendars/$Param1/events?max_results=$maxResults"
    }
    
    "help" {
        Write-Host "IRIS Teams API Commands for GitHub Copilot CLI" -ForegroundColor $Green
        Write-Host ""
        Write-Host "Available commands:" -ForegroundColor $Yellow
        Write-Host "  teams                    - Get user's teams"
        Write-Host "  channels <team_id>       - Get channels for a team"
        Write-Host "  chats                    - Get user's group chats"
        Write-Host "  send-message <team_id> <channel_id> [message] - Send message to channel"
        Write-Host "  send-chat <chat_id> <message>                - Send message to group chat"
        Write-Host "  messages <team_id> <channel_id> [max_results] - Get channel messages"
        Write-Host "  chat-messages <chat_id> [max_results]         - Get chat messages"
        Write-Host "  calendars                - Get user's calendars"
        Write-Host "  events <calendar_id> [max_results]           - Get calendar events"
        Write-Host "  help                     - Show this help"
        Write-Host ""
        Write-Host "Environment variables:" -ForegroundColor $Yellow
        Write-Host "  IRIS_API_URL            - API base URL (default: http://localhost:8000)"
        Write-Host "  IRIS_ACCESS_TOKEN       - Azure AD access token (required)"
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor $Yellow
        Write-Host "  `$env:IRIS_ACCESS_TOKEN='your_token_here'"
        Write-Host "  copilot teams teams"
        Write-Host "  copilot teams send-message team123 channel456 'Hello from Copilot!'"
    }
    
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor $Red
        Write-Host "Use 'copilot teams help' for available commands" -ForegroundColor $Yellow
        exit 1
    }
}
