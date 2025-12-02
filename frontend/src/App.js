import React, { useEffect, useState } from 'react';
import axios from 'axios';
import RacePage from './pages/racePage';

function App() {
  const [backendMessage, setBackendMessage] = useState('Checking backend status...'); //initial message is stored in backendMessage variable and then when set message is called it changes the variable on successfull connection with the server
  const [backendReady, setBackendReady] = useState(false);
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
        setBackendReady(true);
      })
      .catch(error => {
        // 4. Handle any errors (e.g., server not running, CORS issue)
        console.error('Error calling backend API:', error);
        setBackendMessage('Backend Status: ❌ Failed to connect. Check if Python server is running.');
        setBackendReady(false);
      });
  }, []); // Empty dependency array ensures this runs only once

  // we are passing the backend status as props to display the back end status on the race page it self
  return (
    <RacePage
      isBackendReady={backendReady}
      backendMessage={backendMessage}
    />
  );
}

export default App;