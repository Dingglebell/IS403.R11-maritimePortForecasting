# Beginner Git Bash guide

Use **Git Bash** on Windows. Bash commands move around files; Git records changes; GitHub hosts the shared repository. A branch is your separate line of work, a commit is a saved change, and a pull request asks the team to review it.

Repository: https://github.com/Dingglebell/is403-maritime-port-forecasting

## First use

Install Git from its official site if needed and open Git Bash. The repository owner adds teammates as collaborators; each teammate accepts the invitation. A public repository can be read by anyone, but pushing requires access. Complete GitHub’s browser sign-in if Git prompts; do not paste passwords or tokens into commits or chat.

Type commands without any leading `$`. Replace example identity values with your own. Use your GitHub-provided no-reply email if you prefer not to publish your personal email in commit metadata.

```bash
git --version
git clone https://github.com/Dingglebell/is403-maritime-port-forecasting.git
cd is403-maritime-port-forecasting
git config user.name "Your Name"
git config user.email "YOUR_GITHUB_NOREPLY_EMAIL"
git status
```

These identity settings apply only to this repository. If you are using the already prepared `Project` checkout, open Git Bash in that folder and skip `git clone` and `cd`.

## Basic Bash commands

| Command | Meaning |
|---|---|
| `pwd` | Show the current folder |
| `ls` or `ls -a` | List files; `-a` includes hidden files |
| `cd docs` | Enter docs |
| `cd ..` | Go up one folder |
| `cat README.md` | Read a text file |
| `mkdir practice` | Create a folder, if needed |
| `cp README.md practice/readme-copy.md` | Copy a file |
| `mv practice/readme-copy.md practice/notes.md` | Rename or move a file |

Use quotation marks around paths containing spaces, for example `cat "docs/Task 1_Han.md"`. Git Bash uses `/`, not Windows backslashes. Press Tab to complete filenames and the up arrow to recall commands. The example `practice` files are local exercises; do not commit them by accident.

## Daily workflow

First save your current work and check `git status`. Start a new task from an up-to-date main branch:

```bash
git switch main
git pull --ff-only origin main
git switch -c task1-han-data-audit
```

Choose your own short branch name, such as `task2-dinh-features` or `task3-tien-hgb`. For an existing branch use `git switch BRANCH_NAME`; do not use `-c` again. Paired owners can use separate branches and review each other’s pull requests.

Edit files in your normal editor. For example, after editing your task brief:

```bash
git status
git diff
git add "docs/Task 1_Han.md"
git diff --staged
git commit -m "Clarify the zero cargo audit"
git push -u origin task1-han-data-audit
```

`add` selects files for the commit, `commit` saves locally, and `push` uploads the branch. Replace the example filename and branch with your own. Later pushes on the same branch can use `git push`. Prefer specific paths to `git add .` so you can see exactly what will be shared.

On GitHub, open **Compare & pull request**, choose base `main`, describe what changed and what you checked, and ask one teammate to review. After review, merge the pull request. Then, with a clean working tree:

```bash
git switch main
git pull --ff-only origin main
git log --oneline -5
```

Before another change, create a new branch from this updated main. Do not reuse a merged branch.

## Common problems

- **Wrong file staged:** `git restore --staged "path/to/file"` removes it from the next commit while keeping the edited file.
- **Nothing to commit:** save the file in your editor, run `git status`, then add the intended file.
- **Local edits block switching:** commit those edits on the correct branch before switching. Do not force the switch.
- **Push rejected:** do not force-push. Run `git fetch origin`, then `git merge origin/YOUR_BRANCH` on that branch and resolve any conflicts before pushing. If only main advanced, merge `origin/main` into your feature branch instead.
- **Merge conflict:** run `git status`. For text files, edit the conflict markers with the other author, retain the correct content, then `git add "file"` and `git commit`. For PDF/DOCX/PPTX, agree on the correct version or regenerate it; Git cannot combine their contents meaningfully. To cancel an in-progress merge, use `git merge --abort`.
- **File is ignored:** raw data and large results are intentionally local. For an approved small results table only, use `git add -f results/metrics.csv` after reviewing its contents.

Keep code and editable Markdown in Git. When updating a task PDF, update its Markdown counterpart and regenerate or re-export the PDF with Times New Roman 13, black text and gray table headers. Do not use `git reset --hard`, `git clean -fd` or force-push as beginner troubleshooting shortcuts.

## Official help

[Git branch switching](https://git-scm.com/docs/git-switch) and [GitHub repository basics](https://docs.github.com/en/get-started/start-your-journey/creating-a-repository-for-your-project-on-github).
