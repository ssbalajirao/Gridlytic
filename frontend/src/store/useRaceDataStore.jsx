import {create} from 'zustand';

const initialState = {
    // session metaData
    session:{
        currentLap: 1,
        totalLaps: 70,
        flagSTatus: 'GREEN',
        trackName: 'Monza',
        sessionName: 'Race',
        pointProjection: {"1st": "Max +25", "2nd": "Sainz +18", "3rd": "Oscar +15"},
    },

    // Driver Data Array
    drivers: [
        { id: 'VER', position: 1, driverName: 'Max', gapToLeader: '+0.000', interval: '+0.000', teamColor: '#0600EF', tireCompound: 'HARD', lapPercentage: 0.85 },
        { id: 'HAM', position: 2, driverName: 'Lewis', gapToLeader: '+3.500', interval: '+3.500', teamColor: '#00D2BE', tireCompound: 'MEDIUM', lapPercentage: 0.70 }
    ],

    // Track Layout Data
    track: {
        svgPath: '',
        pitEntryPercentage: 0.90,
    },

    // Utility Status
    loading: false,
    error: null,
};


// defining STore

export const useRaceDataStore = create((set) => ({
    // initializing initial state
    ...initialState,

        // Action to set the loading status
    setLoading: (isLoading) => set({ loading: isLoading }),

    // Action to update the entire driver array
    setDrivers: (newDriversArray) => set({ drivers: newDriversArray }),

    // Action to update the session metadata (e.g., current flag status)
    setSessionStatus: (newStatus) => set((state) => ({ 
        session: { ...state.session, ...newStatus } 
    })),

    // Action to reset the store back to its initial state
    resetState: () => set(initialState),

}))