import React, { useEffect, useState } from 'react';
import axios from 'axios';
import RacePage from './pages/racePage';
import { useRaceDataStore } from './store/useRaceDataStore';

function App() {
  const [backendMessage, setBackendMessage] = useState('Checking backend status...'); //initial message is stored in backendMessage variable and then when set message is called it changes the variable on successfull connection with the server
  const [backendReady, setBackendReady] = useState(false);
  const setDrivers = useRaceDataStore((state) => state.setDrivers);
  const setSessionStatus = useRaceDataStore((state) => state.setSessionStatus);
  const setTrackMap = useRaceDataStore((state) => state.setTrackMap);

  // new changes 2/12/25
  useEffect(() => {
    // 1. Define the URL for your Flask backend
    // Note: Flask runs on port 5000 by default.
    const API_URL = 'http://localhost:5000/api/test';

    // 2. Make the GET request using axios and writing a function to get race data 
    const fetcchRaceData = () =>{
      axios.get(API_URL)
      .then((response) =>{
        if (response.data.status === "success") {
          // updating the store with  the f1 race data received from the backend
          setDrivers(response.data.drivers);
          setSessionStatus(response.data.session);
          if (response.data.track_map) {
            setTrackMap(response.data.track_map)
          }
          setBackendMessage(`Monitoring: ${response.data.session.trackName}`);
          setBackendReady(true);
        }
      })
      .catch((error) => {
        console.error('Error connecting to the backend:', error);
        setBackendMessage('Error: Unable to connect to the backend.');
        setBackendReady(false);
      } );
    };
    // initiallsing  and 5 second pulse 
    fetcchRaceData(); // Initial fetch when component mounts
    const intervalId = setInterval(fetcchRaceData, 15000); // Fetch every 5 seconds

    return () => clearInterval(intervalId); // Cleanup on unmount this prevents memory leak

  }, [setDrivers, setSessionStatus, setTrackMap]); // Empty dependency array ensures this runs only once

  // we are passing the backend status as props to display the back end status on the race page it self
  return (
    <RacePage
      isBackendReady={backendReady}
      backendMessage={backendMessage}
    />
  );
}

export default App;