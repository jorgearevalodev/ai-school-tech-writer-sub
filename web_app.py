from code_assistant import call_agent, load_predefined_prompts
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Define the input model for the POST request
class InputModel(BaseModel):
    text: str

# Initialize the FastAPI app
app = FastAPI()

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize the Jinja2 templates directory
templates = Jinja2Templates(directory="templates")

# Function to process the input text using the call_agent function
def process_input(text: str) -> str:
    result = call_agent(text)
    return f"Processed: {result}"

# Define the root endpoint to serve the main HTML page
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    # Load predefined prompts
    predefined_prompts = load_predefined_prompts()
    prompts = []
    for prompt in predefined_prompts:
        prompts.append({
            "prompt": prompt['id'],
            "title": prompt['title'],
            "whole_text": prompt['prompt']
        })
    # Render the index.html template with the predefined prompts
    return templates.TemplateResponse("index.html", {"request": request, 
                                                     "predefined_prompts": prompts})

# Define the endpoint to process the input text
@app.post("/process")
def process_text(input: InputModel):
    result = process_input(input.text)
    return {"result": result}

# Run the FastAPI app with Uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)