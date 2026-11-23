// Import this component's styles and React's state hook.
import "./App.css";
import { useState } from "react";

// A component is a function that describes part of the interface.
function App() {
  // State is remembered between renders. Each setter updates its value and
  // tells React to render again; null means there is no file or result yet.
  const [selectedFile, setSelectedFile] = useState(null);
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState(null);

  // React calls this handler when the file input changes.
  function handleFileChange(event) {
    // The input's files list contains the selected files; [0] gets the first.
    setSelectedFile(event.target.files[0]);
    setResults(null);
    setApiError(null);
  }

  // async lets this handler use await while the backend responds.
  async function handleValidate() {
    // Stop immediately if no file is selected.
    if (!selectedFile) return;

    // set loading as true
    setIsLoading(true);

    // FormData holds the file under "file", the field expected by the backend.
    const formData = new FormData();
    formData.append("file", selectedFile);

    // Send the form data to the backend and wait for its response. catch errors
    try {
      const response = await fetch("http://127.0.0.1:8000/validate", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      setApiError(error);
      console.log(error);
    } finally {
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

      {/*add error message*/}
      {apiError && <p>Validation failed. Please try again</p>}

      {/* added loading state*/}
      {isLoading && <p>Validating...</p>}

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
