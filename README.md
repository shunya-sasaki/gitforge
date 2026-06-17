# Git Forge

![Git](https://img.shields.io/badge/Git-F05032?logo=git&labelColor=gray&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?logo=github&labelColor=gray&logoColor=white)
![Gitea](https://img.shields.io/badge/Gitea-609926?logo=gitea&labelColor=gray&logoColor=white)

A unified CLI wrapper for git forges such as GitHub and Gitea.

## 📦 Requirements

This program is a wapper of `gh` and `tea` that are CLI tools for Git forges.

- git
- gh (If you use GitHub)
- tea (If you use Gitea)

## ⚙️ Setup

```sh
uv tool install git+https://github.com/shunya-sasaki/gitforge
```

## 🚀 Usage

`gitforge` auto-detects whether the current repository is hosted on
GitHub or Gitea (from its `origin` remote) and forwards each command to
the matching CLI (`gh` or `tea`). The same commands work on both forges.

Run without arguments to see all available commands:

```sh
gf --help
```

### Pull requests

```sh
gf pr list                              # list pull requests
gf pr create --title "Title" --body "Body"   # create a pull request
gf pr create --title "Title" --body "Body" --base dev --label bug
gf pr view 12                           # view PR #12
gf pr merge 12                          # merge PR #12
gf pr template                          # print the PR template
```

### Issues

```sh
gf issue list                           # list issues
gf issue create --title "Title" --body "Body"   # create an issue
gf issue create --title "Title" --body "Body" --label bug
gf issue view 7                         # view issue #7
gf issue template --label bug           # print an issue template
```

### Labels & worktrees

```sh
gf label list                           # list labels
gf worktree --help                      # manage git worktrees
```

## 📚 Reference

The upstream CLI tools that `gitforge` wraps:

- [cli/cli](https://github.com/cli/cli) — `gh`, the official GitHub CLI
- [gitea/tea](https://gitea.com/gitea/tea) — `tea`, the official Gitea CLI

## 📄 License

MIT License

See [LICENSE](./LICENSE) for the detail
