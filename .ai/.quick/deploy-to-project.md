# Deploy .ai (Agent OS) Into a Target Project

## Files only — clean file copy (recommended for most cases)

```text
@deploy-files copy - /absolute/path/to/my-project
# Creates /absolute/path/to/my-project/.ai/ (excludes .git, .github, .gitignore, .cursorrules)
```

If the path already includes `.ai`:

```text
@deploy-files copy - /absolute/path/to/my-project/.ai
```

## Full repo — with .git and .github

### Clone (full git mirror — requires origin remote)

```text
@deploy-repo clone - /absolute/path/to/destination
# Full git clone preserving history, branches, tags
```

### Archive (snapshot — no remote needed, includes .github/ and .cursorrules)

```text
@deploy-repo archive - /absolute/path/to/destination
# git archive extract — everything except .git directory
```

## Check deploy status

```text
@deploy-files status
@deploy-repo status
```

## Next steps in the target project

```text
@project-bootstrap init
@session-control start
```

## Examples

```text
@deploy-files copy - /home/user/work/ecommerce-platform
@deploy-files copy - /home/user/work/ecommerce-platform/.ai
@deploy-repo clone - /home/user/work/mirror
@deploy-repo archive - /home/user/work/internal-admin
```
