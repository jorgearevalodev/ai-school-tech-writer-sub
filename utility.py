import os
import base64
from openai import OpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_openai.chat_models.base import ChatOpenAI

def format_data_for_openai(diffs, readme_content, commit_messages):
    prompt = None

    # Combine the changes into a string with clear delineation.
    changes = "\n".join(
        [f"File: {diff['filename']}\nPatch: {diff['patch']}\n" for diff in diffs]
    )

    # Combine all commit messages

    # Decode the README content

    # Construct the prompt with clear instructions for the LLM.
    prompt = "".join([
         f"Please review the following code changes and commit messages from a GitHub pull request:\n"
        ,"Code changes from Pull Request:\n"
        ,f"{changes}\n"
        ,"Commit messages:\n"
        ,f"{commit_messages}"
        ,"Here is the current README file content:\n"
        ,f"{readme_content}\n"
        ,"Consider the code changes and commit messages, determine if the README needs to be updated. If so, edit the README, ensuring to maintain its existing style and clarity.\n"
        ,"Updated README:\n"
    ])

    return prompt

def call_openai(prompt):
    client = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-3.5-turbo")
    try:
        messages=[
             {"role":"system", "content":"You are an AI trained to help with updating README files based on commit messages and code"}
            ,{"role":"user", "content":prompt}
        ]
        response = client.invoke(input=messages)
        parser= StrOutputParser()
        content= parser.invoke(input=response)
        return content
    except Exception as e:
        print(e)
        return None
    pass


def update_readme_and_create_pr(repo, updated_readme, readme_sha):
    commit_message = "AI COMMIT: Proposed README update based on recent code changes."

    commit_sha = os.getenv('COMMIT_SHA')
    main_branch = repo.get_branch('main')
    new_branch_name = f'update-readme-{commit_sha[:7]}'
    new_branch = repo.create_git_ref(ref=f'refs/heads/{new_branch_name}', sha=main_branch.commit.sha)

    repo.update_file("README.md", commit_message, updated_readme, readme_sha, branch=new_branch_name)

    pr_title = "AI PR: Update README based on recent change"
    pr_body = "This is an AI PR. Please review the README"
    pull_request = repo.create_pull(title=pr_title, body=pr_body, head=new_branch_name, base="main")

    return pull_request
