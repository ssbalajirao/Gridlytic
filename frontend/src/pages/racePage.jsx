//Importing react and importing all the components in our race page 
import React from "react";
import TrackView from "../components/trackView";
import DriverList from "../components/driverList";
import SessionInfo from "../components/sessionInfo";

// Race page function
//getting props from app.js to display the backend
function RacePage ({isBackendReady, backendMessage}) {
// Styling the Race page 
    const containerStyle = {
        display: 'flex',
        flexDirection:'column',
        height: '100vh',
        margin: 0, 
        backgroundColor: '#000000',
        fontFamily: "'Inter', sans-serif",
    };

    const topSectionStyle = {
        display: 'flex',
        flexGrow: 1,
    };

    const trackViewStyle = {
        flex: 4,
        borderRight: '1px solid #111'
    };

    const driverListStyle = {
        flex: 1,
    };

    return (
         
        <div style={containerStyle}>
            {/* Only display if back end is not ready */}
            {!isBackendReady &&(
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left:0,
                    right:0,
                    bottom:0,
                    backgroundColor: 'rgba(0,0,0,0.95)',
                    color: 'white',
                    zIndex: 100,
                    display: 'flex',
                    flexDirection:'column',
                    justifyContent:'center',
                    alignItems:'center',
                    textAlign:'center',
                }}>
                    <h1 style={{ color: backendMessage.includes('❌') ? 'red' : 'yellow', fontSize: '2em' }}>
                        SYSTEM STATUS
                    </h1>
                    <p style={{ fontSize: '1.5em', fontWeight: 'bold', maxWidth: '80%' }}>
                        {backendMessage}
                    </p>
                    <p style={{ color: '#888' }}>
                        Please check your Python server terminal.
                    </p>
                </div>
            )}
            {/* TOP SECTION (Horizontal Split: TrackView + DriverList) */}
            <div style={topSectionStyle}>
                <div style={trackViewStyle}>
                    {/* Left Column (80%) */}
                    <TrackView />
                </div>

                <div style={driverListStyle}>
                    {/* Right Column (20%) */}
                    <DriverList />
                </div>
            </div>
            {/* BOTTOM SECTION (SessionInfo) */}
            <SessionInfo />
        </div>
    );
}
export default RacePage;