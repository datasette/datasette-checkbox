from datasette.app import Datasette
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("is_root", (False, True))
async def test_plugin_adds_javascript(is_root):
    datasette = Datasette()
    datasette.root_enabled = True
    db = datasette.add_memory_database("demo")
    await db.execute_write(
        "CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, is_active INTEGER)"
    )
    await datasette.invoke_startup()
    cookies = {}
    if is_root:
        cookies["ds_actor"] = datasette.client.actor_cookie({"id": "root"})
    response = await datasette.client.get("/demo/test", cookies=cookies)
    assert response.status_code == 200
    js_snippet = "handleCheckboxChange(event.target);"
    if is_root:
        assert js_snippet in response.text
    else:
        assert js_snippet not in response.text
