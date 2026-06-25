# Session Lifecycle — Start, Check, Close

## Start a session

```text
@session-control start
@session-control start - implement user export feature
```

## Check session state

```text
@session-control status
```

## Close a session (default: no git)

```text
@session-control close
```

## Close and commit changes

```text
@session-control close commit
@session-control close commit push
@session-control close commit scoped
```

## Mid-session checkpoint (commit without closing)

```text
@session-control commit
@session-control commit push
```
