import "./App.css";

function App() {
  return (
    <main>
      <h1>Bank Account Batch Validator</h1>
      <p>Upload a CSV file to check your customer records.</p>

      <label htmlFor="csv-file">Choose a CSV file</label>
      <input id="csv-file" type="file" accept=".csv" />

      <button type="button">Validate file</button>
    </main>
  );
}

export default App;
