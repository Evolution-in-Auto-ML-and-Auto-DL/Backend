from pydantic import BaseModel
from typing import Any

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

import uvicorn

import databases

from sqlalchemy import create_engine,select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column, Integer, String, MetaData

import pandas as pd

import evalml
from evalml import AutoMLSearch

import pickle


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

@app.post("/upload_dataset_details")
async def knockdown(values:Project):
    # ins = projects.insert().values(name=values.name,description=values.description,location=DATASET_STORAGE_PATH+'/'+values.dataset)
    query = "INSERT INTO projects(name,description,location) VALUES (:name, :description, :location)"
    values = {
        "name": values.name,
        "description": values.description,
        "location": str(DATASET_STORAGE_PATH+'/'+values.dataset)
    }
    last_record_id = await database.execute(query=query,values=values)

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

@app.get("/project/{id}")
async def get_project_meta(id: int):
    # query = projects.select(id=id)
    query = "SELECT * FROM projects WHERE id = :id"
    return await database.fetch_one(query=query, values={"id":id})

############################################# CLEANING ##############################################

class CleaningData(BaseModel):
    url: str

@app.post("/cleaning_info")
async def getCleaning(data: CleaningData):
    loc = data.url
    data = pd.read_csv(loc)
    cat = []
    num = []
    for i in data.columns:
        if data[i].dtype == 'object':
            cat.append(i)
        else:
            num.append(i)

    return [cat,num]

class CleanMethod(BaseModel):
    url: str
    tags: list = []

@app.post("/cleaning")
async def getCleaning(data: CleanMethod):
    loc = data.url
    tags = data.tags

    data = pd.read_csv(loc)

    print(data.isnull().values.any())

    def statistics(series,method):
        if method == 'mode':
            mode = series.value_counts().index[0]
            return (mode)
        elif method == 'mean':
            return series.mean()
        else:
            return series.median()

    for col, method in tags:
        if method == 'mean' or method == 'mode' or method == 'median':
            stat = statistics(data[col], method)
            data[col].fillna(stat, inplace=True)
        else:
            data[col].fillna(method=method, inplace=True)

    print(data.isnull().values.any())

    data.to_csv(loc, header=True, index=False)

    return {"it":"worked"}


############################################## MODEL BUILDING ##########################################

class ModelData(BaseModel):
    url: str
    y: str


@app.post("/evalml_info")
async def getModel(data: ModelData):
    loc = data.url
    y = data.y

    data = pd.read_csv(loc)

    X = data.drop(y, axis=1)
    y = data[y]

    X_train, X_test, y_train, y_test = evalml.preprocessing.split_data(X, y, problem_type="regression")

    automl = evalml.automl.AutoMLSearch(X_train=X_train,y_train= y_train, problem_type="regression")
    automl.search()

    pipelines = automl.rankings.pipeline_name[:10]
    temp = (list(pipelines.values))

    return temp

@app.post("/evalml_run")
async def saveModel(data: ModelData):
    loc = data.url
    y = data.y

    data = pd.read_csv(loc)

    X = data.drop(y, axis=1)
    y = data[y]

    X_train, X_test, y_train, y_test = evalml.preprocessing.split_data(X, y, problem_type="regression")

    automl = evalml.automl.AutoMLSearch(X_train=X_train,y_train= y_train, problem_type="regression")
    automl.search()

    best = automl.best_pipeline

    best.save("/home/athena/Desktop/ATHENA/STORAGE/CurrentModel/model.pkl")

    return {"saved":"model"}

######################## Error Metrics ######################

class ErrorData(BaseModel):
    url: str
    y: str
    metrics: list

@app.get("/fetch_error_metrics")
async def error():
    return ['Mean Squared Error', 'Root Mean squared errow', 'Mean Absolute Error', 'R-Squared']
        
@app.post("/error_metrics")
async def error(data: ErrorData):
    metrics = data.metrics

    loc = data.url

    y = data.y

    print(metrics)

    convert = {'Mean Squared Error':'mse', 'Root Mean squared errow':'root mean squared log error', 'Mean Absolute Error':'mae', 'R-Squared':'r2'}

    metrics = [convert[x] for x in metrics]

    model = evalml.automl.AutoMLSearch.load("/home/athena/Desktop/ATHENA/STORAGE/CurrentModel/model.pkl")

    data = pd.read_csv(loc)

    X = data.drop(y, axis=1)
    y = data[y]

    X_train, X_test, y_train, y_test = evalml.preprocessing.split_data(X, y, problem_type="regression")

    result = model.score(X_test, y_test, objectives=metrics)

    with open('/home/athena/Desktop/ATHENA/STORAGE/CurrentModel/reports', 'wb') as fp:
        pickle.dump(result, fp)
    
    return {"status":"success"}

############################################ Reports #########################################

@app.get("/reports")
async def error():
    with open('/home/athena/Desktop/ATHENA/STORAGE/CurrentModel/reports', 'rb') as fp:
        result = pickle.load(fp)
    return result


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
        Column('description', String),
        Column('location', String) 
    )

    meta.create_all(engine)

    uvicorn.run(app, host="194.195.119.85")
