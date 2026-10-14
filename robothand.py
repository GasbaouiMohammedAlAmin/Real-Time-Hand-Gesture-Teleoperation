"""
RobotHand
Sends finger angles from Python to the 3D robot hand viewer (viewer/robot_hand.html).

This is a provided file: you don't need to change it.
It starts a small WebSocket server in the background. The viewer connects to it
and moves the robot's joints to whatever angles you send.

Usage:
    robot = RobotHand()
    robot.setFinger("index", mcp, pip, dip)   # degrees, 0 = straight
    robot.update()                            # send to the viewer
"""

import asyncio
import json
import threading

from websockets.asyncio.server import broadcast, serve

FINGERS = ("thumb", "index", "middle", "ring", "pinky")


class RobotHand:
    def __init__(self, host="localhost", port=8765):
        self.host, self.port = host, port
        self.angles = {name: [0.0, 0.0, 0.0] for name in FINGERS}
        self._clients = set()
        self._error = None
        self._ready = threading.Event()
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._run, daemon=True).start()
        self._ready.wait(5)
        if self._error:
            raise RuntimeError(f"Could not start the robot hand server on port {port}: {self._error}")
        print(f"Robot hand server running on ws://{host}:{port}. Open viewer/robot_hand.html in your browser.")

    # ---------- public ----------
    def setFinger(self, name, mcp, pip, dip):
        """Set the three joint angles of one finger, in degrees (0 = straight)."""
        if name not in self.angles:
            raise ValueError(f"Unknown finger '{name}'. Use one of: {', '.join(FINGERS)}")
        self.angles[name] = [round(float(mcp), 1), round(float(pip), 1), round(float(dip), 1)]

    def update(self):
        """Send the current angles to every connected viewer."""
        message = json.dumps(self.angles)
        #print ("message",message)
        self._loop.call_soon_threadsafe(lambda: broadcast(set(self._clients), message))

    @property
    def connected(self):
        return len(self._clients) > 0

    # ---------- internal ----------
    def _run(self):
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except Exception as e:  # e.g. port already in use
            self._error = e
            self._ready.set()

    async def _serve(self):
        async with serve(self._handler, self.host, self.port):
            self._ready.set()
            await asyncio.Future()  # run forever

    async def _handler(self, websocket):
        self._clients.add(websocket)
        print("Viewer connected")
        try:
            await websocket.send(json.dumps(self.angles))
            await websocket.wait_closed()
        finally:
            self._clients.discard(websocket)
            print("Viewer disconnected")
