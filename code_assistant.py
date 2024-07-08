from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import TextLoader
from langchain_community.tools.shell.tool import ShellTool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.tools import tool
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain_openai import ChatOpenAI
#from prompt import *
from issue_documenter import add_comment_to_issue, create_or_update_release, delete_tag, document_github_issue, get_similar_issues, list_all_releases, list_github_issues, search_issues
from git_files_comparer import compare_files_between_commits
from content_generator import  extract_issue_information, generate_release_table, generate_release_notes, generate_release_notes_for_issue, prepare_release_notes 
import os

@tool
def look_at_existing_app():
    """
    Retrieve all file names within the 'app' directory.

    This function loads the contents of the 'app' directory and extracts the file names.

    Returns:
        list: A list of file names present in the 'app' directory.
    """
    code = DirectoryLoader(f"./app/", silent_errors=True).load()
    return [c.metadata["source"] for c in code]

def load_documents(directory, encoding='utf-8'):
    documents = []
    for filename in os.listdir(directory):
        if filename.endswith('.md'):
            with open(os.path.join(directory, filename), 'r', encoding=encoding) as file:
                content = file.read()
                documents.append({'source': filename, 'content': content})
    return documents


@tool
def get_page_contents(files):
    """
    Retrieve the current contents for the given file names.

    This function loads the contents of the specified files and formats them.
    The contents should be edited and not completely replaced.

    Args:
        files (list): A list of file names whose contents need to be retrieved.

    Returns:
        list: A list of formatted strings containing the file names and their contents.
    """
    loader = TextLoader(files[0])
    return [f"___{doc.metadata['source']}___\n{doc.page_content}" for doc in loader.load()]
    directory = 'issues'
    documents = load_documents(directory)
    return [f"___{doc['source']}___\n{doc['content']}" for doc in documents]

@tool
def generate_unit_tests(function_code):
    """
    Generates the unit tests using OpenAI and `unittest` python library.
    """
    model_name = os.getenv('GPT_MODEL_NAME')
    llm = ChatOpenAI(
        model_name=model_name,
        temperature=0,
    )

    system_prompt = open('prompts/agent_prompt.md').read()

    prompt_str = f"""
    {system_prompt}
    
    ## Function to be tested:
    ```python
    {function_code}
    ```

    ## Generate comprehensive unit tests for the function above:
    """

    response = llm.invoke(prompt_str)
    return response

@tool
def update_file(file_path, new_content):
    """
    Add content to an existing file.
    """
    try:
        # Open the file in write mode
        with open(file_path, 'w') as file:
            # Write the new content to the file
            file.write(new_content)
        print("File updated successfully.")
    except Exception as e:
        print("Error:", e)

@tool
def create_new_file(filename: str):
    """Only use this if the file is not created already. 
    If it is, then use the tool get_page_contents. 
    Creates a new file with the given filename. 
    Only use this function when the file doesn't already exist."""
    with open(filename, 'w'):
        pass

@tool
def document_github_issue_tool(issue_id: int, repo: str):
    """Use this to download all information about a GitHub issue
    The information will be saved in the file issues/issue_<issue_id>_documentation.md
    repo is the name of the GitHub repository:
    'maintenance' for maintenance issues
    'release' for issues related to product releases
    """
    if repo == 'maintenance':
        repo = os.getenv('MAINTENANCE_REPO')
    else:
        repo = os.getenv('RELEASE_REPO')
    return document_github_issue(issue_id, repo)

@tool
def list_all_releases_tool():
    """Use this to list all the releases in the repository"""
    return list_all_releases()

@tool
def get_similar_issues_tool(issue_number: int, repo_name: str):
    """Use this to get a list of similar issues to the one provided.
    Args:
        issue_number (int): _description_
        repo_name (str): _description_
    repo_name is the name of the repository where the issue is located:
    'maintenance' for maintenance issues
    'release' for issues related to product releases
    Returns:
        _type_: _description_
    """
    if repo_name == 'maintenance':
        repo_name = os.getenv('MAINTENANCE_REPO')
    else:
        repo_name = os.getenv('RELEASE_REPO')
    return get_similar_issues(issue_number, repo_name)

@tool
def list_release_line_issues(product: str=None, status: str='open'):
    """Use this to get the status of all GitHub issues created to generate a release for a version
    of the specified product.
    status can be 'open' for releases that are not yet released or 'closed' for releases that are already released.
    this only retrieves the GH issues associated to the task of making a release
    for the product just send Noneprovide one of these:
    """
    repo_release = os.getenv('RELEASE_REPO')
    release_issues = search_issues(product=product, status=status, repo_name=repo_release)
    sorted_issues = sorted(release_issues, key=lambda k: k['number']*-1)
    return sorted_issues[0] if len(sorted_issues) > 0 else None


@tool
def delete_tag_tool(tag_name:str, product: str):
    """Use this to delete a tag from the repository.

    Args:
        tag_name (str): The name of the tag to be deleted.
        product (str): The name of the product for which the tag is to be deleted.
    """
    delete_tag(tag_name, product)
    
@tool
def add_comment_to_issue_tool(issue_number: int, comment: str, repo_name: str):
    """Use this to add a comment to a GitHub issue.
    please provide the issue number, the comment and the name of the repository
    for the repository provide one of these:
    maintenance for maintenance issues
    release for issues related to product releases
    Args:
        issue_number (int): _description_
        comment (str): _description_
        repo_name (str): _description_
    """
    if repo_name == 'maintenance':
        repo_name = os.getenv('MAINTENANCE_REPO')
    else:
        repo_name = os.getenv('RELEASE_REPO')   
    add_comment_to_issue(issue_number=issue_number, comment=comment, repo_name=repo_name)

@tool
def list_github_issues_tool(project_number: int, status: str= None, product: str= None):
    """Use this to get the status of all GitHub issues for a specific project or product.
       Please specify the project number.
       When available specify the status, the options available are:
       'backlog' for issues not yet triaged
       'to do' for issues that are ready to work on and have not started yet
       'in progress' for issues that are being worked on
       'in review' for issues that are ready for review
       'for release' for issues that are ready to be released
       'done' for resolved issues that are closed
       'all' for all issues
       When available specify the product, the options available are:
       or 'all' for all products
       'all' for all issues
    """
    print(f'Getting the status of all GitHub issues for project {project_number} and status {status}')
    status = 'all' if status is None else status.lower()
    product = 'all' if product is None else product.lower()
    return list_github_issues(project_number, status, product)


@tool
def generate_release_table_tool(issue_numbers: list[int]):
    """Use this too to generate a table with the information of the issues included in the release we are preparing 
    pass a list with the GitHub issues id, for the release we should consider only the issues in the Pending Release state
    """
    issue_info = { }
    for issue_number in issue_numbers:
        #issue_notes[issue_number] = generate_release_notes_for_issue(issue_number)
        if not os.path.exists(f'issues/issue_{issue_number}_documentation.md'):
            document_github_issue(issue_number)
        issue_info[issue_number] = extract_issue_information(issue_number)

    result = generate_release_table(issue_info)
    return result


@tool
def generate_release_notes_for_issue_tool(issue_numbers: list[int], product=''):
    """Use this tool to generate a detailed release notes for each issue included in the release we are preparing
    pass a list with the GitHub issues id, for the release we should consider only the issues in the Pending Release state
    
    product is the name of the product that is being released: maintenance
    """
    issue_notes = { }
    for issue_number in issue_numbers:
        if not os.path.exists(f'issues/issue_{issue_number}_documentation.md'):
            document_github_issue(issue_number)
        issue_notes[issue_number] = generate_release_notes_for_issue(issue_number)

    return issue_notes




@tool
def generate_release_notes_tool(issue_numbers: list[int], build_tag: str, release_issue_number: int=0, product: str = 'maintenance'):
    """Use this tool to generate a release notes statement that we will deliver as part of the release we are preparing
    pass a list with the GitHub issues id, for the release we should consider only the issues in the Pending Release state
    pass a build_tag parameter with the github tag we will be using, use the tag from the release
    pass a release_issue_number this is GitHub issue id where we will document the release
    pass a product parameter with the name of the product that is being released: maintenace
    """
    with open('releases/v1.0.md', 'r') as file:
        content = file.read()

    content = prepare_release_notes(build_tag, issue_numbers, release_issue_number, product)

    create_or_update_release('maintenance', build_tag, content)

    return content


@tool
def compare_files_between_commits_tool(commit_a: str = None, commit_b: str = None):
    """
    Use this to extract the content of the files that have changed between two commits.
    if the second commit is not specified, the comparison will be between the first commit and the parent commit.
    if the first commit is not specified, the comparison will be between the uncommited changes and head
    The repo is assumed to be the repo we are currently working on.
    this function will return a path to a file containing the content of the files that have changed.
    both versions of the files will be saved in the output file, the before and after the change.
    no analysis will be performed on the files. only the content will be saved.
    """
    return compare_files_between_commits("C:/github/repo-folder", commit_a, commit_b)

@tool
def create_or_update_release_tool(build_tag:str, release_notes:str, product:str = 'maintenance'):
    """Use this to create or update a release for a repository in GitHub.
    if the release does not exist it will be created, otherwise it will be updated.
    the text provided in release_notes will be used as the body of the release.
    Args:
        product: name of the product that is being released: maintenance
        build_tag: the tag that will be used to identify the release
        release_notes: use the release notes generated by the tool generate_release_notes
    """
    create_or_update_release(product, build_tag, release_notes)

predefined_prompts = []
def load_predefined_prompts():
    print("Loading predefined prompts...")
    prompts = []
    global predefined_prompts
    predefined_prompts = []
    with open('prompts/predefined_prompts.md', 'r') as file:
        content = file.read()
        prompts = content.split('##')   
        for i in range(len(prompts)):
            parts = prompts[i].strip().split('\n')
            if len(parts) < 2:
                continue
            predefined_prompts.append({
                'title': parts[0],
                'prompt': "\n".join(parts[1:]).strip(),
                'id': f'{i}'
            })
    print(f"Loaded {len(prompts)} predefined prompts: {predefined_prompts}")
    return predefined_prompts


def start_agent():
    load_predefined_prompts()
    # Main loop to prompt the user
    while True:
        print("Enter 'exit' to quit.")
        print("Enter 'help' to see a list of predefined prompts.")
        user_prompt = input("Prompt: ")
        if user_prompt == 'exit':
            break
        elif user_prompt == 'help':
            print("Predefined prompts:")
            global predefined_prompts
            for i, prompt in enumerate(predefined_prompts):
                print(f"{i+1}. {prompt['title']}")
            continue
        call_agent(user_prompt)

agent_executor = None
def initialize_agent():
    # List of tools to use
    tools = [
        ShellTool(ask_human_input=True),
        look_at_existing_app,
        get_page_contents,
        generate_unit_tests,
        create_new_file,
        update_file,
        document_github_issue_tool,
        list_github_issues_tool,
        delete_tag_tool,
        add_comment_to_issue_tool,
        #list_release_line_issues,
        list_all_releases_tool,
        get_similar_issues_tool,
        compare_files_between_commits_tool,
        generate_release_table_tool,
        generate_release_notes_for_issue_tool,
        generate_release_notes_tool,
        create_or_update_release_tool
        # Add more tools if needed
    ]


    # Configure the language model
    model_name = os.getenv('GPT_MODEL_NAME')
    llm = ChatOpenAI(model=model_name, temperature=0.5)


    # Set up the prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert web developer.",
            ),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )


    # Bind the tools to the language model
    llm_with_tools = llm.bind_tools(tools)


    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_tool_messages(
                x["intermediate_steps"]
            ),
        }
        | prompt
        | llm_with_tools
        | OpenAIToolsAgentOutputParser()
    )


    global agent_executor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)



def call_agent(user_prompt):
    if agent_executor is None:
        initialize_agent()

    if user_prompt.isdigit():
        index = int(user_prompt) - 1
        if index < len(predefined_prompts):
            user_prompt = predefined_prompts[index]['prompt']
            print(f"Selected prompt: {predefined_prompts[index]['title']}, prompt: {user_prompt}")
        else:
            print("Invalid prompt number.")
            return "Invalid prompt number."

    result = list(agent_executor.stream({"input": user_prompt}))
    return result[-1]['output'] 