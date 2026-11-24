import csv
import io

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.pydantic_bank_validation import (
    get_batch_summary,
    validate_csv,
    validate_records,
    HeaderValidationResult
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.get("/health")
def read_root():
    return {"message": "Are you running?"}

async def validate_helper(file: UploadFile = File(...)):
    file_bytes = await file.read()
    file_text = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(file_text))
    valid_headers = validate_csv(reader.fieldnames)
    if not valid_headers.valid:
        return valid_headers
    else:
        record_validation = validate_records(reader)
        preflight_summary = get_batch_summary(record_validation.valid_records, record_validation.failed_records, record_validation.errors )
        return {
                "summary": preflight_summary,
                "validation": record_validation,
}

@app.post("/validate")
async def validate_file(file: UploadFile = File(...)):
    return await validate_helper(file)
    


@app.post("/submit-batch")
async def submit_batch(file: UploadFile = File(...)):
    validation_result = await validate_helper(file)
    if isinstance(validation_result, HeaderValidationResult):
        return validation_result
    if validation_result["summary"].failed_records > 0:
        return validation_result
    if validation_result["summary"].total_records == 0:
        raise HTTPException(400, detail="Batch File contains no records")
    return validation_result
   

