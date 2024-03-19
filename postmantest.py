# import requests
# from requests.auth import HTTPBasicAuth
# import json
#
# url = "https://devsbeta.atlassian.net/rest/api/3/project"
#
# auth = HTTPBasicAuth("info@devsbeta.com", "ATATT3xFfGF0pogUFVOH0_AjBEA8LJcnOJx_Ki4yl_PYkv-LwEBQQp2r37KZYnKm8IGQ-KKXDxCl6qnzxF7BRF0a3pwEeAuKEo2iLK7bHXNQgZgVBAURy5RnTnYXwyifmYqWlCAW6J7u04BqXA6pSSceOPQewIpy0CQzDe8MRqmqZw-zcpzSRS0=110E7FC6")
#
# headers = {
#   "Accept": "application/json"
# }
#
# response = requests.request(
#    "GET",
#    url,
#    headers=headers,
#    auth=auth
# )
#
# print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))


import requests
from base64 import b64encode

# Replace 'your_email' and 'your_api_token' with your actual email and Jira API token
email = 'info@devsbeta.com'
api_token = 'ATATT3xFfGF0pogUFVOH0_AjBEA8LJcnOJx_Ki4yl_PYkv-LwEBQQp2r37KZYnKm8IGQ-KKXDxCl6qnzxF7BRF0a3pwEeAuKEo2iLK7bHXNQgZgVBAURy5RnTnYXwyifmYqWlCAW6J7u04BqXA6pSSceOPQewIpy0CQzDe8MRqmqZw-zcpzSRS0=110E7FC6'

# URL of the API endpoint
url = 'https://devsbeta.atlassian.net/rest/api/3/project'

# Combine email and API token as credentials
credentials = f'{email}:{api_token}'

# Encode credentials in base64
encoded_credentials = b64encode(credentials.encode('utf-8')).decode('utf-8')
print(f"New Auth: {encoded_credentials}")

# Set up headers with the Authorization header
headers = {
    'Authorization': f'Basic {encoded_credentials}'
}

# Make a GET request (you can change this to other HTTP methods as needed)
response = requests.get(url, headers=headers)

# Print the response
print(response.text)
