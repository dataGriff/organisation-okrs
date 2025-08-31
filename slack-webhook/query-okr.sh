#!/bin/bash

# Simple script to query OKR agent and post to Slack
# Usage: ./query-okr.sh "what are the objectives" "Platform"

QUERY="$1"
TEAM="$2"
QUARTER="$3"

# Configuration
OKR_API_URL="http://localhost:8000"
SLACK_WEBHOOK_URL="YOUR_SLACK_WEBHOOK_URL_HERE"

# Build API URL
API_URL="${OKR_API_URL}/ask?q=${QUERY}"
if [ ! -z "$TEAM" ]; then
    API_URL="${API_URL}&team=${TEAM}"
fi
if [ ! -z "$QUARTER" ]; then
    API_URL="${API_URL}&quarter=${QUARTER}"
fi

# Query OKR API
echo "Querying OKR Agent..."
RESPONSE=$(curl -s "${API_URL}")

# Extract bullets from JSON response
BULLETS=$(echo "$RESPONSE" | jq -r '.bullets[]' 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$BULLETS" ]; then
    echo "Error querying OKR agent or no results found"
    exit 1
fi

# Format for Slack
SLACK_MESSAGE="🎯 *OKR Query Results*\n"
SLACK_MESSAGE="${SLACK_MESSAGE}❓ Query: ${QUERY}\n"
if [ ! -z "$TEAM" ]; then
    SLACK_MESSAGE="${SLACK_MESSAGE}📊 Team: ${TEAM}\n"
fi
if [ ! -z "$QUARTER" ]; then
    SLACK_MESSAGE="${SLACK_MESSAGE}📅 Quarter: ${QUARTER}\n"
fi
SLACK_MESSAGE="${SLACK_MESSAGE}\n"

# Add bullets with emojis
while IFS= read -r bullet; do
    if [[ "$bullet" == Objective:* ]]; then
        SLACK_MESSAGE="${SLACK_MESSAGE}🎯 *${bullet}*\n"
    elif [[ "$bullet" == KR* ]]; then
        SLACK_MESSAGE="${SLACK_MESSAGE}📈 ${bullet}\n"
    else
        SLACK_MESSAGE="${SLACK_MESSAGE}• ${bullet}\n"
    fi
done <<< "$BULLETS"

# Post to Slack
curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"${SLACK_MESSAGE}\"}" \
    "$SLACK_WEBHOOK_URL"

echo "Posted to Slack!"
