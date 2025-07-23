import requests

url = "http://localhost:5001/api/chat"  # Updated to port 5001
payload = {
    "user_id": "test_user_charlie",
    "message": "Hey Charlie, I’m UTG in a $1/$2 cash game with AK suited and 8 at the table. The table’s been wild—players from mid to the button are super aggressive and love 3-betting light. I want to raise preflop to set the tone, but I’m also almost certain I’ll get reraised. Do I flat a 3-bet with AKs from this position or should I go ahead and 4-bet? My main concern is being out of position post-flop and missing. If the flop comes low and I brick, am I just checking and giving up or is there a line that keeps the pressure on?",
    "context": {
        "intent": "coaching",
        "debug": True  # Optional: Use this to print RAG steps and model path
    }
}

response = requests.post(url, json=payload)
print(response.json())
