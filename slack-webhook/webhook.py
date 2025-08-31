"""
Simple Slack Webhook Integration for OKR Agent
This creates webhook endpoints that can be called from Slack workflows
"""

from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Your OKR Agent API URL
OKR_API_BASE = os.environ.get("OKR_API_URL", "http://localhost:8000")

@app.route("/webhook/okr", methods=["POST"])
def okr_webhook():
    """Handle OKR queries from Slack workflows"""
    data = request.json
    
    # Extract parameters from Slack workflow
    query = data.get("query", "")
    team = data.get("team", "")
    quarter = data.get("quarter", "")
    
    if not query:
        return jsonify({
            "response_type": "ephemeral",
            "text": "❌ Please provide a query"
        })
    
    # Build API request
    params = {"q": query}
    if team:
        params["team"] = team
    if quarter:
        params["quarter"] = quarter
    
    try:
        # Query OKR Agent
        response = requests.get(f"{OKR_API_BASE}/ask", params=params, timeout=30)
        response.raise_for_status()
        okr_data = response.json()
        
        # Format response for Slack
        formatted_response = format_slack_response(okr_data)
        
        return jsonify({
            "response_type": "in_channel",
            "text": formatted_response
        })
        
    except requests.RequestException as e:
        return jsonify({
            "response_type": "ephemeral", 
            "text": f"❌ Error querying OKR agent: {str(e)}"
        })

def format_slack_response(data):
    """Format OKR data for Slack"""
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
        return "No results found."
    
    # Format bullets with emojis
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

@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3001))
    app.run(host="0.0.0.0", port=port)
