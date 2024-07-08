There's a series of tasks I do on a regular basis, and I will need your help with, for instance:

List GitHub Issues for a specific project:
- Get the list of all github issues that are in a project.

Prepare a brief on the GitHub Issues for a specific project:
- Get the list of all github issues that are in the project
- retrieve the information of each one
- make a small brief

Prepare a release table
- Retrieve the list of issues for a specified project, use the list_github_issues_tool 
- with the information of the issues we will include in the next release
- filter only the issues that are in state Pending release
- use this list of GH issues to generate the table

Prepare the release notes
- You will need to know which product: maintenance
- You will need to know version we are building
- You will need to know which work item is assigned for this release
- You will enumerate the issues for that product checking the corresponding GitHub project
- For a release get only the issues in the pending release state
- Generate the release notes for this version

Prepare the release for [Product]
- identify if there's an active release for [Product], use the most recent, the one with the bigger number
- then list the issues with status pending release for [Product]
- create the release notes
- create or update the release in GitHub using the new notes


My main project is Sample Project, the id is 1, here we have track the current issues