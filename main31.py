from fastapi import FastAPI, HTTPException, Request,File, UploadFile, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contentextraction import extract_text_from_pdf
import requests
import json
import os

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
async def generate_response(prompt: str = Form(...), file: UploadFile = File(None)):
    context_text = prompt
    external_api_url = 'http://localhost:11434/api/generate'  # External API URL
    if file:
        try:
            # Save the uploaded file temporarily
            file_path = f"/tmp/{file.filename}"
            with open(file_path, "wb") as buffer:
                buffer.write(file.file.read())
            
            # Extract text from the PDF file
            context_text = extract_text_from_pdf(file_path)
            
            # Clean up the temporary file
            os.remove(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing PDF file: {str(e)}")

    # Create the payload with the prompt and context
    payload = {
        "model": "llama3",
        "prompt": f""" Hi llama i am given you a context {context_text},on the basis of give context {prompt} this query is Objective and informative for General audience interested in technology and its impacts,and Provide the MCQs in JSON format,
        ans for example
       The Amazon rainforest, often referred to as the "lungs of the Earth," plays a critical role in regulating the global climate. Spanning over 5.5 million square kilometers across nine countries in South America, it is home to an unparalleled diversity of flora and fauna. The forest acts as a massive carbon sink, absorbing billions of tons of carbon dioxide annually, which helps mitigate the effects of climate change. However, deforestation driven by logging, agriculture, and mining poses a significant threat to this vital ecosystem. Conservation efforts are crucial to preserve the Amazon, not only for its environmental benefits but also for the indigenous communities that rely on its resources for their livelihood.
         question 1.: What is the primary role of the Amazon rainforest in the global climate?
                A. Providing timber for construction
                B. Acting as a massive carbon sink
                C. Serving as a habitat for polar bears
                D. Generating renewable energy
        correct_answer:B Acting as a massive carbon sink
        question 2.: How many countries does the Amazon rainforest span across?
                A. Seven
                B. Eight
                C. Nine
                D. Ten
        correct_answer:C Nine
        question 3.: What are the main threats to the Amazon rainforest mentioned in the paragraph?
                A. Urban development and pollution
                B. Logging, agriculture, and mining
                C. Tourism and recreational activities
                D. Fishing and hunting
        correct_answer:B Logging, agriculture, and mining
        question 4.: Why are conservation efforts in the Amazon rainforest important, according to the paragraph?
                A. To increase tourism revenue
                B. To expand agricultural land
                C. To preserve the environment and support indigenous communities
                D. To build new cities
        correct_answer:C To preserve the environment and support indigenous communities
        question 5.: Which phrase is used to describe the Amazon rainforest's role in regulating the global climate?
                A. "Heart of the world"
                B. "Lungs of the Earth"
                C. "Brain of the planet"
                D. "Kidneys of nature"
        correct_answer:B "Lungs of the Earth"
        
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
                            accumulated_response += data.get("response", "")
                            print(accumulated_response)  # Accumulate the response part
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
