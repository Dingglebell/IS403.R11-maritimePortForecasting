# Git Bash guide

## 1 Get the repository into your current folder

Open Git Bash in an empty folder, then run:

```bash
git clone https://github.com/Dingglebell/is403-maritime-port-forecasting.git .
```

The final dot means “use this folder.” Run this only once. If you already have the repository, skip this step.

## 2 Start your work

Inside the repository, start a new branch from main:

```bash
git switch main
git pull --ff-only origin main
git switch -c task1-han
```

Replace `task1-han` with your own new branch name. Then edit and save your files.

## 3 Commit and push your work

```bash
git add -A
git status
git commit -m "Update the data preparation task"
git push -u origin task1-han
```

Replace the message and branch with yours. `git add -A` stages all new, modified and deleted files across the repository, except ignored files. Check `git status` before committing. A commit saves locally; push uploads to GitHub.

## 4 Create a pull request

Open [the repository on GitHub](https://github.com/Dingglebell/is403-maritime-port-forecasting). Click **Compare & pull request**, set the base to `main` and compare to your branch, add a title and short description, then click **Create pull request**. If the banner is absent, use **Pull requests → New pull request**. Ask a teammate to review before merging.

After the pull request is merged, with your work committed:

```bash
git switch main
git pull --ff-only origin main
```

Start the next task on a new branch.

## 5 Save all changes directly to main

If you are already on `main` and want to publish without a pull request:

```bash
git add -A
git status
git commit -m "Update project files and rename manifest"
git push origin main
```

For the rename from `data/manifest.example.csv` to `data/example.csv`, first replace `!data/manifest.example.csv` with `!data/example.csv` in `.gitignore`. Otherwise, the new filename stays ignored. Then run the commands above; they include the rename and the `.gitignore` change.

