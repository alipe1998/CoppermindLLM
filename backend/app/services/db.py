from neo4j import GraphDatabase

class Neo4jHelper:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.create_unique_constraint()  # Ensure unique URL nodes are enforced

    def close(self):
        self.driver.close()

    def create_unique_constraint(self):
        """Creates a unique constraint on the URL property for URL nodes."""
        with self.driver.session() as session:
            session.execute_write(self._create_unique_constraint)

    @staticmethod
    def _create_unique_constraint(tx):
        # Creates a unique constraint on :URL nodes if it doesn't already exist.
        tx.run("CREATE CONSTRAINT IF NOT EXISTS ON (u:URL) ASSERT u.url IS UNIQUE")

    def create_url_node(self, url):
        with self.driver.session() as session:
            session.execute_write(self._create_url_node, url)

    def create_relationship(self, url1, url2):
        with self.driver.session() as session:
            session.execute_write(self._create_relationship, url1, url2)

    @staticmethod
    def _create_url_node(tx, url):
        tx.run("MERGE (u:URL {url: $url})", url=url)

    @staticmethod
    def _create_relationship(tx, url1, url2):
        # Creates a single directional relationship from url1 to url2.
        tx.run("""
        MATCH (a:URL {url: $url1}), (b:URL {url: $url2})
        MERGE (a)-[:LINKS_TO]->(b)
        """, url1=url1, url2=url2)
