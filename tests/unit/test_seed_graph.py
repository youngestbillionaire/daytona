import pytest
from orchestrator.seed_graph import seed_baseline_graph
from orchestrator.clients.neo4j_client import neo4j_client

@pytest.mark.asyncio
async def test_seed_baseline_graph():
    await seed_baseline_graph()
    stats = await neo4j_client.get_graph_stats()
    assert stats["nodes"] > 0
    assert stats["edges"] > 0
