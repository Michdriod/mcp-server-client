#!/usr/bin/env python3
import requests
import json

# Test the query endpoint
response = requests.post(
    'http://localhost:8000/api/query',
    headers={'Content-Type': 'application/json'},
    json={'question': 'How many customers do we have?', 'user_id': 1}
)

print(f"Status Code: {response.status_code}")
print(f"\nResponse Headers:")
for key, value in response.headers.items():
    print(f"  {key}: {value}")

print(f"\nResponse Body:")
print(json.dumps(response.json(), indent=2))
