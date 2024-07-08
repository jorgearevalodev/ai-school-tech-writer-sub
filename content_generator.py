from datetime import datetime
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from issue_documenter import IssueDocumenter
from dotenv import load_dotenv
import os

model_name = os.getenv('GPT_MODEL_NAME')

def generate_release_table(issues):
    llm = ChatOpenAI(model=model_name, temperature=0)
    release_brief_template = open('prompts/release_table.md').read()
    prompt = ChatPromptTemplate.from_template(release_brief_template)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    result=chain.invoke({
        "tickets": issues
    })
    print(result, '\n-------------------------\n')
    return result


def generate_release_brief(issue_notes):
    llm = ChatOpenAI(model=model_name, temperature=0)
    release_brief_template = open('prompts/release_brief.md').read()
    prompt = ChatPromptTemplate.from_template(release_brief_template)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    result=chain.invoke({
        "issue_notes": issue_notes
    })
    print(result, '\n-------------------------\n')
    return result

def extract_issue_information(issue_number):
    # Set up the OpenAI LLM
    llm = ChatOpenAI(model=model_name, temperature=0)
    release_notes_template = open('prompts/extract_issue_information.md').read()

    prompt = ChatPromptTemplate.from_template(release_notes_template)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser

    #check if file exists
    if not os.path.exists(f'issues/issue_{issue_number}_documentation.md'):
        raise Exception(f'document for issue {issue_number} does not exist yet')
    issue_info = open(f'issues/issue_{issue_number}_documentation.md', encoding='utf-8').read()

    result = chain.invoke({
        "issue_content": issue_info
    })
    print(result, '\n-------------------------\n')
    return result

def generate_release_notes_for_issue(issue_number):
    # Set up the OpenAI LLM
    model_name = os.getenv('GPT_MODEL_NAME')
    llm = ChatOpenAI(model=model_name, temperature=0)


    release_notes_template = open("prompts/release_notes_for_issue.md").read()

    prompt = ChatPromptTemplate.from_template(release_notes_template)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser

    load_dotenv()
    github_token = os.getenv('GITHUB_TOKEN')
    repo_owner = os.getenv('REPO_OWNER')
    repo_name = os.getenv('REPO_NAME')

    documenter = IssueDocumenter(github_token, repo_owner, repo_name, issue_number)
    issue_info = documenter.document_issue()

    result = chain.invoke({ "issue_url": f"https://github.com/{repo_owner}/{repo_name}/issues/{issue_number}",
        "issue_content": issue_info
    })
    print(result, '\n-------------------------\n')
    return result


def generate_release_notes(build_tag, issue_numbers, release_issue_number, issue_notes, brief, product: str=None, release_table: str=None):
    # reade the prompt from prompts/release_notes.md

    if product is None:
        raise Exception('product is not specified')

    prompt_for_product = {
        'maintenance': 'prompts/release_notes_maintenance.md',
    }
    if product not in prompt_for_product:
        raise Exception(f'no prompt found for product {product}')
    print(f'using prompt for product {product}, prompt file: {prompt_for_product[product]}')

    release_notes_template = open(prompt_for_product[product]).read()
    #release_notes_template = open('prompts/release_notes.md').read()

    # Set up the OpenAI LLM
    llm = ChatOpenAI(model=model_name, temperature=0)

    prompt = ChatPromptTemplate.from_template(release_notes_template)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser

    result = chain.invoke({
        'build_tag': build_tag,
        'issues_list': issue_numbers,
        'release_issue_number': release_issue_number,
        'release_version': build_tag,
        'issue_notes': issue_notes,
        'brief': brief,
        'release_date': datetime.now().strftime('%Y-%m-%d'),
        'release_table': release_table,
        'organization': os.getenv('REPO_OWNER'),
        'maintenance_repo': os.getenv('MAINTENANCE_REPO'),
        'release_repo': os.getenv('RELEASE_REPO')
    })

    #save to a file with the name of the release wu
    with open(f'releases/{build_tag}.md', 'w', encoding='utf-8') as f:
        f.write(result)

    #print(f'release notes for {build_tag} generated and saved to releases/{build_tag}.md')
    print(f'release notes for {build_tag} generated')

    #return f'''release notes for {build_tag} generated and saved to releases/{build_tag}.md.
    return f"Release notes for {build_tag}: {result}"


def prepare_release_notes(build_tag, issue_numbers, release_issue_number, product):
    issue_notes = { }
    issue_info = { }
    for issue_number in issue_numbers:
        issue_notes[issue_number] = generate_release_notes_for_issue(issue_number)
        issue_info[issue_number] = extract_issue_information(issue_number)

    release_table = generate_release_table(issue_info)
    print(release_table, '\n-------------------------\n')

    brief = generate_release_brief(issue_notes)

    result = generate_release_notes(build_tag, issue_numbers, release_issue_number, issue_notes, brief, product, release_table)
    print(result, '\n-------------------------\n')

    return result


def prepare_verification_notes(build_tag, issue_numbers, release_date, release_issue_number):
    issue_notes = { }
    issue_info = { }
    for issue_number in issue_numbers:
        #issue_notes[issue_number] = generate_release_notes_for_issue(issue_number)
        issue_info[issue_number] = extract_issue_information_verification(issue_number)

    result = issue_info
    print(result, '\n-------------------------\n')

    return result


def extract_issue_information_verification(issue_number):
    # Set up the OpenAI LLM
    llm = ChatOpenAI(model=model_name, temperature=0)
    release_notes_template = open('prompts/verification.md').read()

    prompt = ChatPromptTemplate.from_template(release_notes_template)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser

    issue_info = open(f'issues/issue_{issue_number}_documentation.md', encoding='utf-8').read()

    result = chain.invoke({
        "issue_info": issue_info
    })
    print(result, '\n-------------------------\n')
    return result

if __name__ == '__main__':
    build_tag = '1.7.0.164'
    issue_numbers = [7213, 8295, 8278, 8394, 7182, 7180]
    release_date = datetime.today().strftime('%Y-%m-%d')
    release_issue_number = 717

    #prepare_release_notes(build_tag, issue_numbers, release_date, release_issue_number)
    #prepare_verification_notes(build_tag, issue_numbers, release_date, release_issue_number)