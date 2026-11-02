from fastapi import FastAPI, UploadFile, File
import csv, io

from backend.pydantic_bank_validation import validate_csv, validate_records, get_batch_summary

app = FastAPI()

@app.get("/health")
def read_root():
    return {"message": "Are you running?"}

@app.post("/validate")
async def validate_file(file: UploadFile = File(...)):
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