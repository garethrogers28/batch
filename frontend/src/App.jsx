// Import this component's styles and React's state hook.
import "./App.css";
import { useState } from "react";

// A component is a function that describes part of the interface.
function App() {
  // State is remembered between renders and updated using its setter.
  const [selectedFile, setSelectedFile] = useState(null);
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [missingFields, setMissingFields] = useState([]);

  // React calls this handler when the file input changes.
  function handleFileChange(event) {
    // Save the first selected file and clear feedback from the previous file.
    setSelectedFile(event.target.files[0]);
    setResults(null);
    setApiError(null);
    setMissingFields([]);
  }

  // async lets this handler use await while the backend responds.
  async function handleValidate() {
    // Clear previous errors before a new validation attempt.
    setMissingFields([]);
    setApiError(null);
    // Stop immediately if no file is selected.
    if (!selectedFile) return;

    // Show that validation is in progress.
    setIsLoading(true);

    // FormData holds the file under "file", the field expected by the backend.
    const formData = new FormData();
    formData.append("file", selectedFile);

    // Send the file and handle the response or any request errors.
    try {
      const response = await fetch("http://127.0.0.1:8000/validate", {
        method: "POST",
        body: formData,
      });
      // Throw an error for an unsuccessful HTTP response.
      if (!response.ok) throw new Error("Request Failed");

      // Read the JSON response into a JavaScript value.
      const data = await response.json();
      // Save missing headers separately instead of treating them as results.
      if (data.valid === false) {
        setMissingFields(data.missing_fields);
        return;
      }
      // Save the validation results for display.
      setResults(data);
    } catch (error) {
      // Store request or response errors for the UI.
      setApiError(error);
    } finally {
      // Stop loading whether the request succeeded or failed.
      setIsLoading(false);
    }
  }

  // JSX describes what React should display. Curly braces embed JavaScript.
  return (
    <main>
      <h1>Bank Account Batch Validator</h1>
      <p>Upload a CSV file to check your customer records.</p>

      {/* htmlFor connects the label to the input with this id. */}
      <label htmlFor="csv-file">Choose a CSV file</label>
      {/* The input suggests CSV files and calls the handler when it changes. */}
      <input
        id="csv-file"
        type="file"
        accept=".csv"
        onChange={handleFileChange}
      />

      {/* && renders the paragraph only when a file has been selected. */}
      {selectedFile && <p>{selectedFile.name}</p>}

      {/* ! means "not": disable the button when no file is selected. */}
      <button disabled={!selectedFile} onClick={handleValidate} type="button">
        Validate file
      </button>

      {/* Show a message while validation is in progress. */}
      {isLoading && <p>Validating...</p>}

      {/* Show a friendly message if the request fails. */}
      {apiError && <p>Validation failed. Please try again</p>}

      {/* Show missing headers as a comma-separated list. */}
      {missingFields.length > 0 && (
        <p>Missing Headers: {missingFields.join(", ")}</p>
      )}

      {/* Show the backend's summary only once results are available. */}
      {results && <p>Total Records: {results.summary.total_records}</p>}
      {results && <p>Valid Records: {results.summary.valid_records}</p>}
      {results && <p>Failed Records: {results.summary.failed_records}</p>}

      {/* === compares the failed-record count with zero. */}
      {results && results.summary.failed_records === 0 && (
        <p>No Validation Errors Found</p>
      )}

      {/* map creates a paragraph for each error; key helps React track items. */}
      {results &&
        results.validation.errors.map((error) => (
          <p key={error.row + "-" + error.field}>
            Row {error.row}: {error.field}{" "}
            {/* Remove this prefix from the displayed message. */}
            {error.message.replace("Value error, ", "")}
          </p>
        ))}
    </main>
  );
}

// Make App available for main.jsx to import and render.
export default App;
