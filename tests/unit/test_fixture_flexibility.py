import pytest
from orchestrator.clients.oxylabs_client import oxylabs_client

def test_seed_reproducibility():
    """Verify that specifying a seed guarantees deterministic fixture output."""
    fix1 = oxylabs_client.get_fixture_data("an AI accountant for freelancers", seed=42)
    fix2 = oxylabs_client.get_fixture_data("an AI accountant for freelancers", seed=42)
    assert fix1["category"] == fix2["category"]
    assert fix1["keywords"] == fix2["keywords"]
    assert fix1["raw_complaint_pool"] == fix2["raw_complaint_pool"]
    assert [c["name"] for c in fix1["competitors"]] == [c["name"] for c in fix2["competitors"]]
    assert fix1["market_size"] == fix2["market_size"]

def test_randomization_variety():
    """Verify that multiple unseeded calls across the extended complaint pool produce variation."""
    results = [
        oxylabs_client.get_fixture_data("roommate bill split")["raw_complaint_pool"]
        for _ in range(5)
    ]
    # At least two runs should have different first complaints or different subsets
    unique_pools = len(set(tuple(r) for r in results))
    assert unique_pools > 1, "Expected randomized sampling across extended complaint pools"

def test_all_categories_invariants():
    """Verify minimum data guarantees for all supported categories."""
    categories = ["productivity", "fintech", "devtools", "health", "social"]
    for cat in categories:
        data = oxylabs_client.get_fixture_data(cat)
        assert data["category"] == cat
        assert len(data["competitors"]) >= 4, f"Category {cat} should have >= 4 competitors"
        assert len(data["raw_complaint_pool"]) >= 8, f"Category {cat} should have >= 8 complaints"
        assert len(data["keywords"]) >= 3, f"Category {cat} should have >= 3 keywords"
        assert "B" in data["market_size"], f"Category {cat} should have formatted market size"

def test_unknown_query_fallback():
    """Verify that unknown inputs gracefully resolve to default fixtures without crashing."""
    data = oxylabs_client.get_fixture_data("quantum teleportation interstellar rocket propulsion")
    assert "category" in data
    assert len(data["competitors"]) >= 4
    assert len(data["raw_complaint_pool"]) >= 8
