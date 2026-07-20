import re
from datetime import datetime
from typing import List, Dict, Any
from app.schemas import CommitAnalysis, PoorCommitMessage, CommitTimelinePoint, Deduction

class CommitAnalyzer:
    GENERIC_WORDS = {"fix", "update", "changes", "misc", "wip", "temp", "test", "commit", "working", "done", "refactor"}

    @classmethod
    def is_generic_message(cls, message: str) -> bool:
        """Determines if a commit message is generic or low quality."""
        msg_clean = message.strip().lower()
        if not msg_clean:
            return True
        
        # Strip common symbols and issue references
        msg_clean = re.sub(r"#[0-9]+", "", msg_clean).strip()
        # Remove commit prefixes like "chore:", "feat:", "fix:" etc.
        msg_clean = re.sub(r"^[a-z]+(\([a-z0-9_-]+\))?!?:", "", msg_clean).strip()
        
        # Check if length is too short (excluding formatting prefixes)
        if len(msg_clean) < 4:
            return True
            
        # Check if the message matches generic terms
        if msg_clean in cls.GENERIC_WORDS:
            return True
            
        # Check if it consists solely of generic words (e.g., "fix changes", "update wip")
        words = set(re.findall(r"\b[a-z]+\b", msg_clean))
        if words and words.issubset(cls.GENERIC_WORDS):
            return True
            
        return False

    @classmethod
    def analyze(cls, commits: List[Dict[str, Any]]) -> CommitAnalysis:
        """
        Analyze commit logs, build timeline, calculate quality score.
        Weight: 20% of overall score.
        """
        deductions: List[Deduction] = []
        
        if not commits:
            deductions.append(Deduction(
                category="Commit Quality",
                points=100,
                explanation="No commit history was found or could be fetched. Commit history is critical for tracking changes, reviews, and versioning.",
                file_involved=None
            ))
            return CommitAnalysis(
                score=0,
                total_commits=0,
                avg_commits_per_week=0.0,
                contributors_count=0,
                poor_messages_percentage=0.0,
                poor_messages=[],
                timeline=[],
                deductions=deductions
            )

        total_commits = len(commits)
        poor_messages: List[PoorCommitMessage] = []
        contributors = set()
        
        # Extract timeline and compile metrics
        timeline_counts: Dict[str, int] = {}
        commit_dates: List[datetime] = []
        total_message_len = 0

        for commit_item in commits:
            commit_hash = commit_item.get("sha", "")[:7]
            commit_data = commit_item.get("commit", {})
            message = commit_data.get("message", "")
            first_line = message.split("\n")[0].strip()
            total_message_len += len(first_line)

            # Author info
            author_data = commit_data.get("author", {})
            author_name = author_data.get("name", "Unknown")
            author_email = author_data.get("email", "")
            date_str = author_data.get("date", "")
            
            if author_email:
                contributors.add(author_email)
            else:
                contributors.add(author_name)

            # Parse commit date
            # GitHub returns ISO dates: "2026-07-04T13:12:00Z"
            try:
                date_parsed = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                commit_dates.append(date_parsed)
                date_key = date_parsed.strftime("%Y-%m-%d")
                timeline_counts[date_key] = timeline_counts.get(date_key, 0) + 1
            except ValueError:
                pass

            # Check message quality
            if cls.is_generic_message(first_line):
                poor_messages.append(PoorCommitMessage(
                    hash=commit_hash,
                    message=first_line,
                    author=author_name,
                    date=date_str
                ))

        poor_messages_percentage = round((len(poor_messages) / total_commits) * 100, 1)
        contributors_count = len(contributors)
        
        # Calculate activity frequency (average commits/week)
        if commit_dates:
            oldest = min(commit_dates)
            newest = max(commit_dates)
            days_span = max(1, (newest - oldest).days)
            weeks_span = max(1.0, days_span / 7.0)
            avg_commits_per_week = round(total_commits / weeks_span, 1)
        else:
            avg_commits_per_week = 0.0

        # Calculate base score starting at 100
        score = 100
        
        # Deduct for poor commit messages
        if poor_messages_percentage > 5:
            # Deduct 0.6 points for every percentage point of poor messages, up to 40 points
            msg_deduction = min(40, int(poor_messages_percentage * 0.6))
            score -= msg_deduction
            deductions.append(Deduction(
                category="Commit Quality",
                points=msg_deduction,
                explanation=f"{poor_messages_percentage}% of analyzed commit messages were flagged as generic or descriptive-lacking (e.g. 'fix', 'wip', 'changes'). Use semantic commit messages (e.g. 'feat: add auth login') to improve traceability.",
                file_involved=None
            ))

        # Deduct for short average commit message length
        avg_len = total_message_len / total_commits
        if avg_len < 15:
            score -= 15
            deductions.append(Deduction(
                category="Commit Quality",
                points=15,
                explanation=f"The average commit message length is very short ({round(avg_len, 1)} characters). Commit messages should briefly summarize what changed and why.",
                file_involved=None
            ))

        # Deduct for single contributor (minor warning)
        if contributors_count == 1:
            score -= 5
            deductions.append(Deduction(
                category="Commit Quality",
                points=5,
                explanation="Only 1 unique contributor detected in recent history. A single-contributor project has high Bus Factor and lower collaborative overhead checks.",
                file_involved=None
            ))

        # Build sorted timeline list
        sorted_timeline = [
            CommitTimelinePoint(date=k, count=v)
            for k, v in sorted(timeline_counts.items())
        ]

        return CommitAnalysis(
            score=max(0, score),
            total_commits=total_commits,
            avg_commits_per_week=avg_commits_per_week,
            contributors_count=contributors_count,
            poor_messages_percentage=poor_messages_percentage,
            poor_messages=poor_messages[:15], # Limit list size for API payload
            timeline=sorted_timeline[:30], # Limit timeline to recent 30 active days
            deductions=deductions
        )
