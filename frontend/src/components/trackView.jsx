import React, {useEffect, useState, useRef, useCallback}from 'react';
import { useRaceDataStore } from '../store/useRaceDataStore';

function TrackView() {

  const {flagStatus, currentLap, totalLaps } = useRaceDataStore(state => state.session);
  const drivers = useRaceDataStore(state => state.drivers);
  const trackMap = useRaceDataStore(state => state.trackMap);

  const setDrivers = useRaceDataStore(state => state.setDrivers);
  const setSessionStatus = useRaceDataStore(state => state.setSessionStatus);

  // animation variables
  const [isPlaying, setIsPlaying] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(5);

  const animationRef = useRef(null);  
  const startTimeRef = useRef(null); 
  const elapsedAtPauseRef = useRef(0);  

  // adding throttling in order to tackle memory leak
  // old method was sending 60 https request per second which caused memory leak  now we are make it 10 per second and also handling mempry leak 

  const lastFetchTimeREf = useRef(0); //this tracks when the last request was made
  const fetchInterval = 100;  //using this to fetch every 100ms
  const abortControllerRef = useRef(null); //used to cancel previous requests

  // ✅ ADD: Console log to see current drivers
  console.log("🎯 Current drivers in state:", drivers.length, drivers.map(d => ({id: d.id, x: d.x, y: d.y})));

  const fetchLivePositions = useCallback(async(time) => {
    const now  = Date.now();

    // throttling logic
    if (now - lastFetchTimeREf.current <fetchInterval) {
      return; //skips this current request if atleast 100ms has passed since last fetch
    }

    lastFetchTimeREf.current = now; //updates last fetch time 
    // request cancellation
    if (abortControllerRef.current) {
      abortControllerRef.current.abort(); // cancels previous request if it is still pending 
    }

    // creating new abort controller for this request 
    abortControllerRef.current = new AbortController()

    console.log("📡 Fetching positions for time:", time);  // ✅ ADD THIS
    
    try{
      const response = await fetch(`http://127.0.0.1:5000/api/race/live?elapsed=${time}`,{signal:abortControllerRef.current.signal});
      const data = await response.json();

      console.log("📡 Response received:", data.status, "Drivers:", data.drivers?.length);  // ✅ ADD THIS

      if (data.status === 'success' && data.drivers) {
        console.log("✅ Setting drivers:", data.drivers.map(d => ({id: d.id, x: d.x, y: d.y})));  // ✅ ADD THIS
        setDrivers(data.drivers);
        setSessionStatus({ currentLap: data.currentLap });
      }
    }catch(error){
      if (error.name !== 'AbortError') {
        console.error('❌ Error fetching live positions:', error);
      }
    }
  },[setDrivers, setSessionStatus]);

  useEffect(() => {
    console.log("🎬 Animation effect triggered. isPlaying:", isPlaying);  // ✅ ADD THIS
    
    if(isPlaying){
      const animate = (timestamp) => {
        if (!startTimeRef.current) {
          startTimeRef.current = timestamp;
          console.log("⏱️ Animation started at timestamp:", timestamp);  // ✅ ADD THIS
        }

        const elapsed = (timestamp - startTimeRef.current) / 1000;
        const raceTime = elapsedAtPauseRef.current + (elapsed * playbackSpeed);

        console.log("🔄 Animation frame - raceTime:", raceTime.toFixed(2));  // ✅ ADD THIS

        setElapsedTime(raceTime);
        fetchLivePositions(raceTime);
        
        if(raceTime < 4680){
          animationRef.current = requestAnimationFrame(animate);
        }else{
          setIsPlaying(false);
          console.log("🏁 Race has finished");
        }
      };
      animationRef.current = requestAnimationFrame(animate);
    }
    
    return () => {
      if (animationRef.current) {
        console.log("🛑 Cleaning up animation");  // ✅ ADD THIS
        cancelAnimationFrame(animationRef.current);
      }

      // cleaning pending requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [isPlaying, playbackSpeed, fetchLivePositions]);

  const togglePlay = () => {
    console.log("▶️ Toggle Play clicked. Current isPlaying:", isPlaying, "-> New:", !isPlaying);  // ✅ ADD THIS
    
    if (isPlaying) {
      // Save current race time when pausing
      elapsedAtPauseRef.current = elapsedTime;
    } else {

      startTimeRef.current = null; // Will be recalculated with offset
    }
    setIsPlaying(!isPlaying);
  };

  const resetAnimation = () => {
    console.log("⏮️ Reset clicked");  // ✅ ADD THIS
    setIsPlaying(false);
    setElapsedTime(0);
    startTimeRef.current = null;
    // resets trottle timer
    elapsedAtPauseRef.current = 0;

    // canceling any pending request 
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }    
    fetchLivePositions(0);

  };

  const changeSpeed = (newSpeed) => {
    console.log("⚡ Speed changed to:", newSpeed);  // ✅ ADD THIS
    
    const wasPlaying = isPlaying;
    if (wasPlaying) {
      setIsPlaying(false);
    }
    setPlaybackSpeed(newSpeed);
    if (wasPlaying) {
      setTimeout(() => {
        startTimeRef.current = null;
        // reset throttle timer
        lastFetchTimeREf.current = 0;
        setIsPlaying(true);
      }, 50);
    }
  };

  if (!trackMap || trackMap.svgPath === 0 ) {
    return <div style = {{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#666' }}>Loading Track Map...</div>
  }

  const flagColorMap = {
    'RED':'red',
    'YELLOW':"#FFD700",
    'SC':'orange',
    'VSC':'yellow',
    'GREEN': 'white',
  }
  
  const currentFlagStatus = flagColorMap[flagStatus] || 'white';
  const isWarningActive = flagStatus !== 'GREEN'

  const statusTextMap = {
    'RED': '🛑 RED FLAG',
    'YELLOW': '⚠️ YELLOW FLAG',
    'SC': 'SAFETY CAR',
    'VSC': 'VIRTUAL SAFETY CAR',
  }

  const indicatorText = statusTextMap[flagStatus] || `Status: ${flagStatus}`;
  
  const trackStyle = {
    width: '100%',
    height: '100%',
    backgroundColor: '#000000',
    display: 'flex',
    flexDirection: 'column',
    padding:'20px 30px',
    color: 'white',
    fontFamily:'sans-serif',
    overflow: 'hidden'
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds/60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${String(secs).padStart(2, '0')}`;
  }

  return (
    <div style={trackStyle}>
      <div style={{ flexShrink: 0 }}>
        <h1 style={{
          fontSize: '1.8em',
          margin: '0 0 10px 0',
          fontFamily: "'Rajdhani', sans-serif",
        }}>
          Gridlytic
        </h1>
        
        <div style={{ 
          padding: '5px 0 15px 0',
          fontSize: '0.9em', 
          display: 'flex', 
          alignItems: 'center',
          gap: '15px',
          flexWrap: 'wrap'
        }}>
          {isWarningActive && (
            <span style={{ 
              backgroundColor: '#FFD700',
              color: '#000', 
              padding: '4px 8px',
              borderRadius: '3px', 
              fontWeight: 'bold'
            }}>
              {indicatorText}
            </span>
          )}

          <span style={{ fontSize: '1.2em', fontWeight: 'bold' }}>
            Lap: {currentLap}/{totalLaps}
          </span>

          <span style={{ fontSize: '1em', color: '#888' }}>
            Race Time: {formatTime(elapsedTime)}
          </span>
        </div>

        <div style={{ 
          display: 'flex', 
          gap: '10px', 
          marginBottom: '15px',
          alignItems: 'center'
        }}>
          <button 
            onClick={togglePlay}
            style={{
              padding: '8px 16px',
              backgroundColor: isPlaying ? '#ff4444' : '#44ff44',
              border: 'none',
              borderRadius: '4px',
              color: '#000',
              fontWeight: 'bold',
              cursor: 'pointer',
              fontSize: '13px',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => e.target.style.opacity = '0.8'}
            onMouseOut={(e) => e.target.style.opacity = '1'}
          >
            {isPlaying ? '⏸ Pause' : '▶ Play'}
          </button>
          
          <button 
            onClick={resetAnimation}
            style={{
              padding: '8px 16px',
              backgroundColor: '#4444ff',
              border: 'none',
              borderRadius: '4px',
              color: '#fff',
              fontWeight: 'bold',
              cursor: 'pointer',
              fontSize: '13px',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => e.target.style.opacity = '0.8'}
            onMouseOut={(e) => e.target.style.opacity = '1'}
          >
            ⏮ Reset
          </button>

          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            marginLeft: '10px'
          }}>
            <span style={{ fontSize: '12px', color: '#aaa' }}>Speed:</span>
            {[1, 2, 5, 10, 20].map(speed => (
              <button
                key={speed}
                onClick={() => changeSpeed(speed)}
                style={{
                  padding: '6px 10px',
                  backgroundColor: playbackSpeed === speed ? '#666' : '#222',
                  border: playbackSpeed === speed ? '1px solid #888' : '1px solid #444',
                  borderRadius: '3px',
                  color: playbackSpeed === speed ? '#fff' : '#aaa',
                  cursor: 'pointer',
                  fontSize: '11px',
                  transition: 'all 0.2s'
                }}
              >
                {speed}x
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: 0,
        padding: '10px 0'
      }}>
        <svg
          viewBox={trackMap.viewBox}
          style={{ 
            width: '100%',
            height: '100%',
            maxHeight: '100%'
          }}
          preserveAspectRatio="xMidYMid meet"
        >
          <path
            d={trackMap.svgPath}
            fill="none"
            stroke={currentFlagStatus}
            strokeWidth="15"
            strokeLinejoin="round"
            strokeLinecap="round"
            style={{ transition: 'stroke 0.5s ease' }}
          />
          
          {drivers.map((driver) => (
            <g key={driver.id}>
            <circle
              cx={0}
              cy={0}
              r="12"
              fill={driver.teamcolor}
              stroke="white"
              strokeWidth="2"
              style={{ transform: `translate(${driver.x}px, ${driver.y}px)`, transition: 'transform 0.1s linear' }}
            />
              
              <text
                x={0}
                y={ -18}
                fill="white"
                fontSize="13"
                fontWeight="bold"
                textAnchor="middle"
                style={{ transform: `translate(${driver.x}px, ${driver.y}px)`, transition: 'transform 0.1s linear' }}

              >
                {driver.driverName}
              </text>
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
}

export default TrackView;