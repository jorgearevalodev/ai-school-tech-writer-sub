# AI for Developer Productivity: Technical Writer Agent

## Overview
In this project, we developed a **Technical Writer Agent** to enhance developer productivity. The core functionality of our agent leverages Retrieval-Augmented Generation (RAG) to dynamically update and refine technical documentation. This innovative approach not only streamlines the documentation process but also ensures that it remains accurate, up-to-date, and contextually relevant.

## Now It's Your Turn!
Embrace your creativity and personalize this project to craft a solution that uniquely addresses the challenges and inefficiencies you face in your own environment. After seeing what our Technical Writer Agent can do, it’s time for you to take the reins. Use the foundation we’ve built and apply it to a challenge you face in your own professional or personal environment. Here’s how you can get started:

### Minimum Requirements
1. **RAG Integration:** Successfully integrate Retrieval-Augmented Generation (RAG) to enable your agent to access and utilize external information when generating responses.
2. **Vector Database Implementation:** Create and implement a vector data store capable of embedding and retrieving documents, ensuring that the system can access necessary information efficiently.

### Stretch Goals
1. **Enhanced UI/UX:** Develop a more advanced and user-friendly interface that includes features such as real-time suggestions, auto-completion of content, and a more interactive documentation process.
2. **Automated Content Updates:** Implement a feature where the agent periodically checks and updates existing documentation based on new information or changes in the relevant field, ensuring that all documentation remains current without manual intervention.
3. **Integration with Existing Tools:** Develop integrations for the agent with commonly used development tools and platforms (e.g., Confluence, Jira, Notion) to streamline workflows and increase accessibility.
4. **Add The Features You Want**: Let your creativity shine by adding a unique feature that significantly simplifies or enhances your daily routines. Innovate with functionalities that solve problems and improve efficiency or satisfaction in meaningful ways.

## Privacy and Submission Guidelines
- **Submission Requirements:** Please submit a link to your public repo with your implementation or a loom video showcasing your work on the [BloomTech AI Platform](app.bloomtech.com). 
- **Sensitive Information:** If your implementation involves sensitive information, you are not required to submit a public repository. Instead, a detailed review of your project through a Loom video is acceptable, where you can demonstrate the functionality and discuss the technologies used without exposing confidential data.

---

## Project description

This project is designed to automate various tasks related to managing GitHub issues and releases. It provides a web interface and a console interface to interact with GitHub repositories, allowing users to document issues, update issue statuses, generate release notes, and more.

## Features

- **Document GitHub Issues**: Automatically document the details and comments of a GitHub issue.
- **Update Issue Status**: Update the status of an issue in a GitHub project.
- **Generate Release Notes**: Generate comprehensive release notes for a list of issues.
- **Create or Update Releases**: Create or update a release on a GitHub repository.
- **Add Comments to Issues**: Add comments to a GitHub issue.
- **Delete Tags**: Delete a tag from a GitHub repository.
- **List All Releases**: List all releases for a product.
- **Get Similar Issues**: Retrieve similar issues from a vector database.

## Demo

A video is available [here](https://drive.google.com/file/d/1xsi8EjarjIBv-_UhEmXXZRdUKE_HkQEA/view?usp=drive_link)

This GitHub project can be used to test the application:
https://github.com/users/jorgearevalodev/projects/1
https://github.com/jorgearevalodev/sample_repo/releases

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/jorgearevalodev/ai-school-tech-writer.git
    cd ai-school-tech-writer
    ```

2. Create and activate a virtual environment:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up environment variables:
    - Create a `.env` file in the root directory of the project.
    - Add the following environment variables:
        ```env
        GITHUB_TOKEN=your_github_token
        REPO_OWNER=your_repo_owner
        REPO_NAME=your_repo_name
        MAINTENANCE_REPO=your_maintenance_repo
        USE_CONSOLE=False  # Set to 'True' to use console mode
        ```

## Usage

### Web Interface

1. Run the web application:
    ```sh
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```

2. Open your browser and navigate to `http://localhost:8000`.

3. Use the web interface to interact with GitHub issues and releases.

### Console Interface

1. Set `USE_CONSOLE=True` in your `.env` file.

2. Run the console application:
    ```sh
    python main.py
    ```

3. Follow the prompts to interact with GitHub issues and releases.

## Code Structure

- **main.py**: Entry point of the application. Determines whether to run the web or console interface.
- **web_app.py**: Contains the FastAPI web application and endpoints.
- **code_assistant.py**: Contains functions to load predefined prompts and start the agent.
- **issue_documenter.py**: Contains the `IssueDocumenter` class and various functions to interact with GitHub issues and releases.
- **content_generator.py**: Contains functions to generate content using OpenAI's language model.

## Example Code References

### `issue_documenter.py`

- **Class Definition and Initialization**:
- **Get Issue Details and Comments**:
- **Update Issue Status**:
- **Document Issue**:

### `web_app.py`

- **Web Application Setup**:
- **Root Endpoint**:

### `content_generator.py`

- **Extract Issue Information**:
- **Generate Release Notes for Issue**:
