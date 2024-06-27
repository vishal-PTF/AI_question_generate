from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contentextraction import full_text
import requests
import json
 
app = FastAPI()
 
class RequestData(BaseModel):
    prompt: str
 
@app.post("/api/generate")
def generate_response(data: RequestData):
    # URL of the API you want to proxy to
    external_api_url = 'http://localhost:11434/api/generate'  # Replace with your actual API URL
 
    # JSON payload to send to the external API
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
        # Make a POST request to the external API
        response = requests.post(external_api_url, json=payload, stream=True)
        # Check if the request was successful (status code 200)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        # Initialize an empty string to accumulate the response parts
        accumulated_response = ""

            # Iterate over lines in the response content
        for line in response.iter_lines():
            if line:
                try:
                # Decode line to string
                    line_data = line.decode('utf-8')
                    # Parse the JSON object from the line
                    data = json.loads(line_data)
                    # Accumulate the response parts
                    accumulated_response += data.get("response", "")

                    # Check if the 'done' key is present and True
                    if data.get("done"):
                        # Combine all parts to form the complete JSON response
                        complete_response_json = accumulated_response
                        inner_data = json.loads(complete_response_json)
                        # Print or process the complete response
                        print("Complete Response:")
                        # print(inner_data)
                        return inner_data
                      # Exit loop once 'done' is received
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    continue
            else:
                # If 'done' was not received
                raise HTTPException(status_code=500, detail="Stream ended without receiving 'done'.")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to external API: {str(e)}")