import asyncio
import logging
from typing import Any, Dict, List, Optional
from orchestrator.config import settings

logger = logging.getLogger("founder0.neo4j")

class Neo4jClient:
    """
    Neo4j Graph Database client supporting parameterized Cypher queries,
    node and relationship merging, and an in-memory graph fallback for mock mode.
    """

    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self.mock_mode = settings.MOCK_MODE
        self._driver = None
        self._connected = False

        # In-memory graph representation for mock mode or fallback
        self._in_memory_nodes: Dict[str, Dict[str, Any]] = {}
        self._in_memory_edges: List[Dict[str, Any]] = []

    async def connect(self):
        """Establish connection to Neo4j if available."""
        if self.mock_mode:
            self._connected = False
            return

        try:
            from neo4j import AsyncGraphDatabase
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connectivity
            await self._driver.verify_connectivity()
            self._connected = True
            logger.info("Connected to live Neo4j instance at %s", self.uri)
        except Exception as e:
            logger.warning(f"Could not connect to live Neo4j ({e}). Utilizing robust in-memory graph engine.")
            self._connected = False

    async def close(self):
        if self._driver:
            await self._driver.close()

    async def run_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Run parameterized Cypher query against Neo4j or in-memory fallback."""
        if parameters is None:
            parameters = {}

        if self._connected and self._driver:
            try:
                async with self._driver.session() as session:
                    result = await session.run(query, parameters)
                    records = await result.data()
                    return records
            except Exception as e:
                logger.error(f"Error executing Cypher query on live Neo4j: {e}")
                # Fall back to in-memory

        # In-memory fallback execution for whitespace queries
        if "Complaint" in query and "Feature" in query:
            # Aggregate complaint counts on features
            feature_complaints: Dict[str, int] = {}
            for edge in self._in_memory_edges:
                if edge.get("relationship") == "ABOUT":
                    target = edge.get("target")
                    feature_complaints[target] = feature_complaints.get(target, 0) + 1
            
            records = []
            for node_id, node in self._in_memory_nodes.items():
                if node.get("type") == "Feature":
                    records.append({
                        "feature_name": node.get("label"),
                        "complaint_count": feature_complaints.get(node_id, 1),
                        "competitor_count": sum(1 for e in self._in_memory_edges if e.get("relationship") == "OFFERS" and e.get("target") == node_id)
                    })
            return records

        return []

    async def merge_node(self, node_id: str, label: str, node_type: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Merge a node into the graph (idempotent)."""
        props = properties or {}
        node_obj = {
            "id": node_id,
            "label": label,
            "type": node_type,
            "properties": props
        }
        self._in_memory_nodes[node_id] = node_obj

        if self._connected and self._driver:
            query = f"""
            MERGE (n:{node_type} {{id: $id}})
            SET n.label = $label, n += $properties
            RETURN n
            """
            await self.run_query(query, {"id": node_id, "label": label, "properties": props})

        return node_obj

    async def merge_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Merge a directed relationship between two nodes."""
        props = properties or {}
        edge_obj = {
            "source": source_id,
            "target": target_id,
            "relationship": relationship,
            "properties": props
        }
        # Check duplicate in memory
        exists = any(
            e["source"] == source_id and e["target"] == target_id and e["relationship"] == relationship
            for e in self._in_memory_edges
        )
        if not exists:
            self._in_memory_edges.append(edge_obj)

        if self._connected and self._driver:
            query = f"""
            MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
            MERGE (a)-[r:{relationship}]->(b)
            SET r += $properties
            RETURN r
            """
            await self.run_query(query, {
                "source_id": source_id,
                "target_id": target_id,
                "properties": props
            })

        return edge_obj

    async def get_graph_export(self) -> Dict[str, Any]:
        """Export full graph (nodes + edges) for frontend visualization."""
        if self._connected and self._driver:
            try:
                query = """
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN n, r, m
                """
                records = await self.run_query(query)
                nodes_map = {}
                edges_list = []
                for rec in records:
                    n = rec.get("n")
                    if n:
                        nid = n.get("id") or str(n.element_id)
                        labels = list(n.labels) if hasattr(n, 'labels') else ["Node"]
                        nodes_map[nid] = {
                            "id": nid,
                            "label": n.get("label", nid),
                            "type": labels[0] if labels else "Node",
                            "properties": dict(n)
                        }
                    r = rec.get("r")
                    m = rec.get("m")
                    if r and m:
                        mid = m.get("id") or str(m.element_id)
                        edges_list.append({
                            "source": nid,
                            "target": mid,
                            "relationship": r.type if hasattr(r, 'type') else "RELATED",
                            "properties": dict(r)
                        })
                return {
                    "nodes": list(nodes_map.values()),
                    "edges": edges_list,
                    "node_count": len(nodes_map),
                    "edge_count": len(edges_list)
                }
            except Exception as e:
                logger.error(f"Failed to export live Neo4j graph: {e}")

        return {
            "nodes": list(self._in_memory_nodes.values()),
            "edges": self._in_memory_edges,
            "node_count": len(self._in_memory_nodes),
            "edge_count": len(self._in_memory_edges)
        }

    async def get_graph_stats(self) -> Dict[str, int]:
        """Return total count of nodes and edges."""
        export = await self.get_graph_export()
        return {"nodes": export["node_count"], "edges": export["edge_count"]}

    async def clear_all(self):
        """Clear graph nodes and edges."""
        self._in_memory_nodes.clear()
        self._in_memory_edges.clear()
        if self._connected and self._driver:
            await self.run_query("MATCH (n) DETACH DELETE n")

    async def add_node(self, node_id: str, node_type: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convenience wrapper for merge_node."""
        label = properties.get("name", node_id) if properties else node_id
        return await self.merge_node(node_id=node_id, label=label, node_type=node_type, properties=properties)

    async def add_edge(self, source_id: str, target_id: str, relationship: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convenience wrapper for merge_relationship."""
        return await self.merge_relationship(source_id=source_id, target_id=target_id, relationship=relationship, properties=properties)

    async def init_schema(self):
        """Initialize schema constraints if connected."""
        if self._connected and self._driver:
            for entity in ["Idea", "Competitor", "Feature", "Complaint", "PricingTier"]:
                try:
                    await self.run_query(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{entity}) REQUIRE n.id IS UNIQUE")
                except Exception:
                    pass

neo4j_client = Neo4jClient()
