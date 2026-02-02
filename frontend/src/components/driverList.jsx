import React from 'react';
import { useRaceDataStore } from '../store/useRaceDataStore';

// getting the data through pi now 
// const DUMMY_DRIVERS = [
//   { pos: 1, name: 'Max', tyre: 'H', gap: '+0.000' },
//   { pos: 2, name: 'Sainz', tyre: 'M', gap: '+2.500' },
//   { pos: 3, name: 'Oscar', tyre: 'H', gap: '+1.200' },
//   { pos: 4, name: 'Driver 4', tyre: 'S', gap: '+5.000' },
// ];

function DriverList() {
  // calling global state
  const drivers  = useRaceDataStore((state) => state.drivers);

  // my take rn: gets the data from the store which gets the drivers state
  const sortedDriver = [...drivers].sort((a,b) => a.position - b.position);

  const listStyle = {
    backgroundColor: '#000000',
    color: 'white',
    padding: '5px 15px',
    height: '100%',
    overflow: 'hidden',
    fontFamily:'sans-serif',
    boxSizing: 'border-box',
  };
  const tableStyle = {
    width: '100%',
    borderCollapse: 'collapse', // Ensures borders look sharp
    fontSize: '0.75em',
    textAlign: 'left',
    lineHeight: '1.1'
  };

  const thStyle = {
    borderBottom: '2px solid #555',
    padding: '4px 2px',
    fontWeight: 'normal',
    color: '#aaa',
    position: 'sticky',
    top: 0,
    backgroundColor: '#000',
    zIndex: 1
  };
  const tdStyle = {
    padding: '10px 5px',
    borderBottom: '1px solid #222', // Subtle gray line below each row
  };
  return (
    <div style = {listStyle}>
      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle}>Pos</th>
            <th style={thStyle}>Name</th>
            <th style={thStyle}>Gap</th>
            <th style={thStyle}>Tyre</th>
          </tr>
        </thead>
        {/* table body currently a dummy later will be filled duynamically */}

        <tbody>
          {sortedDriver.map((driver) => (
            <tr key={driver.id}>
              <td style={tdStyle}>{driver.position}</td>
              <td style={{ ...tdStyle, display: 'flex', alignItems: 'center' }}>
                {/* 4. Display the Team Color Bar from Python */}
                <div style={{ 
                  width: '4px', 
                  height: '18px', 
                  backgroundColor: driver.teamcolor, 
                  marginRight: '10px' 
                }}></div>
                {driver.driverName}
              </td>
              <td style={tdStyle}>{driver.gapToLeader}</td>
              <td style={tdStyle}>
                <span style={{ border: '1px solid #777', padding: '2px 6px', borderRadius: '50%', fontSize: '0.7em' }}>
                    {driver.tireCompound[0]}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DriverList;