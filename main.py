import os
from dotenv import load_dotenv
from code_assistant import start_agent

# Load environment variables from a .env file
load_dotenv()

# Check if the application should run in console mode
use_console = os.getenv('USE_CONSOLE', 'False').lower() == 'true'

# If not in console mode, import and run the web application
if not use_console:
    import web_app
# If in console mode, start the agent
elif __name__ == "__main__":
    start_agent()