from datasette.app import Datasette
import httpx
import sqlite_utils
import pytest


def create_tables(conn):
    db = sqlite_utils.Database(conn)
    db["table_access"].insert_all(
        [
            {"user_id": 1, "database": "test", "table": "dogs", "access_level": 1},
            {"user_id": 2, "database": "test", "table": "dags", "access_level": 1},
            {"user_id": 1, "database": "test", "table": "cats", "access_level": 1},
            {"user_id": 2, "database": "test", "table": "cats", "access_level": -1},
        ]
    )
    db["cats"].insert({"name": "Casper"})
    db["dogs"].insert({"name": "Cleo"})


@pytest.fixture
async def ds(tmpdir):
    filepath = tmpdir / "test.db"
    ds = Datasette(
        [filepath],
        metadata={
            "plugins": {
                "datasette-permissions-sql": [
                    {
                        "action": "view-table",
                        "sql": """
                    SELECT
                        access_level
                    FROM
                        table_access
                    WHERE
                        user_id = :actor_id
                        AND "database" = :resource_1
                        AND "table" = :resource_2
                """,
                    },
                    {
                        "action": "view-database",
                        "sql": """
                    SELECT
                        1
                    FROM
                        table_access
                    WHERE
                        user_id = :actor_id
                """,
                    },
                ]
            },
            "databases": {"test": {"allow": {}, "allow_sql": {}}},
        },
    )
    await ds.get_database().execute_write_fn(create_tables, block=True)
    return ds


@pytest.mark.asyncio
async def test_ds_fixture(ds):
    assert {"table_access", "cats", "dogs"} == set(
        await ds.get_database().table_names()
    )


@pytest.mark.parametrize(
    "actor,table,expected_status",
    [
        (None, "dogs", 403),
        (None, "cats", 403),
        ({"id": 1}, "dogs", 200),
        ({"id": 2}, "dogs", 200),
        ({"id": 1}, "cats", 200),
        ({"id": 2}, "cats", 403),
    ],
)
@pytest.mark.asyncio
async def test_permissions_sql(ds, actor, table, expected_status):
    async with httpx.AsyncClient(app=ds.app()) as client:
        cookie = ds.sign({"a": actor}, "actor")
        response = await client.get(
            "http://localhost/test/{}".format(table), cookies={"ds_actor": cookie}
        )
        assert expected_status == response.status_code
