import React, { useEffect, useState } from 'react';
import axios from 'axios';

function App() {
  const [backendMessage, setBackendMessage] = useState('Checking backend status...'); //initial message is stored in backendMessage variable and then when set message is called it changes the variable on successfull connection with the server
// new changes 2/12/25
  useEffect(() => {
    // 1. Define the URL for your Flask backend
    // Note: Flask runs on port 5000 by default.
    const API_URL = 'http://localhost:5000/api/test';

    // 2. Make the GET request using axios
    axios.get(API_URL)
      .then(response => {
        // 3. Success! Update the state with the message from Python
        console.log('Backend response data:', response.data); 
        setBackendMessage(`Backend Status: ✅ Success! Message: "${response.data.message}"`);
      })
      .catch(error => {
        // 4. Handle any errors (e.g., server not running, CORS issue)
        console.error('Error calling backend API:', error);
        setBackendMessage('Backend Status: ❌ Failed to connect. Check if Python server is running.');
      });
  }, []); // Empty dependency array ensures this runs only once

  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>F1 Project Frontend</h1>
      <p style={{ fontSize: '1.2em', fontWeight: 'bold' }}>{backendMessage}</p>
      <p>Your backend is on **http://localhost:5000** and your frontend is on **http://localhost:3000**.</p>
    </div>
  );
}

export default App;