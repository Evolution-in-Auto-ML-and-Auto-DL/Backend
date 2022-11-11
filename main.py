from fastapi import FastAPI, File, UploadFile
import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column, Integer, String, MetaData



SQLALCHEMY_DATABASE_URL = "postgresql://postgres:mbQwF71Wz3GkDNNP@db.rnitzjdeuuqtgkbjuxzp.supabase.co:5432/postgres"

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Server is running"}


@app.post("/upload_dataset")
def upload_dataset(file: UploadFile):
    accepted_mimes = ["text/csv"]
    try:
        contents = file.file.read()
        print(file.content_type)
        if file.content_type in accepted_mimes :
            with open(file.filename, 'wb') as f:
                f.write(contents)
        else:
            print("Wrong Format")
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()

    return {"message": f"Successfully uploaded {file.filename}"}


@app.get("/projects")
def fetch_projects():
    return Base.metadata


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

    uvicorn.run(app)