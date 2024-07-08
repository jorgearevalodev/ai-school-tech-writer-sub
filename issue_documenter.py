from datetime import datetime, timedelta
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from vector_database import VectorDatabase

# Initialize the database
database = None
if not database:
    database = VectorDatabase()

class IssueDocumenter:
    def __init__(self, github_token, repo_owner, repo_name, issue_number=None):
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.issue_number = issue_number
        self.base_url = f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}'
        self.output_dir = 'downloads'
        self.headers = {'Authorization': f'token {self.github_token}'}
        os.makedirs(self.output_dir, exist_ok=True)

    # Method to get issue details and comments from GitHub
    def get_issue(self):
        issue_url = f'{self.base_url}/issues/{self.issue_number}'
        headers = {'Authorization': f'token {self.github_token}'}
        issue_response = requests.get(issue_url, headers=headers)
        if issue_response.status_code == 404:
            print(f"Issue {self.issue_number} not found")
            return None, None
        issue_response.raise_for_status()
        issue_data = issue_response.json()

        comments_url = f'{self.base_url}/issues/{self.issue_number}/comments'
        comments_response = requests.get(comments_url, headers=headers)
        comments_response.raise_for_status()
        comments_data = comments_response.json()

        return issue_data, comments_data
    
    # Method to update the status of an issue in a GitHub project
    def update_issue_status(self, issue_number, status, project_number, org_name=None, user_name=None):
        graphql_url = 'https://api.github.com/graphql'
        headers = {
            'Authorization': f'Bearer {self.github_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/vnd.github.vixen-preview+json'
        }

        mutation_query = """
        mutation($projectId: ID!, $itemId: ID!, $status: String!) {
            updateProjectV2ItemFieldValue(
                input: {
                    projectId: $projectId,
                    itemId: $itemId,
                    fieldId: "status",
                    value: "Done"
                }
            ) {
                projectV2Item {
                    id
                }
            }
        }
        """

        project_query = """
        query($owner: String!, $projectNumber: Int!) {
            {entity}(login: $owner) {
                projectV2(number: $projectNumber) {
                    id
                }
            }
        }
        """.replace("{entity}", "organization" if org_name else "user")

        project_variables = {
            'owner': org_name if org_name else user_name,
            'projectNumber': project_number
        }

        response = requests.post(
            graphql_url,
            headers=headers,
            json={'query': project_query, 'variables': project_variables}
        )
        response.raise_for_status()
        project_data = response.json()
        project_id = project_data['data']['organization' if org_name else 'user']['projectV2']['id']

        item_query = """
        query($projectId: ID!) {
            node(id: $projectId) {
                ... on ProjectV2 {
                    items(first: 100) {
                        edges {
                            node {
                                id
                                content {
                                    ... on Issue {
                                        number
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        item_variables = {
            'projectId': project_id,
            #'issueNumber': issue_number
        }

        response = requests.post(
            graphql_url,
            headers=headers,
            json={'query': item_query, 'variables': item_variables}
        )
        response.raise_for_status()
        item_data = response.json()
        item_id = next(edge['node']['id'] for edge in item_data['data']['node']['items']['edges'] if edge['node']['content']['number'] == issue_number)

        update_variables = {
            'projectId': project_id,
            'itemId': item_id,
            'status': status
        }

        response = requests.post(
            graphql_url,
            headers=headers,
            json={'query': mutation_query, 'variables': update_variables}
        )
        #response.raise_for_status()
        print(f"Issue {issue_number} status updated to {status} in project {project_number}")

    # Method to get similar issues from the vector database
    def get_similar_issues(self):
        content = self.document_issue()
        global database
        results = database.query_documents(content, n_results=5)
        print(f"Found {len(results)} results")
        results = [result for result in results if result['id'] != f'issue_{self.issue_number}']
        distance_threshold = os.getenv('DISTANCE_THRESHOLD', 0.5)
        results = [result for result in results if result['distance'] < distance_threshold]
        print(f"Found {len(results)} similar issues ")
        return results

    # Method to download a file from a URL
    def download_file(self, url):
        local_filename = os.path.join(self.output_dir, url.split('/')[-1])
        with requests.get(url, stream=True) as r:
            try:
                r.raise_for_status()
            except:
                return
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename

    # Method to document an issue and its comments
    def document_issue(self):
        issue, comments = self.get_issue()
        if not issue:
            return f"Issue {self.issue_number} not found"

        document_content = []
        output_dir = 'downloads'
        os.makedirs(output_dir, exist_ok=True)

        # Add the main issue details to the document content
        document_content.append(f"# Issue #{self.issue_number}: {issue['title']}\n")
        document_content.append(f"**Author:** {issue['user']['login']}\n")
        document_content.append(f"**Date:** {issue['created_at']}\n")
        document_content.append(f"**Status:** {issue['state']}\n")
        document_content.append(f"**Labels:** {', '.join(label['name'] for label in issue['labels'])}\n\n")
        document_content.append(f"## Description\n")
        document_content.append(f"{issue['body']}\n")

        # Add a separator before the comments
        document_content.append(f"-------------------------------------\n")
        document_content.append(f"## Comments\n")

        # Now process the comments
        for comment in comments:
            soup = BeautifulSoup(comment['body'], 'html.parser')
            
            document_content.append(f"### Comment by {comment['user']['login']}\n")
            document_content.append(f"**Date:** {comment['created_at']}\n\n")
            #document_content.append(f"{comment['body']}\n")

            comment_lines = comment['body'].split('\n')
            blockquoted_comment = '\n'.join(f'> {line}' for line in comment_lines if line.strip() != '')
            document_content.append(blockquoted_comment + '\n')

            # Process images and links within the comment
            for img in soup.find_all('img'):
                img_url = img['src']
                #downloaded_image = self.download_file(img_url, output_dir)
                downloaded_image = self.download_file(img_url)
                document_content.append(f"![Downloaded image]({downloaded_image})\n")

            for link in soup.find_all('a'):
                link_url = link['href']
                if link_url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    downloaded_link = self.download_file(link_url, output_dir)
                    document_content.append(f"![Downloaded file]({downloaded_link})\n")
                else:
                    document_content.append(f"[Link]({link_url})\n")

            # Add a separator between comments
            document_content.append(f"\n-------------------------\n")

        output_file_name = f'issues/issue_{self.issue_number}_documentation.md'
        with open(output_file_name, 'w', encoding='utf-8') as f:
            f.write('\n'.join(document_content))

        global database
        database.add_documents([
            {"document": '\n'.join(document_content), "metadata": {"source": "github", "issue_number": self.issue_number}, "id": f"issue_{self.issue_number}"}
        ])

        return '\n'.join(document_content)

    # Method to search for issues on GitHub
    def search_issues(self, status='open', labels=None, assignee=None, title_contains=None):
        search_url = 'https://api.github.com/search/issues'
        headers = {'Authorization': f'token {self.github_token}'}
        query = f'repo:{self.repo_owner}/{self.repo_name} state:{status}'
        
        if labels:
            query += f' label:"{labels}"'
        if assignee:
            query += f' assignee:{assignee}'
        if title_contains:
            query += f' {title_contains} in:title'
        
        print(query)
        params = {'q': query}
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        #print(response.text)
        issues = response.json()['items']
        
        # Exclude specific fields
        fields_to_exclude = {'body', 'user', 'reactions'}
        fields_to_include = {'closed_at', 'created_at', 'updated_at', 'title', 'number','state','labels'}
        filtered_issues = [
            #{k: v for k, v in issue.items() if k not in fields_to_exclude}
            {k: v for k, v in issue.items() if k in fields_to_include}
            for issue in issues
        ]
        
        return filtered_issues

    # Method to get the latest successful workflow runs
    def get_latest_successful_workflow_runs(self, branch="release19"):
        runs_url = f'{self.base_url}/actions/runs'
        headers = {'Authorization': f'token {self.github_token}'}
        response = requests.get(runs_url, headers=headers)
        response.raise_for_status()
        runs = response.json()['workflow_runs']
        status = 'completed'
        workflows = ['Xamarin Android Signed app', 'Xamarin Windows Signed app']
        branches = [branch]
        #python parse date from string
        print(runs)
        valid_runs = [run for run in runs if run['status'] == status and run['name'] in workflows and run['head_branch'] in branches and datetime.strptime(run['created_at'], '%Y-%m-%dT%H:%M:%SZ') > datetime.now() - timedelta(days=1)]
        sorted_runs = sorted(valid_runs, key=lambda run: run['created_at'], reverse=True)
        for run in sorted_runs:
            #print(run)
            print(f"Run: {run['id']}, Status: {run['status']}, Conclusion: {run['conclusion']}, Name: {run['name']}, branch: {run['head_branch']}, display title: {run['display_title']} actor: {run['actor']['login']}, date: {run['created_at']}")

        # Find the latest successful workflow run
        #latest_successful_run = next((run for run in runs if run['conclusion'] == 'success'), None)
        #return latest_successful_run
        print(sorted_runs)
        return sorted_runs

    # Method to get the artifacts for a workflow run
    def get_artifacts_for_run(self, run_id):
        artifacts_url = f'{self.base_url}/actions/runs/{run_id}/artifacts'
        headers = {'Authorization': f'token {self.github_token}'}
        response = requests.get(artifacts_url, headers=headers)
        response.raise_for_status()
        artifacts = response.json()['artifacts']
        return artifacts

    # Method to document the artifacts for the latest successful workflow runs
    def document_artifacts(self):
        document_content = []
        # Now, get the latest successful workflow run
        latest_runs = self.get_latest_successful_workflow_runs()
        if latest_runs:
            for run in latest_runs:
                print(run)
                # Get the artifacts for the latest successful run
                artifacts = self.get_artifacts_for_run(run['id'])
                print(artifacts)

                # Add artifact download links to the document content
                document_content.append(f"## Artifacts for the latest successful build (Run ID: {run['id']})\n")
                for artifact in artifacts:
                    document_content.append(f"- [{artifact['name']}]({artifact['archive_download_url']})\n")
        else:
            document_content.append("No successful workflow runs found.\n")

        return '\n'.join(document_content)

    # Method to get the issues for a GitHub project
    def get_project_issues(self, project_number, org_name='' ):
        # Get the project ID using the project number
        projects_url = f'https://api.github.com/orgs/{org_name}/projects?per_page=100'
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.inertia-preview+json'
        }
        page=1
        while True:
            print(f"Getting page {page}")
            projects_response = requests.get(f"{projects_url}&page={page}"
                                             , headers=headers)
            projects_response.raise_for_status()
            projects = projects_response.json()
            if (len(projects) == 0):
                raise ValueError(f"No more projects found for org: {org_name}")
            
            for project in projects:
                print(f"Project: {project['name']}, number: {project['number']}")
            
            # Find the project with the given number
            #project = next((p for p in projects if str(p['number']) == str(project_number)), None)
            project = next((p for p in projects if str(p['number']) == str(project_number)), None)
            if not project:
                page = page + 1
                #raise ValueError(f"No project found with number: {project_number}")
            else:
                break
        

        # Now get the columns for the found project
        columns_url = project['columns_url']
        columns_response = requests.get(columns_url, headers=headers)
        columns_response.raise_for_status()
        columns = columns_response.json()

        issues_info = []
        for column in columns:
            cards_url = column['cards_url']
            cards_response = requests.get(cards_url, headers=headers)
            cards_response.raise_for_status()
            cards = cards_response.json()

            for card in cards:
                if 'content_url' in card and 'issue' in card['content_url']:
                    issue_response = requests.get(card['content_url'], headers=headers)
                    issue_response.raise_for_status()
                    issue = issue_response.json()
                    issues_info.append({
                        'id': issue['id'],
                        'url': issue['html_url'],
                        'status': column['name']
                    })

        return issues_info

    # Method to get the issues for a GitHub project using the GraphQL API
    def get_project_issues_graphql(self, project_number, org_name=None, user_name=None):
        graphql_url = 'https://api.github.com/graphql'
        headers = {
            'Authorization': f'Bearer {self.github_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/vnd.github.vixen-preview+json'
        }

        query = """
query("""+(
        "$orgName: String!" if org_name else "$userName: String!"
        )+""", $projectNumber: Int!) {
"""+ (
    """organization(login: $orgName)""" if org_name else """user(login: $userName)"""
    )+ """{
    projectV2(number: $projectNumber) {
        id
      	,title
      	,items(first: 100) {
      	  edges {
      	    node {
      	      id,
              createdAt,
              type,
            	fieldValues(first: 20)
              {
                nodes{
                ... on ProjectV2ItemFieldSingleSelectValue {
                field {
                  ... on ProjectV2SingleSelectField {
                    name
                  }
                }
                name
                id
              }
                }},
              content {
                    ... on Issue {
                      number,
                      title,
                      url,
                      state,
                      labels(first:10){
                        nodes{
                            name,
                            color
                        }
                      }
                    }
              }
      		}	
        }
    }
  }
}
}

        """

        variables = {
            'projectNumber': project_number
        }
        if org_name:
            variables['orgName'] = org_name
        else:
            variables['userName'] = user_name

        response = requests.post(
            graphql_url,
            headers=headers,
            json={'query': query, 'variables': variables}
        )
        response.raise_for_status()
        result = response.json()

        #make this a lambda function with validations for the cases where the data doesn't exist, so the index out of bound doesn't happen
        def get_product(node):
            if 'labels' in node['node']['content']:
                product_labels = [label['name'] for label in node['node']['content']['labels']['nodes'] if label['name'].startswith('Product:')]
                if product_labels and len(product_labels) > 0:
                    return product_labels[0].split(':')[1]
            return None

        #print(result)
        # Extract the issues from the result
        issues = [
            {
                'id': node['node']['id'],
                'number': node['node']['content']['number'],
                'title': node['node']['content']['title'],
                'url': node['node']['content']['url'],
                'issue_status': node['node']['content']['state'],
                'board_fields': node['node']['fieldValues']['nodes'],
                'labels': node['node']['content']['labels']['nodes'],
                'product': get_product(node),
                #'product': [label['name'] for label in node['node']['content']['labels']['nodes'] if label['name'].startswith('Product:')][0].split(':')[1],
                'board_status': [status['name'] for status in node['node']['fieldValues']['nodes'] if 'field' in status ][0]
            }
            for node in result['data']['organization' if org_name else 'user']['projectV2']['items']['edges'] if node['node']['type'] == 'ISSUE' # Ensure it's an Issue, not a PR or other content type
        ]

        #pprint(issues)
        print(f"Found {len(issues)} issues")
        return issues

    # Method to create a tag on a GitHub repository
    def create_tag(self, tag_name, commit_sha):
        existing_tag = self.retrive_tag(tag_name)
        if type(existing_tag) == list:
            existing_tag = sorted(existing_tag, key=lambda x : x['ref'])[-1]
        if existing_tag and existing_tag['object']['sha'] == commit_sha:
            print(f'Tag {tag_name} already exists, commit sha matches')
            return existing_tag
        elif existing_tag and existing_tag['object']['sha'] != commit_sha:
            print(f'Tag {tag_name} already exists, commit sha does not match')
            return existing_tag

        url = f'{self.base_url}/git/refs'
        data = {
            'ref': f'refs/tags/{tag_name}',
            'sha': commit_sha
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        print(f'Created tag {tag_name}')
        return response.json()

    # Method to retrieve a tag from a GitHub repository
    def retrive_tag(self, tag_name):
        url = f'{self.base_url}/git/refs/tags/{tag_name}'
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            print(f'Tag {tag_name} not found')
            return None
        tag_info = response.json()
        print(tag_info)
        return tag_info

    # Method to delete a tag from a GitHub repository
    def delete_tag(self, tag_name):
        url = f'{self.base_url}/git/refs/tags/{tag_name}'
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.status_code == 204

    # Method to retrieve a release from a GitHub repository
    def retrieve_release(self, tag_name):
        url = f'{self.base_url}/releases/tags/{tag_name}'
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            print(f'Release for tag {tag_name} not found')
            return None
        release_info = response.json()
        print(release_info)
        return release_info

    # Method to list all releases for a GitHub repository
    def list_all_releases(self, prerelease=True):
        url = f'{self.base_url}/releases'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        releases = response.json()
        sorted_releases = sorted(releases, key=lambda release: release['created_at'], reverse=True)
        filtered_releases = [release for release in sorted_releases if release['prerelease'] == prerelease]
        result = [{
            'tag_name': release['tag_name'],
            'name': release['name'],
            'prerelease': release['prerelease'],
            'draft': release['draft'],

        } for release in filtered_releases]
        return result

    # Method to create a release on a GitHub repository
    def create_release(self, tag_name, release_name, body):
        release_info = self.retrieve_release(tag_name)
        if release_info:
            print(f'Release for tag {tag_name} already exists')
            return release_info

        url = f'{self.base_url}/releases'
        data = {
            'tag_name': tag_name,
            'name': release_name,
            'body': body,
            'prerelease': True
        }
        response = requests.post(url, headers=self.headers, json=data)
        print(response.json())
        response.raise_for_status()
        return response.json()

    # Method to add release notes to a release on a GitHub repository
    def add_release_notes(self, release_id, body):
        url = f'{self.base_url}/releases/{release_id}'
        data = {'body': body}
        response = requests.patch(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    # Method to add a comment to an issue on a GitHub repository
    def add_comment_to_issue(self, issue_number, comment):
        url = f'{self.base_url}/issues/{issue_number}/comments'
        data = {'body': comment}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    # Method to get the last commit in a GitHub repository
    def get_last_commit(self):
        url = f'{self.base_url}/commits'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        commits = response.json()
        if commits:
            return commits[0]['sha']
        else:
            raise Exception("No commits found in the repository")

# Function to document a GitHub issue
def document_github_issue(issue_number, repo=None):
    load_dotenv()
    github_token = os.getenv('GITHUB_TOKEN')
    repo_owner = os.getenv('REPO_OWNER')
    repo_name = os.getenv('REPO_NAME') if not repo else repo
    documenter = IssueDocumenter(github_token, repo_owner, repo_name, issue_number)
    result = documenter.document_issue()
    #result = documenter.document_artifacts()
    #result = documenter.get_project_issues(issue_number)
    #result = documenter.get_project_issues_graphql(issue_number)
    return result

# Function to search for GitHub issues
def search_issues(status: str = 'open', product: str = None, repo_name: str = 'eng-product-release'):
    load_dotenv()
    github_token = os.getenv('GITHUB_TOKEN')
    repo_owner = os.getenv('REPO_OWNER')
    documenter = IssueDocumenter(github_token, repo_owner, repo_name)
    if product:
        result = documenter.search_issues(status=status, labels=f"Product:{product}")
    else:
        result = documenter.search_issues(status=status)
    print(f"Found {len(result)} issues with status {status} and product {product}")
    return result

# Function to list GitHub issues for a specific project
def list_github_issues(project_number: int, status=None, product=None):
    load_dotenv()
    github_token = os.getenv('GITHUB_TOKEN')
    is_org = os.getenv('IS_ORG') == 'true'
    if is_org:
        repo_owner = os.getenv('REPO_OWNER')
    else:
        repo_owner = os.getenv('REPO_OWNER')
    repo_name = os.getenv('REPO_NAME')
    documenter = IssueDocumenter(github_token, repo_owner, repo_name, project_number)
    #result = documenter.document_issue()
    #result = documenter.document_artifacts()
    #result = documenter.get_project_issues(issue_number)
    result = documenter.get_project_issues_graphql(project_number, repo_owner if is_org else None, repo_owner if not is_org else None)
    if status and status.lower() != 'all':
        result = [item for item in result if item['board_status'].lower() == status.lower()]
    if product and product.lower() != 'all' and product.lower() != 'maintenance':
        result = [item for item in result if item['product'].lower() == product.lower()]
    print(f"Found {len(result)} issues in status {status}")
    return result

# Function to create or update a release on GitHub
def create_or_update_release(product:str = None, build_tag:str = None, release_notes:str = None):
    #for tests
    #build_tag='v15.20.0.999'
    if not build_tag:
        raise Exception('No build tag provided')
    #if build_tag and not build_tag.startswith('v'):
    #    build_tag = f'v{build_tag}'

    gh_repo = {
        'maintenance': os.getenv('MAINTENANCE_REPO'),
    }
    if not product or product not in gh_repo:
        raise Exception(f'No repository found for product {product}')
    if not build_tag:
        raise Exception('No build tag provided')

    load_dotenv()
    github_token = os.getenv('GITHUB_TOKEN')
    repo_owner = os.getenv('REPO_OWNER')
    #repo_name = os.getenv('REPO_NAME')
    repo_name = gh_repo[product]
    git_wrapper = IssueDocumenter(github_token, repo_owner, repo_name)
    commit_sha = git_wrapper.get_last_commit()

    # Example usage of the GitWrapper functions
    tag = git_wrapper.create_tag(build_tag, commit_sha)
    release = git_wrapper.create_release(build_tag, '', '')
    
    if not release['prerelease']:
        return f'Release for tag {build_tag} is already published, cannot update release notes'
    
    if release and release['body'] and not release_notes:
        release_notes = release['body']
    updated_release = git_wrapper.add_release_notes(release['id'], release_notes or '[Write release notes here]')
    #comment = git_wrapper.add_comment_to_issue(1, 'This is a comment on issue #1')

# Function to add a comment to a GitHub issue
def add_comment_to_issue(issue_number:int, comment:str, repo_name:str = None):
    if not issue_number or not comment:
        raise Exception('Issue number and comment must be provided')

    load_dotenv()
    github_token = os.getenv('GITHUB_TOKEN')
    repo_owner = os.getenv('REPO_OWNER')
    if not repo_name:
        repo_name = os.getenv('MAINTENANCE_REPO')

    documenter = IssueDocumenter(github_token, repo_owner, repo_name, issue_number)
    issue_url = f'{documenter.base_url}/issues/{issue_number}/comments'
    headers = {'Authorization': f'token {github_token}'}
    data = {'body': comment}

    response = requests.post(issue_url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# Function to delete a tag from a GitHub repository
def delete_tag(tag_name:str, product:str = None):
    if not tag_name:
        raise Exception('No tag name provided')
    gh_repo = {
        'maintenance': 'maintenance',
    }
    if not product or product not in gh_repo:
        raise Exception(f'No repository found for product {product}')

    # Example usage of the GitWrapper functions
    load_dotenv
    github_token = os.getenv('GITHUB_TOKEN')
    repo_owner = os.getenv('REPO_OWNER')
    #repo_name = os.getenv('REPO_NAME')
    repo_name = gh_repo[product]
    git_wrapper = IssueDocumenter(github_token, repo_owner, repo_name)
    git_wrapper.delete_tag(tag_name)

# Function to list all releases for a product
def list_all_releases(product:str = None):
    github_token = os.getenv('GITHUB_TOKEN')
    repo_owner = os.getenv('REPO_OWNER')
    repo_name = os.getenv('MAINTENANCE_REPO')
    git_wrapper = IssueDocumenter(github_token, repo_owner, repo_name)
    releases = git_wrapper.list_all_releases()
    return releases

# Function to get similar issues from the vector database
def get_similar_issues(issue_number:int, repo_name:str = None):
    if not issue_number:
        raise Exception('Issue number must be provided')

    load_dotenv()
    github_token = os.getenv('GITHUB_TOKEN')
    repo_owner = os.getenv('REPO_OWNER')
    if not repo_name:
        repo_name = os.getenv('MAINTENANCE_REPO')

    documenter = IssueDocumenter(github_token, repo_owner, repo_name, issue_number)
    return documenter.get_similar_issues()

# Function to update the status of a GitHub issue
def update_issue_status(issue_number:int, status:str):
    load_dotenv()
    github_token = os.getenv('GITHUB_TOKEN')
    repo_owner = os.getenv('REPO_OWNER')
    repo_name = os.getenv('MAINTENANCE_REPO')
    project_number = 1
    documenter = IssueDocumenter(github_token, repo_owner, repo_name, issue_number)
    documenter.update_issue_status(issue_number, status, project_number, None, repo_owner)

# Usage as a library
if __name__ == '__main__':
    issue_number = 2
    project_id=1
    product = 'maintenance'
    update_issue_status(issue_number, 'Done')

