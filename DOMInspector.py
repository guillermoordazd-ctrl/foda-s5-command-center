import requests
import json
import time

def send_dom_inspection():
    try:
        response = requests.get('http://localhost:8501/')
        if response.status_code == 200:
            print("Server is responding. We need to inspect the DOM via JS injection.")
        else:
            print(f"Status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

send_dom_inspection()
