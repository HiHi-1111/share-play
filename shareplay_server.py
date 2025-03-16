import asyncio
import websockets
import json
import pyautogui  # For mouse control
import logging
import datetime

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

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")