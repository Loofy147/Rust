from sqlalchemy import create_engine, Column, String, Text, MetaData, Table
from sqlalchemy.orm import sessionmaker
from agent.interfaces import KGPlugin

class SQLAlchemyKG(KGPlugin):
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.metadata = MetaData()
        self.nodes = Table('nodes', self.metadata,
            Column('id', String, primary_key=True),
            Column('type', String),
            Column('data', Text)
        )
        self.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def query(self, query: str) -> dict:
        # Example: simple query by id
        session = self.Session()
        result = session.execute(self.nodes.select().where(self.nodes.c.id == query)).fetchone()
        session.close()
        if result:
            return dict(result)
        return {}

    def store(self, data: dict) -> None:
        session = self.Session()
        session.execute(self.nodes.insert().values(**data))
        session.commit()
        session.close()