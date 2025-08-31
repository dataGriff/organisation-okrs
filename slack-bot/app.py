"""
Slack Bot Integration for OKR Agent
Provides slash commands and interactive features for querying OKRs
"""

import os
import json
import requests
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request

# Initialize Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Flask app for handling Slack events
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

# Your OKR Agent API URL
OKR_API_BASE = os.environ.get("OKR_API_URL", "http://localhost:8000")

def query_okr_agent(query, team=None, quarter=None):
    """Query the OKR agent API"""
    params = {"q": query}
    if team:
        params["team"] = team
    if quarter:
        params["quarter"] = quarter
    
    try:
        response = requests.get(f"{OKR_API_BASE}/ask", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": f"Failed to query OKR agent: {str(e)}"}

def format_okr_response(data):
    """Format OKR response for Slack"""
    if "error" in data:
        return f"❌ Error: {data['error']}"
    
    query = data.get("query", "")
    bullets = data.get("bullets", [])
    team = data.get("team")
    quarter = data.get("quarter")
    
    # Build response
    response = f"🎯 *Results for: {query}*\n"
    if team:
        response += f"📊 Team: *{team}*\n"
    if quarter:
        response += f"📅 Quarter: *{quarter}*\n"
    response += "\n"
    
    if not bullets:
        response += "No results found."
        return response
    
    # Format bullets with emojis for better readability
    for bullet in bullets:
        if bullet.startswith("Objective:"):
            response += f"🎯 *{bullet}*\n"
        elif bullet.startswith("KR"):
            response += f"📈 {bullet}\n"
        elif "risk" in bullet.lower():
            response += f"⚠️ {bullet}\n"
        else:
            response += f"• {bullet}\n"
    
    return response

@app.command("/okr")
def okr_command(ack, respond, command):
    """Handle /okr slash command"""
    ack()
    
    text = command["text"].strip()
    
    if not text:
        respond("ℹ️ Usage: `/okr <question> [team:TeamName] [quarter:2025-Q3]`\n" +
                "Examples:\n" +
                "• `/okr what are the objectives`\n" +
                "• `/okr key results team:Platform`\n" +
                "• `/okr performance improvements team:Sales quarter:2025-Q3`")
        return
    
    # Parse team and quarter from command text
    parts = text.split()
    team = None
    quarter = None
    query_parts = []
    
    for part in parts:
        if part.startswith("team:"):
            team = part[5:]
        elif part.startswith("quarter:"):
            quarter = part[8:]
        else:
            query_parts.append(part)
    
    query = " ".join(query_parts)
    
    if not query:
        respond("❌ Please provide a question to search for.")
        return
    
    # Query the OKR agent
    data = query_okr_agent(query, team, quarter)
    response = format_okr_response(data)
    
    respond(response)

@app.command("/okr-teams")
def okr_teams_command(ack, respond):
    """List available teams"""
    ack()
    
    try:
        # Get all teams by querying without filters
        response = requests.get(f"{OKR_API_BASE}/ask", params={"q": "teams"}, timeout=10)
        data = response.json()
        
        # Extract unique teams from citations
        teams = set()
        for citation in data.get("citations", []):
            path = citation.get("path", "")
            if "teams/" in path:
                team_name = path.split("teams/")[1].split("/")[0]
                teams.add(team_name.title())
        
        if teams:
            teams_list = ", ".join(sorted(teams))
            respond(f"📊 *Available Teams:*\n{teams_list}")
        else:
            respond("No teams found.")
    except Exception as e:
        respond(f"❌ Error fetching teams: {str(e)}")

@app.command("/okr-help")
def okr_help_command(ack, respond):
    """Show help for OKR commands"""
    ack()
    
    help_text = """
🎯 *OKR Agent Help*

*Available Commands:*
• `/okr <question>` - Ask questions about OKRs
• `/okr-teams` - List available teams
• `/okr-help` - Show this help

*Query Examples:*
• `/okr what are the objectives`
• `/okr key results team:Platform`
• `/okr performance improvements`
• `/okr reduce lead time team:Platform`
• `/okr risks team:Sales quarter:2025-Q3`

*Filters:*
• `team:TeamName` - Filter by specific team
• `quarter:2025-Q3` - Filter by specific quarter

*Tips:*
• Ask natural language questions
• Use specific terms like "objectives", "key results", "risks"
• Combine filters for more targeted results
"""
    respond(help_text)

# Interactive button for exploring teams
@app.action("explore_team")
def handle_explore_team(ack, body, respond):
    """Handle team exploration button clicks"""
    ack()
    
    team = body["actions"][0]["value"]
    data = query_okr_agent("objectives and key results", team=team)
    response = format_okr_response(data)
    
    respond(response)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """Handle Slack events"""
    return handler.handle(request)

@flask_app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "okr-slack-bot"}

if __name__ == "__main__":
    # Start the Flask app
    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host="0.0.0.0", port=port, debug=False)
