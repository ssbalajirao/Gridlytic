import React from 'react';
import { useRaceDataStore } from '../store/useRaceDataStore';

function TrackView() {

  const {flagStatus, currentLap, totalLaps } = useRaceDataStore(state => state.session);
  const trackSvgPath = useRaceDataStore(state => state.track.svgPath);
  const drivers = useRaceDataStore(state => state.drivers);

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
  };
  return (
    <div style={{trackStyle}}>
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
        flexGrow: 1,
        // border: '2px dashed white',
        display: 'flex',
        justifyContent:'center',
        alignItems:'center',
        marginTop:'10px 0',
        fontSize:'1.5em',
      }}>
        {/* track map */}
        <svg
          width="80%"
          height="80%"
          style={{border:`2px solid ${currentFlagStatus}`, color: currentFlagStatus}}  
        >
          <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle" fill={currentFlagStatus}>
            track Outline over here
          </text>

        </svg>
      </div>
    </div>
  );
}

export default TrackView;