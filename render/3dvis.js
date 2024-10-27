import React, { useState, useEffect } from 'react';

// Constants for visualization
const DistanceType = {
    OUT_OF_DISTANCE: "Out of Distance",
    LONG: "Long Distance",
    MEDIUM: "Medium Distance",
    LUNGE: "Lunge Distance",
    SHORT: "Short Distance",
    INFIGHTING: "Infighting"
};

const FencingVisualizer = () => {
    const [boutState, setBoutState] = useState({
        distance: 'MEDIUM',
        fencer1: { name: '', score: 0, blade_position: '', has_priority: false },
        fencer2: { name: '', score: 0, blade_position: '', has_priority: false },
        current_action: null,
        rounds: 0
    });
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        // Connect to WebSocket server
        const ws = new WebSocket('ws://localhost:8765');

        ws.onopen = () => {
            console.log('Connected to fencing simulator');
            setConnected(true);
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setBoutState(data);
        };

        ws.onclose = () => {
            console.log('Disconnected from fencing simulator');
            setConnected(false);
        };

        return () => ws.close();
    }, []);

    // Calculate fencer positions based on distance
    const getFencerPositions = () => {
        const distanceMap = {
            OUT_OF_DISTANCE: 600,
            LONG: 500,
            MEDIUM: 400,
            LUNGE: 300,
            SHORT: 200,
            INFIGHTING: 100
        };
        const spacing = distanceMap[boutState.distance] || 400;
        return spacing;
    };

    return (
        <div className="w-full min-h-screen bg-gray-900 p-4">
            <div className="max-w-4xl mx-auto bg-gray-800 rounded-lg p-6">
                {/* Connection Status */}
                <div className={`text-sm mb-4 ${connected ? 'text-green-500' : 'text-red-500'}`}>
                    {connected ? 'Connected to simulator' : 'Disconnected'}
                </div>

                {/* Score Display */}
                <div className="flex justify-between mb-6">
                    <div className="text-blue-400">
                        {boutState.fencer1.name}: {boutState.fencer1.score}
                        {boutState.fencer1.has_priority && ' (Priority)'}
                    </div>
                    <div className="text-red-400">
                        {boutState.fencer2.name}: {boutState.fencer2.score}
                        {boutState.fencer2.has_priority && ' (Priority)'}
                    </div>
                </div>

                {/* Piste Visualization */}
                <div className="relative w-full h-64 bg-gray-700 rounded-lg mb-6">
                    <svg viewBox="0 0 800 200" className="w-full h-full">
                        {/* Piste */}
                        <rect x="100" y="120" width="600" height="20" fill="#475569" />
                        
                        {/* Center line */}
                        <line x1="400" y1="110" x2="400" y2="150" stroke="#94a3b8" strokeWidth="2" />

                        {/* Fencers */}
                        <g transform={`translate(${400 - getFencerPositions()/2}, 130)`}>
                            <rect width="20" height="60" fill="#3b82f6" />
                            <line x1="20" y1="30" x2="70" y2="30" stroke="#3b82f6" strokeWidth="4" />
                        </g>
                        <g transform={`translate(${400 + getFencerPositions()/2 - 20}, 130)`}>
                            <rect width="20" height="60" fill="#ef4444" />
                            <line x1="0" y1="30" x2="-50" y2="30" stroke="#ef4444" strokeWidth="4" />
                        </g>
                    </svg>
                </div>

                {/* Current Action & Round */}
                <div className="text-center text-gray-300 mb-4">
                    <div>Round: {boutState.rounds}</div>
                    {boutState.current_action && (
                        <div>Current Action: {boutState.current_action}</div>
                    )}
                </div>

                {/* Distance Indicator */}
                <div className="text-center text-gray-400">
                    Distance: {DistanceType[boutState.distance]}
                </div>
            </div>
        </div>
    );
};

export default FencingVisualizer;