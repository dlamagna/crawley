#!/usr/bin/env bash
#
# test_curl_chat_format.sh
#
# Usage:
#   ./test_curl_chat_format.sh <file_path> <prompt_url>
#
# Example:
#   ./test_curl_chat_format.sh ./example_content.md https://app.bysim.ai/api/glacomscracontact
#
# This sends a POST request with the JSON:
# {
#   "chat": [
#     {
#       "role": "user",
#       "content": "<contents of the file>"
#     }
#   ]
# }

FILE_PATH="$1"
PROMPT_URL="$2"

if [ -z "$FILE_PATH" ] || [ -z "$PROMPT_URL" ]; then
  echo "Usage: $0 <file_path> <prompt_url>"
  exit 1
fi

# Make sure the file exists
if [ ! -f "$FILE_PATH" ]; then
  echo "Error: file '$FILE_PATH' not found."
  exit 1
fi

# Read the file into a JSON string
# -R: raw input lines
# -s: read all lines into one string
# This ensures special chars/newlines are properly escaped
CONTENT=$(cat "$FILE_PATH" | jq -Rsa .)

# Build the JSON payload:
# { "chat": [ { "role": "user", "content": "<CONTENT>" } ] }
JSON_PAYLOAD=$(jq -n --arg content "$CONTENT" \
  '{"chat":[{"role":"user","content": $content}]}' )

echo "Sending payload to $PROMPT_URL ..."
echo "---------------"
echo "$JSON_PAYLOAD" | jq .
echo "---------------"
echo

# Send the request
# Includes X-Authorization: freedom, as per your example
RESPONSE=$(curl -s -X POST "$PROMPT_URL" \
  -H "Content-Type: application/json" \
  -H "X-Authorization: freedom" \
  -d "$JSON_PAYLOAD")

# Pretty-print the JSON response
echo "Response from server:"
echo "$RESPONSE" | jq .
