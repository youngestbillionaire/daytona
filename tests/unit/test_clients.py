import pytest
from orchestrator.clients.daytona_client import daytona_client
from orchestrator.clients.oxylabs_client import oxylabs_client
from orchestrator.clients.neo4j_client import neo4j_client
from orchestrator.clients.nosana_client import nosana_client
from orchestrator.clients.fallback_llm_client import fallback_llm_client, clean_json_response

@pytest.mark.asyncio
async def test_daytona_client_local_sandbox():
    sandbox = await daytona_client.create_sandbox()
    assert sandbox.sandbox_id.startswith("sbx_")
    assert sandbox.workspace_path != ""

    # Test file write and read
    test_rel_path = "test_file.txt"
    test_content = "Hello from FOUNDER-0 automated test"
    await sandbox.write_file(test_rel_path, test_content)

    read_back = await sandbox.read_file(test_rel_path)
    assert read_back == test_content

    # Test command execution
    exec_res = await sandbox.exec_command("echo 'Daytona Sandbox Ready'")
    assert exec_res.exit_code == 0
    assert "Daytona Sandbox Ready" in exec_res.stdout

    # Test get_sandbox retrieval
    fetched = await daytona_client.get_sandbox(sandbox.sandbox_id)
    assert fetched is not None
    assert fetched.sandbox_id == sandbox.sandbox_id

@pytest.mark.asyncio
async def test_oxylabs_client_categories():
    categories_prompts = [
        ("roommate rent bill split", "productivity"),
        ("ai tax invoice accounting", "fintech"),
        ("local hobby meetup friend club", "social"),
        ("circadian sleep health recovery caffeine", "health"),
        ("database postgres schema migration linter", "devtools"),
    ]
    for prompt, expected_category in categories_prompts:
        fixture = oxylabs_client.get_fixture_data(prompt)
        assert fixture["category"] == expected_category
        assert len(fixture["competitors"]) >= 4
        assert len(fixture["raw_complaint_pool"]) >= 8

    # Test search query mock
    res = await oxylabs_client.search_query("test query")
    assert "status" in res

@pytest.mark.asyncio
async def test_neo4j_in_memory_client():
    await neo4j_client.init_schema()

    # Clear and insert nodes
    await neo4j_client.clear_all()
    await neo4j_client.add_node("n1", "Competitor", {"name": "TestComp"})
    await neo4j_client.add_node("n2", "Feature", {"name": "TestFeat"})
    await neo4j_client.add_edge("n1", "n2", "OFFERS")

    stats = await neo4j_client.get_graph_stats()
    assert stats["nodes"] >= 2
    assert stats["edges"] >= 1

    query_res = await neo4j_client.run_query("MATCH (n) RETURN n")
    assert isinstance(query_res, list)

@pytest.mark.asyncio
async def test_fallback_llm_and_json_cleaner():
    # Test json parsing and markdown fence stripping
    raw_markdown = '```json\n{"status": "ok", "count": 42}\n```'
    parsed = clean_json_response(raw_markdown)
    assert parsed["status"] == "ok"
    assert parsed["count"] == 42

    # Test nosana client mock generate
    res, provider = await nosana_client.generate_chat("test prompt", json_mode=True)
    assert isinstance(res, dict)
    assert "nosana" in provider
