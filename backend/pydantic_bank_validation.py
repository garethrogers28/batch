import csv
import os
import random
import re
from typing import Annotated

from pydantic import BaseModel, Field, ValidationError, field_validator

TEMPLATE_HEADERS = [
    "Customer Name (Mandatory)",
    "Bank Account Number (Mandatory)",
    "Sort Code (Mandatory)",
    "Account Type (Mandatory)",
    "Secondary Reference (Optional)",
    "Client Reference (Optional)",
]

EXPECTED_HEADERS = TEMPLATE_HEADERS

FILE_PATH = "bank-accounts.csv"

MAX_FILE_SIZE = 6 * 1024 * 1024  # 6 MB upload limit
MAX_PAYPOINT_BATCH_LIMIT = 25  # Paypoint only accepts batches of up to 25 records


class Customer(BaseModel):
    """Represents a bank customer with validated fields."""
    customer_name: Annotated[str, Field(strict=True, alias="Customer Name (Mandatory)")]
    bank_account_number: Annotated[str, Field(strict=True, alias="Bank Account Number (Mandatory)")]
    sort_code: Annotated[str, Field(strict=True, alias="Sort Code (Mandatory)")]
    account_type:Annotated[str, Field(strict=True, alias="Account Type (Mandatory)")]
    secondary_reference:Annotated[str | None, Field(alias="Secondary Reference (Optional)")] = None
    client_reference:Annotated[str | None, Field(alias="Client Reference (Optional)")] = None

    @field_validator("account_type")
    @classmethod
    def check_account_type(cls, value):
        # Only these two account types are supported by Paypoint
        if value not in {"Business", "Personal"}:
            raise ValueError("Account type must be 'Business' or 'Personal'")
        return value

    @field_validator("sort_code")
    @classmethod
    def check_sort_code(cls, value):
        # UK sort codes are always 6 digits
        if not re.fullmatch(r"[0-9]{6}", value):
            raise ValueError("Sort code must be exactly 6 digits")
        return value

    @field_validator("bank_account_number")
    @classmethod
    def check_account_number(cls, value):
        # UK account numbers are always 8 digits
        if not re.fullmatch(r"[0-9]{8}", value):
            raise ValueError("Account number must be exactly 8 digits")
        return value

class HeaderValidationResult(BaseModel):
    """Reports whether an uploaded CSV contains every expected column."""
    valid:bool
    missing_fields:set[str]

class RecordValidationError(BaseModel):
    """Describes one field-level validation error in a customer row."""
    row:int
    field:str
    message:str

class RecordValidationResult(BaseModel):
    """Collects valid customers and errors produced while validating CSV rows."""
    valid_records:list[Customer]
    failed_records:int
    errors:list[RecordValidationError]
    invalid_records:list[dict]
   
class PreflightSummary(BaseModel):
    """Summarizes record-validation totals before batch submission."""
    total_records:int
    valid_records:int
    errors:int
    failed_records:int
    batch_result:bool

class Batch(BaseModel):
    """Represents a submitted Paypoint batch and its matching results."""
    status:str
    submitted_records:int
    paypoint_batch_ids:list[int]
    results: list[dict] | None = None


def is_file_size_valid(file_path):
    """Check the file is within the allowed size limit."""
    return os.path.getsize(file_path) <= MAX_FILE_SIZE

def validate_csv(headers):
    """Validate CSV headers against expected fields."""
    missing_fields = set(EXPECTED_HEADERS).difference(headers)
    return HeaderValidationResult(missing_fields=missing_fields, valid=not missing_fields)

def get_total_records(valid_records, failed_records):
    """Calculate the total number of records processed."""
    return len(valid_records) + failed_records
    
def validate_records(reader):
    """Validate customer records against the Customer model schema."""
    valid_records = []
    errors = []
    failed_records = 0
    invalid_records = []
    for index, row in enumerate(reader, start=2):  # start=2 accounts for the header row
        try:
            valid_records.append(Customer(**row))
        except ValidationError as e:
            invalid_records.append({"row_number": index, "data": row})
            failed_records += 1
            # A single row can fail on multiple fields, so record each one separately
            for error in e.errors():
                errors.append(RecordValidationError(row=index, field=error["loc"][0], message=error["msg"]))
    return RecordValidationResult(valid_records=valid_records, errors=errors, failed_records=failed_records, invalid_records=invalid_records)

def update_invalid_record(record, field, new_value):
    """update invalid record so it can be submitted"""
    record["data"][field] = new_value
    return record

def revalidate_record(record):
    return Customer(**record["data"])

def get_batch_result(failed_records):
    """Determine if batch validation passed (no failed records)."""
    return failed_records == 0


def get_batch_summary(valid_records, failed_records, errors):
    """Generate a pre-flight summary of batch validation results."""
    return PreflightSummary(
        total_records=get_total_records(valid_records, failed_records),
        valid_records=len(valid_records),
        errors=len(errors),
        failed_records=failed_records,
        batch_result=get_batch_result(failed_records))


def split_into_batches(records, batch_size):
    """Yield successive batch_size chunks from records."""
    for start in range(0, len(records), batch_size):
        yield records[start:start + batch_size]


def mock_submit_to_paypoint(split_batch):
    """Mock Paypoint submission — replace with real API call."""
    return random.randint(100000, 999999)  # Stand-in for a real batch ID returned by Paypoint


def submit_all_batches(valid_records):
    """Split valid records into batches, submit each, and keep the customers with their batch id."""
    return [
        (mock_submit_to_paypoint(split_batch), split_batch)
        for split_batch in split_into_batches(valid_records, MAX_PAYPOINT_BATCH_LIMIT)
    ]



def mock_check_paypoint_status(paypoint_batch_id):
    """Mock Paypoint status check — replace with real API call."""
    return random.choice(["Processed"])  # Always "Processed" since there's no real API yet


def check_all_paypoint_statuses(batches):
    """Check every submitted batch and report whether all have been processed."""
    statuses = {
        batch_id: mock_check_paypoint_status(batch_id)
        for batch_id, _ in batches
    }
    all_processed = all(status != "Pending" for status in statuses.values())
    return all_processed, statuses


def mock_retrieve_paypoint_batch_results(customers):
    """Mock Paypoint result retrieval — replace with real API call."""
    return [
        {
            "Name": customer.customer_name,
            "Account Type": customer.account_type,
            "Result": random.choice(["Full Match", "No Match"]),
            "Client Reference ID": customer.client_reference,
        }
        for customer in customers
    ]

def combine_batch_results(batches):
    """Fetch and flatten results from every submitted batch into one list."""
    final_batch_results = []
    for _, customers in batches:
        final_batch_results.extend(mock_retrieve_paypoint_batch_results(customers))
    return final_batch_results

def process_valid_batch(valid_records):
    """Submit, poll, and collect results for a batch of valid customer records."""
    batches = submit_all_batches(valid_records)
    all_processed, _ = check_all_paypoint_statuses(batches)
    paypoint_batch_ids = [batch_id for batch_id, _ in batches]

    # Don't fetch results until every batch has finished processing
    if not all_processed:
        return Batch(status="Pending", submitted_records=len(valid_records), paypoint_batch_ids=paypoint_batch_ids, results=None)

    return Batch(status="Processed", submitted_records=len(valid_records), paypoint_batch_ids=paypoint_batch_ids, results=combine_batch_results(batches))


def main():
    # Bail out early if the file is too large to process
    if not is_file_size_valid(FILE_PATH):
        print("file exceeds size limit")
        return None

    with open(FILE_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header_validation_results = validate_csv(reader.fieldnames)
        if not header_validation_results.valid:
            print(header_validation_results)
            return header_validation_results

        row_validation_results = validate_records(reader)
        preflight_summary = get_batch_summary(
            row_validation_results.valid_records,
            row_validation_results.failed_records,
            row_validation_results.errors,
        )
        print(preflight_summary)
        # Stop before submission if any row failed validation
        if not preflight_summary.batch_result:
            for error in row_validation_results.errors:
                print(f"Row {error.row}, {error.field} - {error.message}")
            return preflight_summary

        batch = process_valid_batch(row_validation_results.valid_records)
        print(batch)
        return batch


if __name__ == "__main__":
    main()