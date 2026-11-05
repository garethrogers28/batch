import "./App.css";
import { useState } from "react";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [results, setResults] = useState(null);
  function handleFileChange(event) {
    setSelectedFile(event.target.files[0]);
  }
  async function handleValidate() {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append("file", selectedFile);
    const response = await fetch("http://127.0.0.1:8000/validate", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    setResults(data);
    console.log(data);
  }
  return (
    <main>
      <h1>Bank Account Batch Validator</h1>
      <p>Upload a CSV file to check your customer records.</p>

      <label htmlFor="csv-file">Choose a CSV file</label>
      <input
        id="csv-file"
        type="file"
        accept=".csv"
        onChange={handleFileChange}
      />
      {selectedFile && <p>{selectedFile.name}</p>}
      <button onClick={handleValidate} type="button">
        Validate file
      </button>
      {results && <p>Total Records: {results.summary.total_records}</p>}
      {results && <p>Valid Records: {results.summary.valid_records}</p>}
      {results && <p>Failed Records: {results.summary.failed_records}</p>}
      {results &&
        results.validation.errors.map((error) => (
          <p key={error.row + "-" + error.field}>
            Row {error.row}: {error.message} {error.field}
          </p>
        ))}
    </main>
  );
}

export default App;
