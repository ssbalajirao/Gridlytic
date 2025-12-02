import React from 'react';

function SessionInfo({componentStyle}) {
  const infoStyle = {
    backgroundColor: '#000000', 
    color: 'white',
    padding: '20px 30px',
    borderTop: '1px solid #444', // Divider line
    fontSize: '0.9em',
    fontFamily: 'sans-serif',
  };
  return (
// Merge the received style prop with the component's internal style
    <div style={{ ...infoStyle, ...componentStyle }}>
      
      {/* 1. Header Line */}
      <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>IF POSITION IS MAINTAINED</p>
      
      {/* 2. Points Breakdown Line */}
      <p style={{ margin: 0, color: '#ccc' }}>
        1st: Max +25 pts &nbsp;&nbsp;&nbsp; 2nd: Sainz +18 pts &nbsp;&nbsp;&nbsp; 3rd: Oscar +15 pts
      </p>
      
    </div>
  );
}

export default SessionInfo;