# IRIS Teams API Integration với GitHub Copilot CLI

Hướng dẫn tích hợp API IRIS Teams với GitHub Copilot CLI để tương tác với Microsoft Teams và Calendar thông qua command line.

## **Cài đặt**

### **1. Cài đặt GitHub Copilot CLI**

```bash
# Cài đặt GitHub Copilot CLI
npm install -g @githubnext/github-copilot-cli

# Hoặc sử dụng Homebrew (macOS)
brew install github/gh/github-copilot-cli
```

### **2. Cấu hình Environment Variables**

```bash
# Linux/macOS
export IRIS_API_URL="http://localhost:8000"
export IRIS_ACCESS_TOKEN="your_azure_ad_access_token"

# Windows PowerShell
$env:IRIS_API_URL="http://localhost:8000"
$env:IRIS_ACCESS_TOKEN="your_azure_ad_access_token"

# Windows Command Prompt
set IRIS_API_URL=http://localhost:8000
set IRIS_ACCESS_TOKEN=your_azure_ad_access_token
```

### **3. Cài đặt Scripts**

#### **Linux/macOS (Bash)**
```bash
# Cấp quyền thực thi
chmod +x copilot-commands/teams-commands.sh

# Tạo alias
echo 'alias copilot-teams="bash copilot-commands/teams-commands.sh"' >> ~/.bashrc
source ~/.bashrc
```

#### **Windows (PowerShell)**
```powershell
# Tạo alias trong PowerShell profile
if (!(Test-Path -Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force
}

Add-Content -Path $PROFILE -Value 'function copilot-teams { & ".\copilot-commands\teams-commands.ps1" @args }'
```

#### **Python Script (Cross-platform)**
```bash
# Cài đặt dependencies
pip install requests

# Cấp quyền thực thi
chmod +x copilot-commands/teams-commands.py

# Tạo alias
echo 'alias copilot-teams="python3 copilot-commands/teams-commands.py"' >> ~/.bashrc
source ~/.bashrc
```

## **Sử dụng**

### **Các lệnh cơ bản**

```bash
# Xem danh sách teams
copilot-teams teams

# Xem channels của một team
copilot-teams channels <team_id>

# Xem group chats
copilot-teams chats

# Gửi tin nhắn đến channel
copilot-teams send-message <team_id> <channel_id> "Hello from Copilot!"

# Gửi tin nhắn đến group chat
copilot-teams send-chat <chat_id> "Hello from Copilot!"

# Xem tin nhắn trong channel
copilot-teams messages <team_id> <channel_id> [max_results]

# Xem tin nhắn trong group chat
copilot-teams chat-messages <chat_id> [max_results]

# Xem calendars
copilot-teams calendars

# Xem events trong calendar
copilot-teams events <calendar_id> [max_results]

# Xem help
copilot-teams help
```

### **Ví dụ sử dụng**

```bash
# 1. Lấy danh sách teams
copilot-teams teams

# 2. Lấy channels của team đầu tiên
copilot-teams channels "team_123"

# 3. Gửi tin nhắn đến channel
copilot-teams send-message "team_123" "channel_456" "Hello from GitHub Copilot!"

# 4. Lấy tin nhắn từ channel
copilot-teams messages "team_123" "channel_456" 10

# 5. Gửi tin nhắn đến group chat
copilot-teams send-chat "chat_789" "Hello from Copilot CLI!"

# 6. Xem calendars
copilot-teams calendars

# 7. Xem events trong calendar
copilot-teams events "calendar_123" 20
```

## **Tích hợp với GitHub Copilot Chat**

### **1. Tạo Custom Actions**

Tạo file `.copilot/actions.yml` trong project:

```yaml
# .copilot/actions.yml
actions:
  - name: "Send Teams Message"
    description: "Send a message to a Teams channel"
    command: "copilot-teams send-message"
    parameters:
      - name: "team_id"
        description: "Team ID"
        required: true
      - name: "channel_id"
        description: "Channel ID"
        required: true
      - name: "message"
        description: "Message content"
        required: true

  - name: "Get Teams List"
    description: "Get list of user's teams"
    command: "copilot-teams teams"

  - name: "Get Team Channels"
    description: "Get channels for a team"
    command: "copilot-teams channels"
    parameters:
      - name: "team_id"
        description: "Team ID"
        required: true

  - name: "Send Chat Message"
    description: "Send a message to a group chat"
    command: "copilot-teams send-chat"
    parameters:
      - name: "chat_id"
        description: "Chat ID"
        required: true
      - name: "message"
        description: "Message content"
        required: true
```

### **2. Sử dụng trong GitHub Copilot Chat**

```bash
# Trong GitHub Copilot Chat, bạn có thể gọi:
@workspace Send Teams Message team_123 channel_456 "Hello from Copilot!"

# Hoặc
@workspace Get Teams List

# Hoặc
@workspace Send Chat Message chat_789 "Hello from Copilot Chat!"
```

## **Tích hợp với VS Code**

### **1. Tạo VS Code Tasks**

Tạo file `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Get Teams",
      "type": "shell",
      "command": "copilot-teams",
      "args": ["teams"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    },
    {
      "label": "Send Teams Message",
      "type": "shell",
      "command": "copilot-teams",
      "args": ["send-message", "${input:teamId}", "${input:channelId}", "${input:message}"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    }
  ],
  "inputs": [
    {
      "id": "teamId",
      "description": "Team ID",
      "default": "",
      "type": "promptString"
    },
    {
      "id": "channelId",
      "description": "Channel ID",
      "default": "",
      "type": "promptString"
    },
    {
      "id": "message",
      "description": "Message",
      "default": "",
      "type": "promptString"
    }
  ]
}
```

### **2. Tạo VS Code Commands**

Tạo file `.vscode/commands.json`:

```json
{
  "commands": [
    {
      "command": "iris-teams.getTeams",
      "title": "Get Teams List",
      "category": "IRIS Teams"
    },
    {
      "command": "iris-teams.sendMessage",
      "title": "Send Teams Message",
      "category": "IRIS Teams"
    }
  ]
}
```

## **Troubleshooting**

### **Lỗi thường gặp**

1. **"IRIS_ACCESS_TOKEN environment variable is not set"**
   ```bash
   # Kiểm tra token đã được set chưa
   echo $IRIS_ACCESS_TOKEN
   
   # Set token nếu chưa có
   export IRIS_ACCESS_TOKEN="your_token_here"
   ```

2. **"API Error: 401 Unauthorized"**
   - Token đã hết hạn, cần lấy token mới
   - Token không có đủ quyền truy cập Teams API

3. **"API Error: 404 Not Found"**
   - API URL không đúng
   - Endpoint không tồn tại

### **Debug**

```bash
# Bật debug mode
export DEBUG=1

# Kiểm tra API response
curl -H "Authorization: Bearer $IRIS_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/v1/teams/teams
```

## **Security**

- **Không commit token vào git**: Sử dụng environment variables
- **Rotate tokens regularly**: Thay đổi token định kỳ
- **Use least privilege**: Chỉ cấp quyền cần thiết cho token

## **Contributing**

Để đóng góp vào project:

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## **License**

MIT License - xem file LICENSE để biết thêm chi tiết.
