from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import os
from datetime import datetime
import asyncio
from typing import Set, Dict

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

class GameState:
    def __init__(self):
        self.reset()
        
    def reset(self):
        print("Resetting game state...")
        self.left_score = 0
        self.right_score = 0
        self.left_position = -2.0
        self.right_position = 2.0
        self.left_blade_angle = 0.0
        self.right_blade_angle = 0.0
        self.distance = "LONG"
        self.left_action = None
        self.right_action = None
        self.last_update = datetime.now()
        self.episode_in_progress = False
        
    def start_episode(self):
        self.episode_in_progress = True
        self.reset()
        
    def end_episode(self):
        self.episode_in_progress = False
        
    def update_from_client_state(self, state_data: dict):
        try:
            if not self.episode_in_progress:
                return
                
            if 'left_fencer' in state_data:
                left_fencer = state_data['left_fencer']
                self.left_position = left_fencer.get('position', {}).get('x', self.left_position)
                if 'blade_rotation' in left_fencer:
                    self.left_blade_angle = left_fencer['blade_rotation'].get('y', self.left_blade_angle)
                self.left_action = left_fencer.get('current_action', self.left_action)

            if 'right_fencer' in state_data:
                right_fencer = state_data['right_fencer']
                self.right_position = right_fencer.get('position', {}).get('x', self.right_position)
                if 'blade_rotation' in right_fencer:
                    self.right_blade_angle = right_fencer['blade_rotation'].get('y', self.right_blade_angle)
                self.right_action = right_fencer.get('current_action', self.right_action)

            self.distance = state_data.get('distance', self.distance)
            self.last_update = datetime.now()
            
        except Exception as e:
            print(f"Error updating game state: {e}")
            
    def to_dict(self):
        return {
            "left_score": self.left_score,
            "right_score": self.right_score,
            "left_position": self.left_position,
            "right_position": self.right_position,
            "left_blade_angle": self.left_blade_angle,
            "right_blade_angle": self.right_blade_angle,
            "distance": self.distance,
            "left_action": self.left_action,
            "right_action": self.right_action,
            "timestamp": self.last_update.timestamp(),
            "episode_in_progress": self.episode_in_progress
        }

game_state = GameState()
connections: Set[WebSocket] = set()
last_message_time: Dict[WebSocket, datetime] = {}
MIN_MESSAGE_INTERVAL = 0.1  # seconds

@app.get("/")
async def get():
    html_path = os.path.join(CURRENT_DIR, "index.html")
    try:
        with open(html_path, encoding='utf-8') as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse(f"Error: Could not find {html_path}", status_code=500)

async def broadcast_message(message: dict):
    """Broadcast a message to all connected clients"""
    dead_connections = set()
    
    for connection in connections:
        try:
            await connection.send_json(message)
        except:
            dead_connections.add(connection)
    
    # Remove dead connections
    for dead in dead_connections:
        connections.remove(dead)
        if dead in last_message_time:
            del last_message_time[dead]

async def handle_state_update(websocket: WebSocket, data: dict):
    """Handle state update from client"""
    if 'state' in data:
        game_state.update_from_client_state(data['state'])
    
    await websocket.send_json({
        "type": "state_response",
        "state": game_state.to_dict()
    })

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.add(websocket)
    last_message_time[websocket] = datetime.now()
    print(f"Client connected. Total connections: {len(connections)}")
    
    # Send initial state
    await websocket.send_json({
        "type": "state_response",
        "state": game_state.to_dict()
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Rate limiting
            current_time = datetime.now()
            time_since_last = (current_time - last_message_time[websocket]).total_seconds()
            if time_since_last < MIN_MESSAGE_INTERVAL:
                await asyncio.sleep(MIN_MESSAGE_INTERVAL - time_since_last)
            
            last_message_time[websocket] = current_time
            
            # Handle different message types
            if data.get("type") == "state_update":
                await handle_state_update(websocket, data)
                
            elif data.get("type") == "action":
                # Handle action commands
                fencer = data.get("fencer")
                action = data.get("action")
                
                if fencer == "left":
                    game_state.left_action = action
                elif fencer == "right":
                    game_state.right_action = action
                
                # Broadcast action to all clients
                await broadcast_message(data)
                
            elif data.get("type") == "hit":
                # Handle scoring
                scorer = data.get("scorer")
                if scorer == "left":
                    game_state.left_score += 1
                elif scorer == "right":
                    game_state.right_score += 1
                
                # End episode on hit
                game_state.end_episode()
                
                # Broadcast updated state
                await broadcast_message({
                    "type": "game_state",
                    "state": game_state.to_dict()
                })
                
            elif data.get("type") == "reset":
                # Reset and start new episode
                game_state.start_episode()
                print("Starting new episode...")
                
                # Broadcast reset to all clients
                await broadcast_message({
                    "type": "reset",
                    "state": game_state.to_dict()
                })
                
            elif data.get("type") == "hello":
                await websocket.send_json({
                    "type": "game_state",
                    "state": game_state.to_dict()
                })
            
    except WebSocketDisconnect:
        connections.remove(websocket)
        if websocket in last_message_time:
            del last_message_time[websocket]
        print(f"Client disconnected. Total connections: {len(connections)}")
    except Exception as e:
        print(f"Error in websocket connection: {e}")
        if websocket in connections:
            connections.remove(websocket)
        if websocket in last_message_time:
            del last_message_time[websocket]

if __name__ == "__main__":
    print("\nStarting Fencing Game Server")
    print("============================")
    print("Local URL: http://127.0.0.1:8000")
    print("Network URL: http://0.0.0.0:8000")
    print("============================\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)