#!/usr/bin/env python3
"""
repo_miner.py

A command-line tool to:
  1) Fetch and normalize commit data from GitHub

Sub-commands:
  - fetch-commits
"""

import os
import argparse
import pandas as pd
from github import Github
from github import Auth

def fetch_commits(repo_name: str, max_commits: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_commits` from the specified GitHub repository.
    Returns a DataFrame with columns: sha, author, email, date, message.
    """
    # 1) Read GitHub token from environment
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise EnvironmentError("GITHUB_TOKEN not found in environment variables")

    # 2) Initialize GitHub client and get the repo
    auth = Auth.Token(github_token)
    git = Github(auth=auth)
    repo = git.get_repo(repo_name)

    # 3) Fetch commit objects (paginated by PyGitHub)
    commits = repo.get_commits()

    # 4) Normalize each commit into a record dict
    records = []
    count = 0
    for commit in commits:
        sha = commit.sha
        commit_data = commit.commit  # git.Commit object
        author_name = commit_data.author.name if commit_data.author else None
        author_email = commit_data.author.email if commit_data.author else None
        date = commit_data.author.date.isoformat() if commit_data.author and commit_data.author.date else None
        message = commit_data.message.split("\n", 1)[0] if commit_data.message else ""

        records.append({
            "sha" : sha,
            "author_name" : author_name,
            "author_email" : author_email,
            "date" : date,
            "message" : message
        })

        count += 1
        if max_commits is not None and count >= max_commits:
            break

    # 5) Build DataFrame from records
    df = pd.DataFrame.from_records(records, columns=["sha", "author", "email", "date", "message"])
    return df
    
def fetch_issues(repo_name: str, state: str = "all", max_issues: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_issues` issues (not PRs) from the specified GitHub repository.
    Returns a DataFrame with columns:
      id, number, title, user, state, created_at, closed_at, comments, open_duration_days
    """
    # 1) Read GitHub token from environment
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise EnvironmentError("GITHUB_TOKEN not found in environment variables")

    # 2) Initialize GitHub client and get the repo
    auth = Auth.Token(github_token)
    git = Github(auth=auth)
    repo = git.get_repo(repo_name)

    # 3) Fetch issues, filtered by state ('all', 'open', 'closed')
    issues = repo.get_issues(state=state)

    # 4) Normalize each issue (skip PRs)
    records = []
    count = 0
    for issue in issues:
        # Skip pull requests
        if issue.pull_request is not None:
            continue

        created_at = issue.created_at.isoformat() if issue.created_at else None
        closed_at = issue.closed_at.isoformat() if issue.closed_at else None
        open_duration_days = None
        if issue.closed_at and issue.created_at:
            delta = issue.closed_at - issue.created_at
            open_duration_days = delta.days

        records.append({
            "id": issue.id,
            "number": issue.number,
            "title": issue.title,
            "user": issue.user.login if issue.user else None,
            "state": issue.state,
            "created_at": created_at,
            "closed_at": closed_at,
            "comments": issue.comments,
            "open_duration_days": open_duration_days
        })

        count += 1
        if max_issues is not None and count >= max_issues:
            break

    # 5) Build DataFrame
    df = pd.DataFrame.from_records(
        records,
        columns=[
            "id", "number", "title", "user",
            "state", "created_at", "closed_at",
            "comments", "open_duration_days"
        ]
    )
    return df


def main():
    """
    Parse command-line arguments and dispatch to sub-commands.
    """
    parser = argparse.ArgumentParser(
        prog="repo_miner",
        description="Fetch GitHub commits/issues and summarize them"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command: fetch-commits
    c1 = subparsers.add_parser("fetch-commits", help="Fetch commits and save to CSV")
    c1.add_argument("--repo", required=True, help="Repository in owner/repo format")
    c1.add_argument("--max",  type=int, dest="max_commits",
                    help="Max number of commits to fetch")
    c1.add_argument("--out",  required=True, help="Path to output commits CSV")

    # Sub-command: fetch-issues
    c2 = subparsers.add_parser("fetch-issues", help="Fetch issues and save to CSV")
    c2.add_argument("--repo",  required=True, help="Repository in owner/repo format")
    c2.add_argument("--state", choices=["all","open","closed"], default="all",
                    help="Filter issues by state")
    c2.add_argument("--max",   type=int, dest="max_issues",
                    help="Max number of issues to fetch")
    c2.add_argument("--out",   required=True, help="Path to output issues CSV")

    args = parser.parse_args()

    # Dispatch based on selected command
    if args.command == "fetch-commits":
        df = fetch_commits(args.repo, args.max_commits)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} commits to {args.out}")

    elif args.command == "fetch-issues":
        df = fetch_issues(args.repo, args.state, args.max_issues)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} issues to {args.out}")

if __name__ == "__main__":
    main()
