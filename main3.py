from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contentextraction import full_text
import requests
import json

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

# Add CORS middleware to handle cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, adjust as needed
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],  # Allow POST and OPTIONS methods
    allow_headers=["*"],  # Allow all headers
)

class RequestData(BaseModel):
    prompt: str  # Define the structure of the request payload

@app.post("/api/generate", response_class=StreamingResponse)
async def generate_response(data: RequestData, request: Request):
    external_api_url = 'http://localhost:11434/api/generate'  # External API URL

    # Create the payload with the prompt and context
    payload = {
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
        "stream": True
    }

    try:
        # Make a POST request to the external API with streaming enabled
        response = requests.post(external_api_url, json=payload, stream=True)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        async def stream_response():
            accumulated_response = ""  # Initialize an empty string to accumulate the response
            try:
                # Stream the response content line by line
                for line in response.iter_lines():
                    if line:
                        try:
                            line_data = line.decode('utf-8')  # Decode the line
                            data = json.loads(line_data)
                            accumulated_response += data.get("response", "")  # Accumulate the response part
                            if data.get("done"):  # Check if the stream is done
                                complete_response = json.loads(accumulated_response)  # Parse the complete JSON
                                yield json.dumps(complete_response)  # Send the final complete JSON
                                return
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {e}")  # Handle JSON errors
                            continue
            except requests.RequestException as e:
                raise HTTPException(status_code=500, detail=f"Error connecting to external API: {str(e)}")
        
        # Return the streaming response to the client
        return StreamingResponse(stream_response(), media_type="application/json")
    
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to external API: {str(e)}")
