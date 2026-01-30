import React, {useEffect, useState, useRef}from 'react';
import { useRaceDataStore } from '../store/useRaceDataStore';

function TrackView() {

  const {flagStatus, currentLap, totalLaps } = useRaceDataStore(state => state.session);
  // const trackSvgPath = useRaceDataStore(state => state.track.svgPath);
  const drivers = useRaceDataStore(state => state.drivers);
  const trackMap = useRaceDataStore(state => state.trackMap);

  const setDrivers = useRaceDataStore(state => state.setDrivers); //to update driver positions
  const setSessionStatus = useRaceDataStore(state => state.setSessionStatus); //to update lapcount

  // animation variables

  const [isPlaying, setIsPlaying] = useState(false); //play pause
  const [elapsedTime, setElapsedTime] = useState(0); //current race time
  const [playbackSpeed, setPlaybackSpeed] = useState(5); //speed multiplier

// function to fetch live race from backend
    const animationRef = useRef(null);  
    const startTimeRef = useRef(null); 
  const fetchLivePositions = async(time) =>{

    try{
      const response = await fetch(`http://127.0.0.1:5000/api/race/live?elapsed=${time}`);
      const data = await response.json();

      if (data.status === 'success' && data.drivers) {
        setDrivers(data.drivers); //setting driver positions
        setSessionStatus({ currentLap: data.currentLap });
      }
    }catch(error){
      console.error('Error fetching live positions:', error);
    }
  }


// actually animating through animation frame

  useEffect(() =>{
    // it calculates elapsed time continously 
    if(isPlaying){
      const animate  = (timestamp) => {
        if (!startTimeRef.current) {
          startTimeRef.current = timestamp;

        }

        const elapsed  = (timestamp - startTimeRef.current) / 1000;

        const raceTime =  elapsed * playbackSpeed;

        setElapsedTime(raceTime);
        fetchLivePositions(raceTime);
        if(raceTime < 4680){
          animationRef.current = requestAnimationFrame(animate);
        }else{
          setIsPlaying(false);
          console.log("Race has finished");
        }
      };
      animationRef.current = requestAnimationFrame(animate);

    }
    return () =>{
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);

      }
    };
  }, [isPlaying, playbackSpeed]);

  const togglePlay = () => {
    if (!isPlaying) {
      startTimeRef.current = null;
    }
    setIsPlaying(!isPlaying);
  };

// function to reset animation to start 

  const resetAnimation = () =>{
    setIsPlaying(false);
    setElapsedTime(0);
    startTimeRef.current = null;
    fetchLivePositions(0);

  };

  // function to change Speed of playback

  const changeSpeed = (newSpeed) =>{

    const wasPlaying  = isPlaying;
    if (wasPlaying) {
      setIsPlaying(false);

    }
    setPlaybackSpeed(newSpeed);
    if (wasPlaying) {
      setTimeout(() =>{
        startTimeRef.current = null;
        setIsPlaying(true);

      },50)
    }
  };
  // math to generate track map
  if (!trackMap || trackMap.svgPath === 0 ) {
    return <div style = {{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#666' }}>Loading Track Map...</div>
  }

  // // finding the min max values
  // const xValues = trackMap.map(p=> p.x);
  // const yValues = trackMap.map(p=> p.y);

  // const minX = Math.min(...xValues);
  // const maxX = Math.max(...xValues);
  // const minY = Math.min(...yValues);
  // const maxY = Math.max(...yValues);

  // const padding = 500;
  // const width = (maxX - minX) + (padding * 2);
  // const height = (maxY - minY) + (padding *2);   
  // const viewBox = `${minX - padding} ${minY - padding} ${width} ${height}`;

  // // creating Path to show on front end
  // const pathData = trackMap.map((point, index) =>{
  //   return `${index === 0 ? 'M':'L'} ${point.x} ${point.y}`;
  // }).join(' ');

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
    height: '100%', //may need to change it later to 100vh
    backgroundColor: '#000000',
    display: 'flex',
    flexDirection: 'column', //change to row if it doesnt work and loosk bad
    padding:'20px 30px',
    color: 'white',
    fontFamily:'sans-serif',
    overflow: 'hidden'
  };

  const formatTime = (seconds) =>{
    const mins = Math.floor(seconds/60);
    const secs = Math.floor(seconds %60);
    return `${mins}:${String(secs).padStart(2, '0')}`;

  }
  return (
    <div style={trackStyle}>
      {/* ========== NEW: Wrapped header in container with flexShrink ========== */}
      <div style={{ flexShrink: 0 }}> {/* ← NEW: Prevents header from shrinking */}
        
        {/* ========== ORIGINAL: Main Title (no changes) ========== */}
        <h1 style={{
          fontSize: '1.8em',
          margin: '0 0 10px 0',
          fontFamily: "'Rajdhani', sans-serif",
        }}>
          Gridlytic
        </h1>
        {/* ======================================================= */}
        
        {/* ========== CHANGE: Modified status bar with new elements ========== */}
        <div style={{ 
          padding: '5px 0 15px 0',  // ← CHANGE: Reduced bottom padding from 20px to 15px
          fontSize: '0.9em', 
          display: 'flex', 
          alignItems: 'center',
          gap: '15px',  // ← NEW: Added gap between elements
          flexWrap: 'wrap'  // ← NEW: Allow wrapping on small screens
        }}>
          {/* Race status indicator (unchanged) */}
          {isWarningActive && (
            <span style={{ 
              backgroundColor: '#FFD700',
              color: '#000', 
              padding: '4px 8px',  // ← CHANGE: Increased padding slightly
              borderRadius: '3px', 
              fontWeight: 'bold'
            }}>
              {indicatorText}
            </span>
          )}

          {/* Lap count (unchanged) */}
          <span style={{ fontSize: '1.2em', fontWeight: 'bold' }}>
            Lap: {currentLap}/{totalLaps}
          </span>

          {/* ========== NEW: Race time display ========== */}
          <span style={{ fontSize: '1em', color: '#888' }}>
            Race Time: {formatTime(elapsedTime)}
          </span>
          {/* ============================================ */}
        </div>
        {/* =================================================================== */}

        {/* ========== NEW: Playback Controls Section ========== */}
        <div style={{ 
          display: 'flex', 
          gap: '10px', 
          marginBottom: '15px',
          alignItems: 'center'
        }}>
          {/* ========== NEW: Play/Pause Button ========== */}
          <button 
            onClick={togglePlay}
            style={{
              padding: '8px 16px',
              backgroundColor: isPlaying ? '#ff4444' : '#44ff44', // Red when playing, green when paused
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
          {/* =========================================== */}
          
          {/* ========== NEW: Reset Button ========== */}
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
          {/* ======================================= */}

          {/* ========== NEW: Speed Control Buttons ========== */}
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
                  backgroundColor: playbackSpeed === speed ? '#666' : '#222', // Highlight current speed
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
          {/* =============================================== */}
        </div>
        {/* =================================================== */}
      </div>
      {/* ===================================================================== */}

      {/* ========== CHANGE: Modified track container for better layout ========== */}
      <div style={{
        flex: 1,  // ← ORIGINAL: Take remaining space
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: 0,  // ← NEW: Prevent flex item from exceeding container
        padding: '10px 0'  // ← CHANGE: Reduced from 20px to 10px
      }}>
        {/* ========== CHANGE: Modified SVG styling ========== */}
        <svg
          viewBox={trackMap.viewBox}
          style={{ 
            width: '100%',  // ← CHANGE: Changed from 'auto' to '100%'
            height: '100%',  // ← CHANGE: Changed from '95%' to '100%'
            maxHeight: '100%'  // ← NEW: Prevent overflow
          }}
          preserveAspectRatio="xMidYMid meet"
        >
          {/* ========== ORIGINAL: Track outline path (no changes) ========== */}
          <path
            d={trackMap.svgPath}
            fill="none"
            stroke={currentFlagStatus}
            strokeWidth="15"
            strokeLinejoin="round"
            strokeLinecap="round"
            style={{ transition: 'stroke 0.5s ease' }}
          />
          {/* =============================================================== */}
          
          {/* ========== CHANGE: Modified driver dots with animation support ========== */}
          {drivers.map((driver) => (
            <g key={driver.id}>
              <circle
                cx={driver.x}  // ← These update via Zustand when fetchLivePositions runs
                cy={driver.y}
                r="12"
                fill={driver.teamcolor}
                stroke="white"
                strokeWidth="2"
                style={{ 
                  transition: 'cx 0.3s linear, cy 0.3s linear',  // ← NEW: Smooth position transitions
                  cursor: 'pointer'  // ← NEW: Show it's interactive
                }}
              />
              
              <text
                x={driver.x}
                y={driver.y - 18}
                fill="white"
                fontSize="13"  // ← CHANGE: Reduced from 14 to 13
                fontWeight="bold"
                textAnchor="middle"
                style={{ 
                  transition: 'x 0.3s linear, y 0.3s linear',  // ← NEW: Smooth text transitions
                  pointerEvents: 'none',
                  textShadow: '1px 1px 2px rgba(0,0,0,0.8)'  // ← NEW: Added shadow for readability
                }}
              >
                {driver.driverName}
              </text>
            </g>
          ))}
          {/* ========================================================================= */}
        </svg>
      </div>
      {/* ======================================================================= */}
    </div>
  );
}

export default TrackView;