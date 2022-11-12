from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import databases
from sqlalchemy import create_engine,select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column, Integer, String, MetaData


SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
DATASET_STORAGE_PATH = "/home/athena/Desktop/ATHENA/STORAGE/DATASETS"

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://194.195.119.85:3000",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database = databases.Database(SQLALCHEMY_DATABASE_URL)

class Project(BaseModel):
    name: str
    description: str
    dataset: str

@app.get("/")
async def read_root():
    return {"message": "Server is running"}

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/knockdown")
def knockdown(values:Project):
    print(values)
    return values

@app.post("/upload_dataset")
def upload_dataset(file: UploadFile):
    accepted_mimes = ["text/csv"]
    try:
        contents = file.file.read()
        print(file.content_type)
        if file.content_type in accepted_mimes :
            with open(DATASET_STORAGE_PATH+"/"+file.filename, 'wb') as f:
                f.write(contents)
        else:
            print("Wrong Format")
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()

    return {"message": f"Successfully uploaded {file.filename}"}


@app.get("/projects")
async def fetch_projects():
    query = projects.select()
    return await database.fetch_all(query)


if __name__ == "__main__":
    meta = MetaData()

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base = declarative_base()
    
    projects = Table(
    'projects', meta, 
    Column('id', Integer, primary_key = True), 
    Column('name', String), 
    )

    meta.create_all(engine)

    uvicorn.run(app, host="194.195.119.85")
