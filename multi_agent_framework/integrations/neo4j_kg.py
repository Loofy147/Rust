from neo4j import GraphDatabase


class Neo4jKnowledgeGraph:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_entity(self, entity, label):
        with self.driver.session() as session:
            session.run(
                "MERGE (e:Entity {name: $name, label: $label})",
                name=entity,
                label=label)

    def add_relation(self, src, dst, relation):
        with self.driver.session() as session:
            session.run(
                "MATCH (a:Entity {name: $src}), (b:Entity {name: $dst}) "
                "MERGE (a)-[r:REL {type: $rel}]->(b)",
                src=src,
                dst=dst,
                rel=relation)

    def query(self, entity):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (e:Entity {name: $name})-->(n) RETURN n.name, n.label",
                name=entity)
            return [(record["n.name"], record["n.label"]) for record in result]