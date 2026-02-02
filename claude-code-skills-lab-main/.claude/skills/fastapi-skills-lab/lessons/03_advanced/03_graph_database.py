"""
LESSON 13: Graph Databases with Neo4j
=====================================

Integrate graph databases for relationship-heavy data.

Key Concepts:
- Neo4j setup
- Node and relationship models
- Cypher queries
- Graph traversal patterns

To run:
    uv run uvicorn lessons.03_advanced.03_graph_database:app --reload

Requires: Neo4j running (docker run -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j)
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings


# =============================================================================
# Configuration
# =============================================================================

class Neo4jSettings(BaseSettings):
    """Neo4j configuration."""
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "password"

    class Config:
        env_prefix = "NEO4J_"


settings = Neo4jSettings()


# =============================================================================
# Neo4j Driver (Simulated for Demo)
# =============================================================================

class Neo4jDriver:
    """
    Simulated Neo4j driver.

    In production, use:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(user, password))
    """

    def __init__(self):
        self.nodes: dict[str, dict] = {}
        self.relationships: list[dict] = []
        self._id_counter = 0

    def _next_id(self) -> str:
        self._id_counter += 1
        return str(self._id_counter)

    def create_node(self, label: str, properties: dict) -> dict:
        """Create a node."""
        node_id = self._next_id()
        node = {"id": node_id, "label": label, "properties": properties}
        self.nodes[node_id] = node
        return node

    def create_relationship(self, from_id: str, to_id: str, rel_type: str, properties: dict = None) -> dict:
        """Create a relationship."""
        if from_id not in self.nodes or to_id not in self.nodes:
            raise ValueError("Node not found")
        rel = {
            "id": self._next_id(),
            "from": from_id,
            "to": to_id,
            "type": rel_type,
            "properties": properties or {}
        }
        self.relationships.append(rel)
        return rel

    def find_nodes(self, label: str = None) -> list[dict]:
        """Find nodes by label."""
        if label:
            return [n for n in self.nodes.values() if n["label"] == label]
        return list(self.nodes.values())

    def find_relationships(self, node_id: str, direction: str = "both") -> list[dict]:
        """Find relationships for a node."""
        results = []
        for rel in self.relationships:
            if direction in ("out", "both") and rel["from"] == node_id:
                results.append(rel)
            if direction in ("in", "both") and rel["to"] == node_id:
                results.append(rel)
        return results

    def get_neighbors(self, node_id: str, rel_type: str = None) -> list[dict]:
        """Get neighboring nodes."""
        neighbors = []
        for rel in self.relationships:
            target_id = None
            if rel["from"] == node_id:
                target_id = rel["to"]
            elif rel["to"] == node_id:
                target_id = rel["from"]

            if target_id and (not rel_type or rel["type"] == rel_type):
                neighbors.append(self.nodes[target_id])
        return neighbors

    def shortest_path(self, from_id: str, to_id: str) -> list[str] | None:
        """Find shortest path between nodes (BFS)."""
        if from_id not in self.nodes or to_id not in self.nodes:
            return None

        visited = {from_id}
        queue = [[from_id]]

        while queue:
            path = queue.pop(0)
            current = path[-1]

            if current == to_id:
                return path

            for neighbor in self.get_neighbors(current):
                if neighbor["id"] not in visited:
                    visited.add(neighbor["id"])
                    queue.append(path + [neighbor["id"]])

        return None


# Global driver instance
driver = Neo4jDriver()


def get_driver() -> Neo4jDriver:
    """Dependency to get Neo4j driver."""
    return driver


# =============================================================================
# Schemas
# =============================================================================

class PersonCreate(BaseModel):
    name: str
    age: int | None = None


class RelationshipCreate(BaseModel):
    from_id: str
    to_id: str
    rel_type: str


# =============================================================================
# Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize sample data."""
    # Create sample social network
    alice = driver.create_node("Person", {"name": "Alice", "age": 30})
    bob = driver.create_node("Person", {"name": "Bob", "age": 25})
    carol = driver.create_node("Person", {"name": "Carol", "age": 35})
    dave = driver.create_node("Person", {"name": "Dave", "age": 28})

    driver.create_relationship(alice["id"], bob["id"], "KNOWS")
    driver.create_relationship(bob["id"], carol["id"], "KNOWS")
    driver.create_relationship(carol["id"], dave["id"], "KNOWS")
    driver.create_relationship(alice["id"], carol["id"], "WORKS_WITH")

    print("Sample graph created with 4 people")
    yield


app = FastAPI(
    title="Graph Database Demo",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Graph database info."""
    return {
        "database": "Neo4j (simulated)",
        "nodes": len(driver.nodes),
        "relationships": len(driver.relationships),
        "sample_cypher": "MATCH (p:Person)-[:KNOWS]->(friend) RETURN p, friend"
    }


@app.post("/nodes/person")
async def create_person(person: PersonCreate, db: Neo4jDriver = Depends(get_driver)):
    """Create a Person node."""
    node = db.create_node("Person", person.model_dump())
    return node


@app.get("/nodes")
async def list_nodes(label: str = None, db: Neo4jDriver = Depends(get_driver)):
    """List all nodes."""
    return {"nodes": db.find_nodes(label)}


@app.get("/nodes/{node_id}")
async def get_node(node_id: str, db: Neo4jDriver = Depends(get_driver)):
    """Get a specific node."""
    if node_id not in db.nodes:
        raise HTTPException(404, "Node not found")
    return db.nodes[node_id]


@app.post("/relationships")
async def create_relationship(rel: RelationshipCreate, db: Neo4jDriver = Depends(get_driver)):
    """Create a relationship."""
    try:
        return db.create_relationship(rel.from_id, rel.to_id, rel.rel_type)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/nodes/{node_id}/neighbors")
async def get_neighbors(node_id: str, rel_type: str = None, db: Neo4jDriver = Depends(get_driver)):
    """Get neighboring nodes."""
    if node_id not in db.nodes:
        raise HTTPException(404, "Node not found")
    return {"neighbors": db.get_neighbors(node_id, rel_type)}


@app.get("/path/{from_id}/{to_id}")
async def find_path(from_id: str, to_id: str, db: Neo4jDriver = Depends(get_driver)):
    """Find shortest path between nodes."""
    path = db.shortest_path(from_id, to_id)
    if not path:
        raise HTTPException(404, "No path found")

    # Return path with node details
    return {
        "path": [db.nodes[nid] for nid in path],
        "length": len(path) - 1
    }


# =============================================================================
# Key Concepts
# =============================================================================

"""
GRAPH DATABASE CONCEPTS:
- Nodes: Entities (Person, Product, etc.)
- Relationships: Connections between nodes (KNOWS, BOUGHT)
- Properties: Key-value data on nodes/relationships
- Labels: Node categories

CYPHER QUERIES (Neo4j):
- CREATE (n:Person {name: 'Alice'})
- MATCH (p:Person) RETURN p
- MATCH (a)-[:KNOWS]->(b) RETURN a, b
- MATCH path = shortestPath((a)-[*]-(b)) RETURN path

USE CASES:
- Social networks (friends, followers)
- Recommendation engines
- Fraud detection
- Knowledge graphs
- Network/IT infrastructure

NEO4J WITH FASTAPI:
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(uri, auth=(user, pass))

    async def get_session():
        with driver.session() as session:
            yield session
"""
