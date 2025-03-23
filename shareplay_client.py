import asyncio
import websockets
import json
import pyautogui  # To get local mouse position
import tkinter as tk
from tkinter import simpledialog, messagebox
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class RemoteMouseClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Remote Mouse Control")
        self.root.geometry("500x350")
        
        # Local screen dimensions
        self.local_width, self.local_height = pyautogui.size()
        
        # Remote screen dimensions (will be updated after connection)
        self.remote_width = 1920  # Default assumption
        self.remote_height = 1080  # Default assumption
        
        # Initialize event loop management
        self.loop = asyncio.new_event_loop()
        self.loop_thread = None
        
        self.connection_frame = tk.Frame(root)
        self.connection_frame.pack(pady=20)
        
        tk.Label(self.connection_frame, text="Server Address:").grid(row=0, column=0, padx=5, pady=5)
        self.server_entry = tk.Entry(self.connection_frame, width=20)
        self.server_entry.insert(0, "wss://93dd-96-255-61-12.ngrok-free.app")  # Replace with actual IP
        self.server_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.connect_button = tk.Button(self.connection_frame, text="Connect", command=self.connect)
        self.connect_button.grid(row=0, column=2, padx=5, pady=5)
        
        self.status_frame = tk.Frame(root)
        self.status_frame.pack(pady=5)
        
        self.status_label = tk.Label(self.status_frame, text="Disconnected", fg="red")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.screen_info_label = tk.Label(self.status_frame, 
                                          text=f"Local: {self.local_width}x{self.local_height} | Remote: Unknown")
        self.screen_info_label.pack(side=tk.LEFT, padx=10)
        
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(pady=10)
        
        self.tracking = False
        self.track_button = tk.Button(self.control_frame, text="Start Tracking", command=self.toggle_tracking)
        self.track_button.pack(pady=10)
        
        # Add mouse position display
        self.position_frame = tk.Frame(root)
        self.position_frame.pack(pady=5)
        
        tk.Label(self.position_frame, text="Current Position:").pack(side=tk.LEFT, padx=5)
        self.position_label = tk.Label(self.position_frame, text="(0.000, 0.000)")
        self.position_label.pack(side=tk.LEFT, padx=5)
        
        # Update position label periodically
        self.update_position_display()
        
        self.websocket = None
        self.last_position = (0, 0)
        self.tracking_task = None
        
        # Start the event loop thread
        self.start_loop_thread()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def start_loop_thread(self):
        """Start a dedicated thread for the asyncio event loop"""
        self.loop_thread = threading.Thread(target=self.run_event_loop, daemon=True)
        self.loop_thread.start()
    
    def run_event_loop(self):
        """Run the event loop in this thread"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def submit_task(self, coro):
        """Submit a coroutine to the event loop"""
        return asyncio.run_coroutine_threadsafe(coro, self.loop)
    
    def update_position_display(self):
        """Update the mouse position display with fractional coordinates"""
        if self.root.winfo_exists():
            x, y = pyautogui.position()
            x_frac = x / self.local_width
            y_frac = y / self.local_height
            self.position_label.config(text=f"({x_frac:.3f}, {y_frac:.3f})")
            self.root.after(100, self.update_position_display)
        
    def connect(self):
        if self.websocket:
            self.disconnect()
            return
        
        server_address = self.server_entry.get()
        self.submit_task(self.connect_to_server(server_address))
        
    async def connect_to_server(self, server_address):
        try:
            self.websocket = await websockets.connect(server_address)
            
            # Send a ping message to get server info
            await self.websocket.send(json.dumps({
                "type": "ping",
                "message": "Hello from client"
            }))
            
            response = await self.websocket.recv()
            server_info = json.loads(response)
            
            if "screen_width" in server_info and "screen_height" in server_info:
                self.remote_width = server_info["screen_width"]
                self.remote_height = server_info["screen_height"]
            
            self.root.after(0, self.update_ui_connected)
        except Exception as e:
            self.root.after(0, lambda: self.update_ui_error(str(e)))
        
    def update_ui_connected(self):
        self.status_label.config(text="Connected", fg="green")
        self.connect_button.config(text="Disconnect")
        self.screen_info_label.config(text=f"Local: {self.local_width}x{self.local_height} | Remote: {self.remote_width}x{self.remote_height}")
        
    def update_ui_error(self, error_msg):
        self.status_label.config(text=f"Error: {error_msg}", fg="red")
        messagebox.showerror("Connection Error", error_msg)
        
    def update_ui_disconnected(self):
        self.status_label.config(text="Disconnected", fg="red")
        self.connect_button.config(text="Connect")
        self.toggle_tracking(force_stop=True)
        
    def disconnect(self):
        if self.tracking:
            self.toggle_tracking(force_stop=True)
        
        if self.websocket:
            self.submit_task(self.disconnect_from_server())
        
    async def disconnect_from_server(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.root.after(0, self.update_ui_disconnected)
            
    def toggle_tracking(self, force_stop=False):
        if force_stop or self.tracking:
            self.tracking = False
            self.track_button.config(text="Start Tracking")
            if self.tracking_task:
                self.tracking_task.cancel()
                self.tracking_task = None
        else:
            if not self.websocket:
                messagebox.showwarning("Not Connected", "Please connect to the server first")
                return
                
            self.tracking = True
            self.track_button.config(text="Stop Tracking")
            self.tracking_task = self.submit_task(self.track_mouse())
            
    async def track_mouse(self):
        try:
            # Track mouse and send events while tracking is True
            while self.tracking and self.websocket:
                # Get current mouse position as fractional coordinates
                x, y = pyautogui.position()
                x_frac = x / self.local_width
                y_frac = y / self.local_height
                
                # Calculate fractional position
                current_pos = (x_frac, y_frac)
                
                # Only send if position changed significantly
                if abs(current_pos[0] - self.last_position[0]) > 0.001 or abs(current_pos[1] - self.last_position[1]) > 0.001:
                    self.last_position = current_pos
                    message = {
                        "type": "move",
                        "x": x_frac,
                        "y": y_frac
                    }
                    await self.websocket.send(json.dumps(message))
                    await self.websocket.recv()  # Wait for acknowledgment
                    
                # Check for mouse clicks
                # Note: PyAutoGUI doesn't provide a direct way to check if buttons are pressed
                # You would need to use a different approach for real-time click detection
                # This simplified example doesn't detect clicks
                
                # Small delay to prevent flooding the connection
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            logging.info("Mouse tracking cancelled")
        except Exception as e:
            logging.error(f"Tracking error: {e}")
            if self.websocket:
                self.root.after(0, lambda: self.update_ui_error(str(e)))
                await self.websocket.close()
                self.websocket = None
                self.root.after(0, self.update_ui_disconnected)
    
    def on_closing(self):
        """Handle window close event"""
        self.tracking = False
        
        # Cancel any tracking task
        if self.tracking_task:
            self.tracking_task.cancel()
        
        # Close websocket if open
        if self.websocket:
            self.submit_task(self.disconnect_from_server())
        
        # Shutdown the event loop
        if self.loop:
            for task in asyncio.all_tasks(self.loop):
                task.cancel()
            
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        # Destroy the window
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteMouseClient(root)
    root.mainloop()
    