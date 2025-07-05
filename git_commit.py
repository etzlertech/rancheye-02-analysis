#!/usr/bin/env python3
import subprocess
import os

os.chdir('/Users/travisetzler/Documents/GitHub/rancheye-02-analysis')

# Git add
subprocess.run(['git', 'add', '-A'], check=True)

# Git commit
commit_message = """Change RanchEye logo eye icon to olive green

- Updated eye icon color from green-600 to #6b7c3a (olive green)
- Matches the Analyze button color for consistent branding
- Applied to both React Header component and old HTML file

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

subprocess.run(['git', 'commit', '-m', commit_message], check=True)

# Git push
subprocess.run(['git', 'push'], check=True)

print("Successfully committed and pushed!")