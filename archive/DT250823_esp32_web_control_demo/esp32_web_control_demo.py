import network
import time
import socket
from machine import Pin, PWM

# --- Wi-Fi Configuration ---
SSID = "ChinaNet-3zfD"
PASSWORD = "ehhx2fk4"

# --- Servo Configuration ---
SERVO_PIN = 13  # GPIO pin connected to the servo's PWM signal line (D13)
servo = PWM(Pin(SERVO_PIN), freq=50) # 50Hz PWM frequency for servos

# Global variable to track servo state
servo_state = "Unknown"
current_duty = 75 # Initial duty cycle (mid-point for 25-125 range)

# Function to set servo angle (for limited-range servos like SG90/SG92)
# Note: This is a simplified mapping. You might need to calibrate for your specific servo.
def set_servo_angle(angle):
    global servo_state, current_duty
    # SG90/SG92 typically use a pulse width between 0.5ms (0 degrees) and 2.5ms (180 degrees)
    # 0.5ms corresponds to a duty of about 25, 2.5ms corresponds to about 125 on a 50Hz PWM (20ms period)
    # This maps 0-180 degrees to duty 25-125
    if angle < 0:
        angle = 0
    if angle > 180:
        angle = 180
    duty = int((angle / 180) * (125 - 25) + 25)
    servo.duty(duty)
    current_duty = duty
    
    # Update state
    servo_state = f"Angle: {angle} (Duty: {duty})"

# Function to adjust PWM duty cycle directly
def adjust_pwm_duty(delta):
    global current_duty, servo_state
    current_duty += delta
    # Clamp duty cycle within typical servo range (25-125)
    if current_duty < 25:
        current_duty = 25
    if current_duty > 125:
        current_duty = 125
    
    servo.duty(current_duty)
    servo_state = f"Direct PWM Control (Duty: {current_duty})"
    print(servo_state) # Print to serial for debugging

# Function to generate the web page with dynamic content
def web_page():
    global servo_state
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESP32 Servo PWM Control</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial; text-align: center; margin: 40px auto; width: 80%; }}
            .button {{ padding: 15px 32px; font-size: 16px; margin: 10px; cursor: pointer; border: none; border-radius: 5px; }}
            .open {{ background-color: #4CAF50; color: white; }}
            .close {{ background-color: #f44336; color: white; }}
            .pwm-btn {{ background-color: #2196F3; color: white; }} /* New style for PWM buttons */
            .status {{ font-size: 18px; font-weight: bold; margin: 20px 0; padding: 10px; border-radius: 5px; background-color: #f0f0f0; }}
            .open-state {{ color: #4CAF50; }}
            .close-state {{ color: #f44336; }}
            .pwm-state {{ color: #2196F3; }} /* New style for PWM state */
        </style>
        <script>
            function updateState(action) {{
                fetch('/' + action)
                    .then(response => response.text())
                    .then(data => {{
                        // Update the status div with the response
                        document.getElementById('status').innerHTML = data;
                        // Update the status class for color coding
                        const statusDiv = document.getElementById('status');
                        statusDiv.className = 'status'; // Reset classes
                        if (data.includes('Open')) {{
                            statusDiv.classList.add('open-state');
                        }} else if (data.includes('Closed')) {{
                            statusDiv.classList.add('close-state');
                        }} else if (data.includes('PWM')) {{
                            statusDiv.classList.add('pwm-state');
                        }}
                    }})
                    .catch(error => console.error('Error:', error));
            }}
        </script>
    </head>
    <body>
        <h1>ESP32 Servo PWM Control</h1>
        <div id="status" class="status">{servo_state}</div>
        
        <h2>Angle Control</h2>
        <p>
            <button class="button open" onclick="updateState('open')">Open Finger (0°)</button>
            <button class="button close" onclick="updateState('close')">Close Finger (90°)</button>
        </p>
        
        <h2>Direct PWM Control</h2>
        <p>
            <button class="button pwm-btn" onclick="updateState('pwm_up')">↑ Increase PWM</button>
            <button class="button pwm-btn" onclick="updateState('pwm_down')">↓ Decrease PWM</button>
        </p>
    </body>
    </html>
    """
    return html

# Function to connect to Wi-Fi
def connect_wifi():
    print("Initializing Wi-Fi...")
    wlan = network.WLAN(network.STA_IF)
    print("Activating Wi-Fi interface...")
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Connecting to network:', SSID)
        wlan.connect(SSID, PASSWORD)
        print("Connection initiated. Waiting for connection...")
        timeout = 0
        while not wlan.isconnected() and timeout < 30: # 30 second timeout
            time.sleep(1)
            timeout += 1
            print('Waiting for connection...', timeout)
        
        if not wlan.isconnected():
            print("Failed to connect within 30 seconds.")
            print("Connection status:", wlan.status())
            return None
        else:
            print("Successfully connected!")
    else:
        print("Already connected.")
        
    print('Network config:', wlan.ifconfig())
    return wlan.ifconfig()[0] # Return the IP address

# Function to start the web server
def start_web_server():
    global servo_state
    print("Starting web server setup...")
    ip_address = connect_wifi()
    if ip_address is None:
        print("Web server setup failed due to Wi-Fi connection failure.")
        return
    print(f'Web server starting on http://{ip_address}')
    
    # Create a socket for the web server
    print("Creating socket...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Binding socket to port 80...")
    s.bind(('', 80)) # Bind to port 80
    print("Listening for connections...")
    s.listen(5)      # Listen for incoming connections (max 5 queued)
    print('Web server started. Waiting for connections...')

    # Try to set up mDNS
    try:
        import mdns
        mdns.init()
        mdns.register_service("esp32demo", "_http", 80) # Register service name 'esp32demo'
        print("mDNS service registered: http://esp32demo.local")
    except ImportError:
        print("mDNS module not available. Please check your MicroPython firmware.")
    except Exception as e:
        print("mDNS setup failed:", e)

    try:
        while True:
            print("Waiting for a client to connect...")
            conn, addr = s.accept()
            print('Got a connection from %s' % str(addr))
            request = conn.recv(1024) # Receive the HTTP request
            request_str = str(request)
            print('Content = %s' % request_str)
            
            # Parse the request to determine the action
            response_body = ""
            if "GET /open" in request_str:
                print("Opening finger...")
                set_servo_angle(0)   # Adjust angle for 'open' position
                response_body = servo_state # Return current state
            elif "GET /close" in request_str:
                print("Closing finger...")
                set_servo_angle(90)  # Adjust angle for 'close' position
                response_body = servo_state # Return current state
            elif "GET /pwm_up" in request_str:
                print("Increasing PWM duty...")
                adjust_pwm_duty(5) # Increase by 5
                response_body = servo_state # Return current state
            elif "GET /pwm_down" in request_str:
                print("Decreasing PWM duty...")
                adjust_pwm_duty(-5) # Decrease by 5
                response_body = servo_state # Return current state
            else:
                # For root path or any other path, serve the main page
                response_body = web_page()
            
            # Send HTTP response
            response_headers = "HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n"
            
            print("Sending response...")
            conn.send(response_headers + response_body)
            conn.close()
            print('Connection closed.')
            
    except KeyboardInterrupt:
        print('Server stopped by user.')
        s.close()
    except Exception as e:
        print('An error occurred:', str(e))
        s.close()

# Main execution
if __name__ == "__main__":
    print("=== ESP32 Web PWM Control Demo ===")
    start_web_server()