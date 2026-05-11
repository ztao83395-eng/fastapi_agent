import requests

url = "http://127.0.0.1:8000/api/agent/chat"
headers = {
    "accept": "application/json",
    "Authorization": "Bearer 6425d404-5c72-4043-aa1b-02085fdf12c9",
    "Content-Type": "application/json"
}
data = {"question": "收藏新闻111"}

response = requests.post(url, headers=headers, json=data)
print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}")