import asyncio
import websockets
import json
import pyautogui  # For mouse control
import logging
import datetime
import tkinter as tk
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mouse_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MouseServer")

# Set failsafe to False if you want to allow mouse movement to all screen positions
# Be careful with this setting as it can make it hard to regain control
pyautogui.FAILSAFE = True

# Get screen dimensions once at startup
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

def fractional_to_absolute(x_frac, y_frac):
    """Convert fractional coordinates (0-1) to absolute screen coordinates"""
    x_abs = int(x_frac * SCREEN_WIDTH)
    y_abs = int(y_frac * SCREEN_HEIGHT)
    return x_abs, y_abs

async def handle_mouse_control(websocket, path):
    """
    Handle incoming WebSocket connections and process mouse control commands.

    Parameters:
    websocket (websockets.WebSocketServerProtocol): The WebSocket connection object representing the client connection.
    path (str): The URL path of the WebSocket connection (not used in this function).

    Functionality:
    - Logs the IP address of the connected client and the screen dimensions of the server.
    - Initializes a dictionary to track the number of different mouse events (moves, clicks, right-clicks, double-clicks, scrolls).
    - Continuously listens for messages from the client and processes them based on the event type:
        - Move: Moves the mouse to the specified fractional coordinates.
        - Click: Performs a mouse click at the specified fractional coordinates or at the current position.
        - Double Click: Performs a double-click at the specified fractional coordinates or at the current position.
        - Right Click: Performs a right-click at the specified fractional coordinates or at the current position.
        - Scroll: Scrolls the mouse wheel by the specified amount.
    - Sends an acknowledgment message back to the client after processing each event.
    - Logs any errors that occur while handling client messages.
    - Logs a summary of the session, including the duration and the number of each type of mouse event.
    """
    client_ip = websocket.remote_address[0]
    logger.info(f"Client connected from {client_ip}")
    logger.info(f"Screen dimensions: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    
    # Track activity statistics
    stats = {
        "moves": 0,
        "clicks": 0,
        "right_clicks": 0,
        "double_clicks": 0,
        "scrolls": 0
    }
    
    start_time = datetime.datetime.now()
    
    try:
        async for message in websocket:
            data = json.loads(message)
            
            # Handle different types of mouse events
            if data["type"] == "move":
                # Convert fractional coordinates to absolute screen coordinates
                x_abs, y_abs = fractional_to_absolute(data["x"], data["y"])
                pyautogui.moveTo(x_abs, y_abs)

                # Update the stats
                stats["moves"] += 1
                
                # Log every 100 moves to avoid excessive logging
                if stats["moves"] % 100 == 0:
                    logger.info(f"Processed {stats['moves']} mouse movements")
                    logger.debug(f"Last move: frac({data['x']:.3f}, {data['y']:.3f}) → abs({x_abs}, {y_abs})")

            elif data["type"] == "click":
                button = data.get("button", "left")
                if "x" in data and "y" in data:
                    # Click at specific position
                    x_abs, y_abs = fractional_to_absolute(data["x"], data["y"])
                    pyautogui.click(x=x_abs, y=y_abs, button=button)
                else:
                    # Click at current position
                    pyautogui.click(button=button)
                                    
                x, y = pyautogui.position()
                frac_x, frac_y = x/SCREEN_WIDTH, y/SCREEN_HEIGHT
                stats["clicks"] += 1
                logger.info(f"{button.capitalize()} mouse click at abs({x}, {y}) / frac({frac_x:.3f}, {frac_y:.3f})")
                
            elif data["type"] == "double_click":
                button = data.get("button", "left")
                if "x" in data and "y" in data:
                    x_abs, y_abs = fractional_to_absolute(data["x"], data["y"])
                    pyautogui.doubleClick(x=x_abs, y=y_abs, button=button)
                else:
                    pyautogui.doubleClick(button=button)
                
                x, y = pyautogui.position()
                frac_x, frac_y = x/SCREEN_WIDTH, y/SCREEN_HEIGHT
                stats["double_clicks"] += 1
                logger.info(f"{button.capitalize()} double-click at abs({x}, {y}) / frac({frac_x:.3f}, {frac_y:.3f})")
                
            elif data["type"] == "right_click":
                if "x" in data and "y" in data:
                    x_abs, y_abs = fractional_to_absolute(data["x"], data["y"])
                    pyautogui.rightClick(x=x_abs, y=y_abs)
                else:
                    pyautogui.rightClick()
                
                x, y = pyautogui.position()
                frac_x, frac_y = x/SCREEN_WIDTH, y/SCREEN_HEIGHT
                stats["right_clicks"] += 1
                logger.info(f"Right click at abs({x}, {y}) / frac({frac_x:.3f}, {frac_y:.3f})")
                
            elif data["type"] == "scroll":
                pyautogui.scroll(data["amount"])
                x, y = pyautogui.position()
                frac_x, frac_y = x/SCREEN_WIDTH, y/SCREEN_HEIGHT
                stats["scrolls"] += 1
                logger.info(f"Scroll: {data['amount']} at abs({x}, {y}) / frac({frac_x:.3f}, {frac_y:.3f})")
            
            # Send acknowledgment
            await websocket.send(json.dumps({
                "status": "ok",
                "screen_width": SCREEN_WIDTH,
                "screen_height": SCREEN_HEIGHT
            }))
    except Exception as e:
        logger.error(f"Error handling client: {e}")
    finally:
        # Log session summary
        duration = datetime.datetime.now() - start_time
        logger.info(f"Client {client_ip} disconnected after {duration}")
        logger.info(f"Session summary - Moves: {stats['moves']}, Clicks: {stats['clicks']}, "
                   f"Right clicks: {stats['right_clicks']}, Double clicks: {stats['double_clicks']}, "
                   f"Scrolls: {stats['scrolls']}")

async def start_server():
    # Start WebSocket server
    host = "0.0.0.0"  # Listen on all interfaces
    port = 3000
    
    logger.info(f"Starting mouse control server on {host}:{port}")
    logger.info(f"Screen size: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    logger.info(f"Using fractional coordinates (0,0) to (1,1)")
    logger.info(f"Log file: mouse_server.log")
    
    async with websockets.serve(handle_mouse_control, host, port):
        await asyncio.Future()  # Run forever

def run_server():
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")

if __name__ == "__main__":
    # Create a simple Tkinter window
    root = tk.Tk()
    root.title("Mouse Control Server")
    root.geometry("300x200")
    
    tk.Label(root, text="Server is running...").pack(pady=10)
    tk.Label(root, text="URL: ws://0.0.0.0:3000").pack(pady=10)
    
    # Run the server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    root.mainloop()