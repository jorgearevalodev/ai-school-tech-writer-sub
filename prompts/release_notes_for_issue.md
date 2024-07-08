Write a Customer-facing release note of the bug described in {issue_url}

It must have the following sections:
 - Title: a short title that sums up what was broken and is now fixed.
 - Description: a short summary of the fix
 - Background: what was the bug
 - Resolution: how we fixed it
 - Impact: what's the system impact and who should update their system because of this release
 - Reference: with a link to the bug's GitHub link, in the format: Reference: [GitHub Issue #XYZ](https://github.com/my-organization/eng-maintenance/issues/XYZ), replacing XYZ with the issue number.

Each section must have a simple header with NO markup: just the section name followed by colon and enter. 

DO NOT REFERENCE any internal ticket code like Jira IDs (usually uppercase letters followed by dash and numbers - For example, DO NOT INCLUDE maint-564 in the response), or GitHub IDs - the only GitHub ID allowed is in the Reference section.

{issue_content}