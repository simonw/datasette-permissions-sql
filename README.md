# datasette-permissions-sql

[![PyPI](https://img.shields.io/pypi/v/datasette-permissions-sql.svg)](https://pypi.org/project/datasette-permissions-sql/)
[![CircleCI](https://circleci.com/gh/simonw/datasette-permissions-sql.svg?style=svg)](https://circleci.com/gh/simonw/datasette-permissions-sql)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/datasette-permissions-sql/blob/master/LICENSE)

Datasette plugin for configuring permission checks using SQL queries

**This only works with the next, unreleased version of Datasette**

## Installation

Install this plugin in the same environment as Datasette.

    $ pip install datasette-permissions-sql

## Usage

First, read up on how Datasette's [authentication and permissions system](https://datasette.readthedocs.io/en/latest/authentication.html) works.

This plugin lets you define SQL queries that are executed to see if the currently authenticated actor has permission to perform certain actions.

Consider a canned query which authenticated users should only be able to execute if a row in the `users` table says that they are a member of staff.

That `users` table in the `mydatabase.db` database could look like this:

| id | username | is_staff |
|--|--------|--------|
| 1 | cleopaws | 0 |
| 2 | simon | 1 |

Authenticated users have an `actor` that looks like this:

```json
{
    "id": 2,
    "username": "simon"
}
```

To configure the canned query to only be executable by staff users, add the following to your `metadata.json`:

```json
{
    "plugins": {
        "datasette-permissions-sql": [
            {
                "action": "view-query",
                "resource": ["mydatabase", "promote_to_staff"],
                "sql": "SELECT * FROM users WHERE is_staff = 1 AND id = :actor_id"
            }
        ]
    },
    "databases": {
        "mydatabase": {
            "queries": {
                "promote_to_staff": {
                    "sql": "UPDATE users SET is is_staff=1 WHERE id=:id",
                    "write": true
                }
            }
        }
    }
}
```

The `"datasette-permissions-sql"` key is a list of SQL matching rules. Each of those rules has the following shape:

```json
{
    "action": "name-of-action",
    "resource": ["resource identifier to run this on"],
    "sql": "SQL query to execute",
    "database": "mydatabas"
}
```

Both `"action"` and `"resource"` are optional. If present, the SQL query will only be executed on permission checks that match the action and, if present, the resource indicators.

`"database"` is also optional: it specifies the named database that the query should be executed against. If it is not present the first connected database will be used.

The Datasette documentation includes a [list of built-in permissions](https://datasette.readthedocs.io/en/stable/authentication.html#built-in-permissions) that you might want to use here.

### The SQL query

If the SQL query returns any rows the permission will be allowed. If it returns no rows, the plugin hook will return `None` which means other plugins can have a go at checking permissions.

If the SQL query returns a single value of `-1` it well be treated as an explicit "deny permission" response to the permission check.

The SQL query is called with a number of named parameters. You can use any of these as part of the query.

The list of parameters is as follows:

* `action` - the action, e.g. `"view-database"`
* `resource_1` - the first component of the resource, if one was passed
* `resource_2` - the second component of the resource, if available
* `actor_*` - a parameter for every key on the actor. Usually `actor_id` is present.

The SQL query can return any of three different types of result:

* No rows at all means "I don't have an opinion about this permission" - which allows the default permission to apply.
* One or more rows means "allow" - unless...
* A single row with a single value of `-1` - which means "deny"

Another example table, this time granting explicit access to individual tables. Consider a table called `table_access` that looks like this:

| user_id | database | table | access_level |
| - | - | - | - |
| 1 | mydb | dogs | 1 |
| 2 | mydb | dogs | 1 |
| 1 | mydb | cats | 1 |
| 2 | mydb | cats | -1 |

The following SQL query would grant access to the `dogs` ttable in the `mydb.db` database to users 1 and 2 - but would forbid access for user 2 to the `cats` table:

```sql
SELECT
    access_level
FROM
    table_access
WHERE
    user_id = :actor_id
    AND "database" = :resource_1
    AND "table" = :resource_2
```
In a `metadata.yaml` configuration file that would look like this:

```yaml
databases:
  mydb:
    allow_sql: {}
plugins:
  datasette-permissions-sql:
  - action: view-table
    sql: |-
      SELECT
        access_level
      FROM
        table_access
      WHERE
        user_id = :actor_id
        AND "database" = :resource_1
        AND "table" = :resource_2
```
We're using `allow_sql: {}` here to disable arbitrary SQL queries to prevent users from running `select * from cats` directly to work around the permissions limits.
