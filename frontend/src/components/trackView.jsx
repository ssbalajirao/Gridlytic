import React from 'react';
import { useRaceDataStore } from '../store/useRaceDataStore';

function TrackView() {

  const {flagStatus, currentLap, totalLaps } = useRaceDataStore(state => state.session);
  const trackSvgPath = useRaceDataStore(state => state.track.svgPath);
  const drivers = useRaceDataStore(state => state.drivers);
  const trackMap = useRaceDataStore(state => state.trackMap);

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
    height: '100vh',
    backgroundColor: '#000000',
    display: 'flex',
    flexDirection: 'row',
    padding:'20px 30px',
    color: 'white',
    fontFamily:'sans-serif',
    overflow: 'hidden'
  };
  return (
    <div style={trackStyle}>
      {/* mainTitle */}
      <h1 style={{
        fontSize:'1.8em',
        margin:'0 0 10px 0',
        fontFamily: "'Rajdhani', sans-serif",
      }}>
        Gridlytic
      </h1>
      {/* lap count and race status indicator */}
      <div style={{padding: '5px 0 20px 0', fontSize: '0.9em', display: 'flex', alignItems: 'center'}}>
        {/* Race status indicator */}
        {isWarningActive && (
          <span style={{ 
              backgroundColor: '#FFD700', // Yellow color for caution
              color: '#000', 
              padding: '2px 5px', 
              borderRadius: '3px', 
              fontWeight: 'bold', 
              marginRight: '15px' 
          }}>
            {indicatorText} {/* dynamic warning texts*/ }
          </span>
        )}

        {/* Lap count */}
        <span style={{fontSize:'1.2em',fontWeight:'bold' }}>
          Lap: {currentLap}/{totalLaps} 
        </span>
      </div>

      {/* 3. TRACK OUTLINE PLACEHOLDER (Grows to fill container) */}
      <div style={{
        flex: 1,              // Take up all remaining space
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100%',
        padding: '20px'
      }}>
        {/* track map */}
        <svg
          viewBox={trackMap.viewBox} // THIS IS THE MAGIC LINE
          style={{ width: 'auto', height: '95%' }}
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Path test */}
        <path
            d={trackMap.svgPath}
            fill="none"
            stroke={currentFlagStatus}
            strokeWidth="15"
            strokeLinejoin="round"
            strokeLinecap="round"
            style={{ transition: 'stroke 0.5s ease'}}
          />
          {/* Driver dots */}
          {drivers.map((driver) =>(
            <g key = {driver.id}>
              <circle
                cx = {driver.x}
                cy = {driver.y}
                r = "12"
                fill = {driver.teamcolor}
                stroke = "width"
                strokeWidth="2"
                style = {{transition: 'all 0.5s linear'}}/>
                
                <text
                  x={driver.x}
                  y={driver.y - 18} // Position name slightly above the dot
                  fill="white"
                  fontSize="14"
                  fontWeight="bold"
                  textAnchor="middle"
                  style={{ transition: 'all 0.5s linear', pointerEvents: 'none' }}
                >
                  {driver.driverName}
                </text>
              </g>
          ))}
          {/* <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle" fill={currentFlagStatus}>
            track Outline over here
          </text> */}

        </svg>
      </div>
    </div>
  );
}

export default TrackView;