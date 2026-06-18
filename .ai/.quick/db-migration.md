# Database Migrations — Init, Create, Run, Verify

## Bootstrap the migration system (first time)

```text
@db-migration init
```

## Create a new migration script

```text
@db-migration create - add users table
@db-migration create - add email verified column
```

## Add a column (quick shorthand)

```text
@db-migration add column role to users
```

## Run pending migrations

```text
@db-migration run
```

## Check migration status

```text
@db-migration status
```

## Verify idempotency (safe re-run)

```text
@db-migration verify
```
