import React from 'react';

function TrackView() {
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
        <span style={{ 
              backgroundColor: '#FFD700', // Yellow color for caution
              color: '#000', 
              padding: '2px 5px', 
              borderRadius: '3px', 
              fontWeight: 'bold', 
              marginRight: '15px' 
          }}>
              🚥 IF VSC
          </span>
        {/* Lap count */}
        <span style={{fontSize:'1.2em',fontWeight:'bold' }}>
          LAP: 11/39  
        </span>
      </div>

      {/* 3. TRACK OUTLINE PLACEHOLDER (Grows to fill container) */}
      <div style={{
        flexGrow: 1,
        border: '2px dashed white',
        display: 'flex',
        justifyContent:'center',
        alignItems:'center',
        marginTop:'10px 0',
        fontSize:'1.5em',
      }}>
        Track Outline will be over Here
      </div>
    </div>
  );
}

export default TrackView;