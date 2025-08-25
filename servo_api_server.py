import network
import time
import socket
import json
from machine import Pin, PWM

# --- Configuration ---
# Wi-Fi
SSID = "ChinaNet-3zfD"
PASSWORD = "ehhx2fk4"

# Servo
SERVO_PIN = 13  # GPIO pin connected to the servo's PWM signal line (D13)
servo = PWM(Pin(SERVO_PIN), freq=50) # 50Hz PWM frequency for servos

# Global state
current_duty = 75  # Initial duty cycle for stop (1.5ms pulse)
servo.duty(current_duty) # Initialize servo to stop

# Speed presets (duty cycle values)
# These values are examples and may need calibration for your specific servo
SPEED_PRESETS = {
    "cw": {  # Clockwise rotation
        "slow": 65,
        "medium": 60,
        "fast": 50
    },
    "ccw": { # Counter-Clockwise rotation
        "slow": 85,
        "medium": 90,
        "fast": 100
    }
}

# --- Helper Functions ---

def connect_wifi():
    """Connects to the configured Wi-Fi network."""
    print("Initializing Wi-Fi...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Connecting to network:', SSID)
        wlan.connect(SSID, PASSWORD)
        timeout = 0
        while not wlan.isconnected() and timeout < 30:
            time.sleep(1)
            timeout += 1
            print('Waiting for connection...', timeout)
        
        if not wlan.isconnected():
            print("Failed to connect.")
            return None
        else:
            print("Successfully connected!")
    else:
        print("Already connected.")
        
    config = wlan.ifconfig()
    print('Network config:', config)
    return config[0] # Return IP address

def get_status():
    """Returns the current status of the servo."""
    # A simple status message based on duty cycle
    if current_duty == 75:
        status_msg = "Stopped"
    elif 50 <= current_duty < 75:
        status_msg = f"CW ({'Fast' if current_duty <= 60 else 'Medium' if current_duty <= 65 else 'Slow'})"
    elif 75 < current_duty <= 100:
        status_msg = f"CCW ({'Fast' if current_duty >= 90 else 'Medium' if current_duty >= 85 else 'Slow'})"
    else:
        status_msg = "Custom"
        
    return {"duty": current_duty, "status": status_msg}

def set_servo_duty(duty):
    """Sets the servo PWM duty cycle and updates the global state."""
    global current_duty
    # Clamp duty cycle to a reasonable range
    duty = max(25, min(duty, 125))
    servo.duty(duty)
    current_duty = duty
    print(f"Servo duty set to: {current_duty}")

def execute_step(direction, speed):
    """Executes a single step rotation and then stops."""
    global current_duty
    if direction not in ["cw", "ccw"] or speed not in ["slow", "medium", "fast"]:
        return False # Invalid parameters

    # Get the duty cycle for the specified speed and direction
    temp_duty = SPEED_PRESETS[direction][speed]
    print(f"Executing {direction.upper()} step at {speed} speed (duty: {temp_duty})")
    
    # Set the temporary duty cycle
    set_servo_duty(temp_duty)
    
    # Wait for a short duration (this determines the step size)
    # Adjust this value (in seconds) to change the step size
    time.sleep(0.2) 
    
    # Stop the servo
    set_servo_duty(75)
    print("Step completed, servo stopped.")
    return True

# --- Web Server ---

def send_response(conn, status_code, content_type, body):
    """Sends an HTTP response."""
    response = f"HTTP/1.1 {status_code}\nContent-Type: {content_type}\nConnection: close\n\n{body}"
    conn.send(response)
    conn.close()

def handle_request(conn, request_str):
    """Parses the HTTP request and calls the appropriate handler."""
    print(f"Handling request: {request_str[:60]}...") # Log first 60 chars
    
    # Default response
    status_code = "404 Not Found"
    content_type = "text/plain"
    body = "Endpoint not found"
    
    try:
        # --- API Routes ---
        
        # GET /api/status
        if "GET /api/status" in request_str:
            status_code = "200 OK"
            content_type = "application/json"
            body = json.dumps(get_status())
            
        # POST /api/step/cw
        elif "POST /api/step/cw" in request_str:
            # Simple parsing for JSON body (for demo purposes)
            # In a full implementation, you'd parse the full HTTP body properly
            if '"speed": "slow"' in request_str:
                success = execute_step("cw", "slow")
            elif '"speed": "medium"' in request_str:
                success = execute_step("cw", "medium")
            elif '"speed": "fast"' in request_str:
                success = execute_step("cw", "fast")
            else:
                success = False
                
            status_code = "200 OK" if success else "400 Bad Request"
            content_type = "application/json"
            body = json.dumps(get_status()) # Return status after action
            
        # POST /api/step/ccw
        elif "POST /api/step/ccw" in request_str:
             # Simple parsing for JSON body (for demo purposes)
            if '"speed": "slow"' in request_str:
                success = execute_step("ccw", "slow")
            elif '"speed": "medium"' in request_str:
                success = execute_step("ccw", "medium")
            elif '"speed": "fast"' in request_str:
                success = execute_step("ccw", "fast")
            else:
                success = False
                
            status_code = "200 OK" if success else "400 Bad Request"
            content_type = "application/json"
            body = json.dumps(get_status()) # Return status after action
            
        # POST /api/pwm/set (for calibration/debugging)
        elif "POST /api/pwm/set" in request_str:
            # Simple parsing for JSON body (for demo purposes)
            try:
                # This is a very basic and fragile way to extract JSON.
                # A real implementation should parse the full HTTP request properly.
                start = request_str.find('{')
                end = request_str.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = request_str[start:end]
                    data = json.loads(json_str)
                    duty = int(data.get("duty", 75))
                    set_servo_duty(duty)
                    status_code = "200 OK"
                else:
                    status_code = "400 Bad Request"
            except Exception as e:
                print(f"Error parsing /api/pwm/set: {e}")
                status_code = "400 Bad Request"
            content_type = "application/json"
            body = json.dumps(get_status())
            
        # Serve a simple message for the root path
        elif "GET / " in request_str:
            status_code = "200 OK"
            content_type = "text/html"
            body = "<h1>ESP32 Servo API Server</h1><p>Use /api endpoints to control the servo.</p>"
            
    except Exception as e:
        print(f"Error handling request: {e}")
        status_code = "500 Internal Server Error"
        content_type = "text/plain"
        body = "Internal server error"
        
    send_response(conn, status_code, content_type, body)

def start_web_server():
    """Starts the main web server loop."""
    print("Starting web server setup...")
    ip_address = connect_wifi()
    if ip_address is None:
        print("Web server setup failed due to Wi-Fi connection failure.")
        return
        
    print(f'Web server starting on http://{ip_address}')
    
    # Create and configure socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow reuse of address
    s.bind(('', 80))
    s.listen(5)
    print('Web server started. Waiting for connections...')

    try:
        while True:
            conn, addr = s.accept()
            print(f'Got a connection from {addr}')
            request = conn.recv(1024)
            request_str = str(request)
            handle_request(conn, request_str)
            print('Connection closed.')
            
    except KeyboardInterrupt:
        print('Server stopped by user.')
    finally:
        s.close()

# --- Main Execution ---
if __name__ == "__main__":
    print("=== ESP32 360 Servo API Server ===")
    start_web_server()