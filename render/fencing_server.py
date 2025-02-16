from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Store active websocket connections
connections = set()


@app.get("/")
async def get():
    with open("index.html", encoding='utf-8') as f:
        return HTMLResponse(f.read())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.add(websocket)
    print(f"Client connected. Total connections: {len(connections)}")

    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received: {data}")
            # Echo back
            await websocket.send_json({"received": data})
    except WebSocketDisconnect:
        connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(connections)}")


@app.post("/action/{fencer}/{action}")
async def send_action(fencer: str, action: str):
    print(f"Action received: {fencer} - {action}")
    message = {"fencer": fencer, "action": action}

    # Broadcast to all connected clients
    dead_connections = set()
    for websocket in connections:
        try:
            await websocket.send_json(message)
        except:
            dead_connections.add(websocket)

    # Clean up dead connections
    for dead in dead_connections:
        connections.remove(dead)

    return {"status": "sent", "connections": len(connections)}


if __name__ == "__main__":
    if __name__ == "__main__":
        print("\nStarting Fencing Game Server")
        print("============================")
        print("Local access URL: http://127.0.0.1:8000")
        print("Public access URL: http://68.181.17.4:8000")
        print("\nMake sure port 8000 is open in your firewall!")
        print("============================\n")

        uvicorn.run(
            app,
            host="0.0.0.0",  # Listen on all interfaces
            port=8000)
