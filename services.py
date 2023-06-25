from sqlmodel import SQLModel, create_engine
import models

engine = create_engine('postgresql://co2-sa-db.postgres.database.azure.com:5432/seattlebeb?user=co2sodapg&password=Greta2023&sslmode=require')

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
