curl -X 'POST' \
  'http://0.0.0.0:8000/v1/chat/completions' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "model": "string",
  "messages": [
    {
      "role": "user",
      "content": "啊啊啊啊我跟你说",
      "tool_calls": [
        {
          "id": "call_default",
          "type": "function",
          "function": {
            "name": "string",
            "arguments": "string"
          }
        }
      ]
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "string",
        "description": "string",
        "parameters": {}
      }
    }
  ],
  "do_sample": true,
  "temperature": 0,
  "top_p": 0,
  "n": 1,
  "max_tokens": 128,
  "stream": false
}'
