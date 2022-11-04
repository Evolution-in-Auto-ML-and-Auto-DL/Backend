from fastapi import FastAPI, File, UploadFile
import uvicorn

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


if __name__ == "__main__":
    uvicorn.run(app)