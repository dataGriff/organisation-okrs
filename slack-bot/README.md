# OKR Agent Slack Integration

This directory contains a Slack bot that integrates with your OKR Agent API to provide slash commands and interactive queries directly in Slack.

## Features

- `/okr` - Ask natural language questions about OKRs
- `/okr-teams` - List available teams
- `/okr-help` - Show help and usage examples
- Team and quarter filtering
- Rich formatting with emojis
- Error handling and validation

## Setup Instructions

### 1. Create a Slack App

1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "OKR Agent") and select your workspace
4. Go to "OAuth & Permissions" and add these Bot Token Scopes:
   - `commands` (for slash commands)
   - `chat:write` (for sending messages)
   - `chat:write.public` (for posting in public channels)

### 2. Create Slash Commands

In your Slack app settings:

1. Go to "Slash Commands"
2. Create these commands:

**Command: `/okr`**
- Request URL: `https://your-domain.com/slack/events`
- Description: "Ask questions about OKRs"
- Usage Hint: `<question> [team:TeamName] [quarter:2025-Q3]`

**Command: `/okr-teams`**
- Request URL: `https://your-domain.com/slack/events`
- Description: "List available teams"

**Command: `/okr-help`**
- Request URL: `https://your-domain.com/slack/events`
- Description: "Show OKR bot help"

### 3. Get Your Credentials

1. **Bot Token**: Go to "OAuth & Permissions" → Copy "Bot User OAuth Token" (starts with `xoxb-`)
2. **Signing Secret**: Go to "Basic Information" → Copy "Signing Secret"

### 4. Configure Environment

1. Copy `.env.example` to `.env`
2. Fill in your credentials:
```bash
SLACK_BOT_TOKEN=xoxb-your-actual-token
SLACK_SIGNING_SECRET=your-actual-signing-secret
OKR_API_URL=http://okr-agent:8000
```

### 5. Deploy

#### Option A: Docker Compose (Recommended)
```bash
# Start both OKR agent and Slack bot
docker-compose up -d
```

#### Option B: Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python app.py
```

### 6. Set Request URL in Slack

1. Go back to your Slack app settings
2. Update the Request URLs for all slash commands to point to your deployed bot:
   - If using ngrok: `https://abc123.ngrok.io/slack/events`
   - If deployed: `https://your-domain.com/slack/events`

### 7. Install App to Workspace

1. Go to "Install App" in your Slack app settings
2. Click "Install to Workspace"
3. Authorize the app

## Usage Examples

Once installed, you can use these commands in any Slack channel:

```
/okr what are the objectives
/okr key results team:Platform
/okr performance improvements
/okr reduce lead time team:Platform quarter:2025-Q3
/okr risks team:Sales
/okr-teams
/okr-help
```

## Features

### Smart Query Processing
- Natural language questions
- Automatic team/quarter filtering
- Rich formatting with emojis
- Error handling

### Response Formatting
- 🎯 Objectives are highlighted
- 📈 Key Results are listed
- ⚠️ Risks are marked
- 📊 Team filtering shown
- 📅 Quarter filtering shown

### Interactive Elements
- Team exploration buttons
- Help commands
- Error messages with guidance

## Development

### Adding New Commands

1. Add a new function decorated with `@app.command("/your-command")`
2. Update the help text in `/okr-help`
3. Register the command in Slack app settings

### Customizing Responses

Modify the `format_okr_response()` function to change how results are displayed.

### Error Handling

The bot includes comprehensive error handling for:
- API timeouts
- Invalid queries
- Network issues
- Slack API errors

## Troubleshooting

### Common Issues

1. **Commands not working**: Check Request URL in Slack app settings
2. **No responses**: Verify bot token and signing secret
3. **API errors**: Ensure OKR agent is running and accessible
4. **Permission errors**: Check bot scopes in Slack app

### Logs

Check Docker logs for debugging:
```bash
docker-compose logs slack-bot
```

### Health Check

The bot includes a health endpoint:
```bash
curl http://localhost:3000/health
```

## Security Notes

- Never commit `.env` files with real credentials
- Use environment variables in production
- Consider using Slack's socket mode for development
- Implement rate limiting for production use
