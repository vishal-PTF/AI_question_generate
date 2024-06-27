from fastapi import FastAPI, HTTPException
import requests
import json
from pydantic import BaseModel
from contentextraction import full_text

# Initialize FastAPI app
app = FastAPI()

# Pydantic model for request body
class RequestData(BaseModel):
    prompt: str

# Endpoint to handle POST requests
@app.post("/api/generate")
def generate_response(data: RequestData):
    # URL of the API you want to proxy to
    external_api_url = 'http://localhost:11434/api/generate'  # Replace with your actual API URL

    # JSON payload to send to the external API
    payload = {
        # "model": "llama3",  # Example model name
        # "prompt": data.prompt
        "model": "llama3",
        "prompt": f""" Hi llama i am given you a context {full_text},on the basis of give context {data.prompt} this query is Objective and informative for General audience interested in technology and its impacts,and Provide the MCQs in JSON format,
        ans for the example
        In recent decades, climate change has become a pressing global issue. The rise in greenhouse gas emissions, primarily due to human activities such as burning fossil fuels and deforestation, has led to increased global temperatures and noticeable changes in weather patterns. Scientists warn that without significant reductions in emissions, the consequences could include more frequent and severe natural disasters, rising sea levels, and disruptions to ecosystems and agriculture.
         question 1.: What is the primary cause of rising global temperatures according to the context?,
                A. Natural climate cycles
                B. Industrial pollution
                C. Increased volcanic activity
                D. Deforestation
        correct_answer:B

        Respond using JSON
        """,
        "format": "json",
        "stream": False  
    }

    try:
        # Make a POST request to the external API
        response = requests.post(external_api_url, json=payload)

        # Check if request was successful (status code 200)
        if response.status_code == 200:
            # Parse JSON response from the external API
            response_data = response.json()
            # print(response_data)
            response_json=response_data.get('response','')
            inner_data=json.loads(response_json)
            
            # Return the response from the external API
            return {
                "model": response_data.get("model", ""),
                "created_at": response_data.get("created_at", ""),
                # "response": response_data.get("response", ""),
                "response":inner_data,
                "done": response_data.get("done", False)
                # response_data
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to external API: {str(e)}")




# new
'''

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
import requests
import json
from pydantic import BaseModel
from contentextraction import full_text

app = FastAPI()

class RequestData(BaseModel):
    prompt: str

# Store connected clients
clients = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process incoming data
            request_data = json.loads(data)
            prompt = request_data.get("prompt")
            response = generate_response(prompt)
            await websocket.send_text(json.dumps(response))
    except WebSocketDisconnect:
        clients.remove(websocket)

def generate_response(prompt: str):
    external_api_url = 'http://localhost:11434/api/generate'  # Replace with your actual API URL
    payload = {
        "model": "llama3",
        "prompt": f"{prompt} on the basis of the given context {full_text} respond using JSON",
        "format": "json",
        "stream": False  
    }

    try:
        response = requests.post(external_api_url, json=payload)

        if response.status_code == 200:
            response_data = response.json()
            response_json = response_data.get('response', '')
            inner_data = json.loads(response_json)
            
            return {
                "model": response_data.get("model", ""),
                "created_at": response_data.get("created_at", ""),
                "response": inner_data,
                "done": response_data.get("done", False)
            }
        else:
            return {"error": response.text}
    except requests.RequestException as e:
        return {"error": f"Error connecting to external API: {str(e)}"}

@app.post("/api/generate")
def generate_response_api(data: RequestData):
    return generate_response(data.prompt)
'''
