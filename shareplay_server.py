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

async def handle_mouse_control(websocket):
    """
    Handle incoming WebSocket connections and process mouse control commands.

    Parameters:
    websocket (websockets.WebSocketServerProtocol): The WebSocket connection object representing the client connection.
    """
    client_ip = websocket.remote_address[0]
    message_count = 0
    
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
            message_count += 1
            print(f"Messages received: {message_count}")
            
            data = json.loads(message)
            
            # Add handling for ping message
            if data["type"] == "ping":
                await websocket.send(json.dumps({
                    "status": "ok",
                    "screen_width": SCREEN_WIDTH,
                    "screen_height": SCREEN_HEIGHT
                }))
                continue
            
            # Handle different types of mouse events
            if data["type"] == "move":
                x_abs, y_abs = fractional_to_absolute(data["x"], data["y"])
                pyautogui.moveTo(x_abs, y_abs)
                stats["moves"] += 1

            elif data["type"] == "click":
                button = data.get("button", "left")
                if "x" in data and "y" in data:
                    x_abs, y_abs = fractional_to_absolute(data["x"], data["y"])
                    pyautogui.click(x=x_abs, y=y_abs, button=button)
                else:
                    pyautogui.click(button=button)
                                    
                stats["clicks"] += 1
                
            elif data["type"] == "double_click":
                if stats["double_click"]< 100 == True:
                    button = data.get("button", "left")
                    if "x" in data and "y" in data:
                        x_abs, y_abs = fractional_to_absolute(data["x"], data["y"])
                        pyautogui.doubleClick(x=x_abs, y=y_abs, button=button)
                    else:
                        pyautogui.doubleClick(button=button)
                
                stats["double_clicks"] += 1
                
            elif data["type"] == "right_click":
                if "x" in data and "y" in data:
                    x_abs, y_abs = fractional_to_absolute(data["x"], data["y"])
                    pyautogui.rightClick(x=x_abs, y=y_abs)
                else:
                    pyautogui.rightClick()
                
                stats["right_clicks"] += 1
                
            elif data["type"] == "scroll":
                pyautogui.scroll(data["amount"])
                stats["scrolls"] += 1
            
            # Send acknowledgment
            response = {
                "status": "ok",
                "screen_width": SCREEN_WIDTH,
                "screen_height": SCREEN_HEIGHT
            }
            await websocket.send(json.dumps(response))
            
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
    
    try:
        server = await websockets.serve(handle_mouse_control, host, port)
        logger.info("Server started successfully!")
        await asyncio.Future()  # Run forever
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

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