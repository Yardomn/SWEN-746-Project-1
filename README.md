# SWEN-746-Project-1
A small data‐collection pipeline that pulls commit and issue data from GitHub, normalizes it, and emits clean CSVs for downstream modeling.
  # fetch_commits
    Fetch up to `max_commits` from the specified GitHub repository.
    Returns a DataFrame with columns: sha, author, email, date, message.
  # fetch_issues
    Fetch up to `max_issues` issues (not PRs) from the specified GitHub repository.
    Returns a DataFrame with columns:
      id, number, title, user, state, created_at, closed_at, comments, open_duration_days
  # merge_and_summarize
    Takes two DataFrames (commits and issues) and prints:
      - Top 5 committers by commit count
      - Issue close rate (closed/total)
      - Average open duration for closed issues (in days)

    Returns a summary dictionary with the same information.
