from fastapi import FastAPI, UploadFile, File
import csv, io

app = FastAPI()

@app.get("/health")
def read_root():
    return {"message": "Are you running?"}

@app.post("/validate")
async def validate_file(file: UploadFile = File(...)):
    file_bytes = await file.read()
    file_text = file_bytes.decode("utf-8-sig")
    return {"filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_bytes),
            "preview": file_text[0:100]}