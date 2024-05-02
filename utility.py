import os
import base64
from openai import OpenAI

def format_data_for_openai(diffs, readme_content, commit_messages):
    prompt = None

    # Combine the changes into a string with clear delineation.

    # Combine all commit messages

    # Decode the README content

    # Construct the prompt with clear instructions for the LLM.

    return prompt

def call_openai(prompt):
    pass

def update_readme_and_create_pr(repo, updated_readme, readme_sha):
    pass