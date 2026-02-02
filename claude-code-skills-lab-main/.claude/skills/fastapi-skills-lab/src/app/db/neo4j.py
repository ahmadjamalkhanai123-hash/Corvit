"""
Neo4j Graph Database Configuration
==================================

Neo4j connection and session management.
"""

from typing import Generator, Any
from contextlib import contextmanager

from ..core.config import settings


class Neo4jConnection:
    """
    Neo4j database connection manager.

    Usage:
        connection = Neo4jConnection(uri, user, password)
        with connection.session() as session:
            result = session.run("MATCH (n) RETURN n")
    """

    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None
    ):
        self.uri = uri or getattr(settings, 'neo4j_uri', 'bolt://localhost:7687')
        self.user = user or getattr(settings, 'neo4j_user', 'neo4j')
        self.password = password or getattr(settings, 'neo4j_password', 'password')
        self._driver = None

    def connect(self):
        """
        Establish connection to Neo4j.

        Requires: pip install neo4j
        """
        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
        except ImportError:
            raise ImportError("neo4j package required: pip install neo4j")

    def close(self):
        """Close connection."""
        if self._driver:
            self._driver.close()
            self._driver = None

    @contextmanager
    def session(self):
        """Get a session context manager."""
        if not self._driver:
            self.connect()
        session = self._driver.session()
        try:
            yield session
        finally:
            session.close()

    def execute(self, query: str, parameters: dict = None) -> list[dict]:
        """Execute a Cypher query."""
        with self.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def create_node(self, label: str, properties: dict) -> dict:
        """Create a node."""
        query = f"CREATE (n:{label} $props) RETURN n"
        result = self.execute(query, {"props": properties})
        return result[0] if result else None

    def find_nodes(self, label: str, filters: dict = None) -> list[dict]:
        """Find nodes by label and optional filters."""
        if filters:
            conditions = " AND ".join([f"n.{k} = ${k}" for k in filters])
            query = f"MATCH (n:{label}) WHERE {conditions} RETURN n"
        else:
            query = f"MATCH (n:{label}) RETURN n"
        return self.execute(query, filters)

    def create_relationship(
        self,
        from_label: str,
        from_id: Any,
        to_label: str,
        to_id: Any,
        rel_type: str,
        properties: dict = None
    ) -> dict:
        """Create a relationship between nodes."""
        query = f"""
        MATCH (a:{from_label}), (b:{to_label})
        WHERE id(a) = $from_id AND id(b) = $to_id
        CREATE (a)-[r:{rel_type} $props]->(b)
        RETURN r
        """
        result = self.execute(query, {
            "from_id": from_id,
            "to_id": to_id,
            "props": properties or {}
        })
        return result[0] if result else None


# Global connection
neo4j_connection = None


def get_neo4j() -> Neo4jConnection:
    """Dependency for Neo4j connection."""
    global neo4j_connection
    if neo4j_connection is None:
        neo4j_connection = Neo4jConnection()
    return neo4j_connection


def close_neo4j():
    """Close Neo4j connection."""
    global neo4j_connection
    if neo4j_connection:
        neo4j_connection.close()
        neo4j_connection = None
