from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from github import Github
from github.GithubException import GithubException

from app.config import settings


def fetch_github_activity(incident: Dict[str, Any]) -> Dict[str, Any]:
    token = settings.github_token
    repo_name = settings.github_repo
    since = datetime.utcnow() - timedelta(hours=6)

    if not token or not repo_name:
        return {
            "commits": [],
            "prs": [],
            "deployments": [],
            "evidence": ["GitHub is not configured; skipping repo analysis."],
            "repo": repo_name,
            "since": since.isoformat()
        }

    commits = []
    prs = []
    deployments = []
    evidence: List[str] = []

    try:
        gh = Github(token)
        repo = gh.get_repo(repo_name)

        for commit in repo.get_commits(since=since)[:5]:
            commits.append(commit.commit.message)

        for pr in repo.get_pulls(state="closed", sort="updated", direction="desc")[:5]:
            if pr.merged_at and pr.merged_at >= since:
                prs.append(pr.title)

        for deployment in repo.get_deployments()[:5]:
            deployments.append(str(deployment.id))

    except GithubException as exc:
        evidence.append(f"GitHub API error: {exc}")
    except Exception as exc:
        evidence.append(f"GitHub connector error: {exc}")

    if commits:
        evidence.append(f"Recent commits found: {len(commits)}")
    if prs:
        evidence.append(f"Recent merged PRs: {len(prs)}")
    if deployments:
        evidence.append(f"Recent deployments: {len(deployments)}")

    if not evidence:
        evidence.append("GitHub activity looked normal for the recent incident window.")

    return {
        "commits": commits,
        "prs": prs,
        "deployments": deployments,
        "evidence": evidence,
        "repo": repo_name,
        "since": since.isoformat()
    }
