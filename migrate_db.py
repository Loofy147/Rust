from db.models import Base
from db.session import engine

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")