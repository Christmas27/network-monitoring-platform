# Git and CI/CD Learning Notes
# 1. Big Picture First
Git:

Git tracks changes to your code over time.
A repository is your project with full change history.
Commits are snapshots with messages.
Branches let you work on features safely.
Remote origin is your GitHub copy.
CI/CD:

CI means Continuous Integration.
Every push or pull request triggers automatic checks like tests or linting.
CD means Continuous Delivery or Deployment.
After CI passes, code can be auto-deployed or prepared for release.
Mental model:

You write code locally.
You commit locally with Git.
You push to GitHub.
GitHub Actions runs CI.
If CI passes, PR can be merged.
Optional: deployment happens automatically after merge.

# 2. Daily Git Workflow With Commands and Meaning
Check status
Command:
git status
What it does:
Shows changed files, staged files, current branch, and what to do next.

See branch and tracking info
Command:
git branch -vv
What it does:
Shows your current branch and which remote branch it tracks.

Get latest remote updates
Command:
git fetch origin
What it does:
Downloads latest changes from GitHub without modifying your working files.

Update your branch safely
Command:
git pull --rebase origin master
What it does:
Brings latest master into your local branch and replays your local commits on top for cleaner history.

Create a new branch for your work
Command:
git checkout -b feat/acl-ui
What it does:
Creates and switches to a new branch so you do not commit directly to master.

Stage changes
Command:
git add -A
What it does:
Adds all tracked and untracked file changes into the staging area.

Commit staged changes
Command:
git commit -m "Add ACL apply/remove API and playbook integration"
What it does:
Creates a snapshot with a message that explains the change.

Push branch to GitHub
Command:
git push -u origin feat/acl-ui
What it does:
Uploads your branch to GitHub and sets upstream so future push can be just git push.

Open pull request
Command:
No terminal command. Open GitHub and create PR from feat/acl-ui into master.
What it does:
Starts review and triggers CI checks.

# 3. Useful Inspection Commands
See commit history in one line format
Command:
git log --oneline --graph --decorate -20
What it does:
Shows recent commits and branch graph clearly.

See exact file differences
Command:
git diff
What it does:
Shows unstaged code changes line by line.

See staged diff before commit
Command:
git diff --staged
What it does:
Shows exactly what will be committed.

See remote URL
Command:
git remote -v
What it does:
Confirms which GitHub repository you are pushing to.

# 4. Safe Undo Commands
Unstage a file but keep its content
Command:
git restore --staged main.py
What it does:
Removes file from staging area only.

Discard local edits in a file
Command:
git restore main.py
What it does:
Reverts file to last committed state. Use carefully.

Fix last commit message only
Command:
git commit --amend -m "Better commit message"
What it does:
Changes most recent commit message before pushing.

# 5. CI/CD in Your Current Project Context
What likely happens:

You push code to GitHub.
A workflow file in .github/workflows runs checks.
If checks pass, PR shows green.
After merge, optional deployment job runs.
Core idea:

CI protects code quality.
CD automates delivery.
Git is the transport layer for CI/CD triggers.
Key trigger event:

git push
This is usually what starts CI.

# 6. Practical Rules to Follow
Always start with git status.
Prefer feature branches over direct master commits.
Pull with rebase before pushing.
Commit small, clear units of change.
Write commit messages that explain why, not only what.
Do not commit secrets, tokens, or passwords.
Wait for CI green before merging.

# 7. Quick Session Template You Can Reuse
Command sequence:
git status
git fetch origin
git pull --rebase origin master
git checkout -b feat/your-change
git add -A
git commit -m "Describe your change"
git push -u origin feat/your-change

Then:

Open PR on GitHub
Wait for CI checks
Merge when green



# Practice 1: Safe Git Flow On This Project

# Check where you are and what changed
What this is for:

git status: shows modified/staged/untracked files
git branch -vv: shows current branch + upstream tracking
git remote -v: confirms your GitHub repo URL

# Sync with remote first
What this is for:

fetch: download remote updates safely
pull --rebase: replay your local commits on top of latest master to keep history clean

# Create a practice branch
What this is for:

New isolated branch so you can practice without touching master

# Make one tiny visible change for practice
What this is for:

Creates a real file change to commit

# Stage and inspect exactly what will be committed
What this is for:

git add: put file in staging area
git diff --staged: preview commit content before committing

# Commit
What this is for:

Saves a snapshot in history with a clear message

# Push branch
What this is for:

Upload branch to GitHub and set upstream for easy next push

# Practice 2: Add Basic CI (GitHub Actions) To This Project

# Create workflow folder and file
What this is for:

Creates a CI pipeline that runs on push/PR
Installs dependencies and runs a simple Python syntax check

# Commit CI workflow
What this is for:

Publishes CI config to GitHub and triggers first run

# Verify CI result
What this is for:

Confirms your CI is running and green/red status is visible

# Practice 3: Open PR Like Real Team Workflow

Create PR from practice/git-cicd-lab into master
Wait for CI checks
Merge only when green
Why this matters:

This is the real CI gate used in production teams

# Useful Recovery Commands During Practice

Unstage a file:

Discard local edits in one file:

See commit graph:

git log --oneline --graph --decorate -20

# tetsing

