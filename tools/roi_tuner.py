
import cv2
import time
import os
import sys
import numpy as np
import threading
import http.server
import socketserver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Add base dir to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def start_server():
    server_dir = os.path.join(Config.BASE_DIR, "dino-chrome")
    os.chdir(server_dir)
    handler = http.server.SimpleHTTPRequestHandler
    try:
        # Allow reuse address to prevent "Address already in use" if restarted quickly
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", 8000), handler) as httpd:
            print("Serving game at port 8000")
            httpd.serve_forever()
    except OSError: 
        print("Server likely already running on port 8000")
        pass

def main():
    print("Launching browser for ROI Tuning...")

    # Start Server
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(2) # Wait for server
    
    # Setup Driver (Similar to Env but standalone)
    chrome_options = Options()
    for arg in Config.CHROME_ARGS:
        chrome_options.add_argument(arg)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(Config.GAME_URL)
    
    print("Waiting 10 seconds for game to stabilize...")
    time.sleep(10)
    
    # Start the game to get some obstacles maybe
    driver.try_execute_script = lambda script: driver.execute_script(script) if driver.service.process else None
    
    try:
        driver.execute_script("Runner.instance_.restart()")
    except Exception as e:
        print(f"Could not restart game: {e}")

    time.sleep(2)
    
    # Capture Full Screenshot using OpenCV/Numpy
    b64_img = driver.get_screenshot_as_base64()
    
    # Use standard library to decode to avoid heavy PIL dependency if possible, but cv2 needs numpy
    import base64
    img_data = base64.b64decode(b64_img)
    nparr = np.frombuffer(img_data, np.uint8)
    img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Draw ROI Rectangle
    # Config: ROI_LEFT, ROI_TOP, ROI_WIDTH, ROI_HEIGHT
    x = Config.ROI_LEFT
    y = Config.ROI_TOP
    w = Config.ROI_WIDTH
    h = Config.ROI_HEIGHT
    
    # Draw Green Box
    cv2.rectangle(img_np, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    output_path = os.path.join(Config.BASE_DIR, "roi_debug.png")
    cv2.imwrite(output_path, img_np)
    
    print(f"Saved debug image with ROI to: {output_path}")
    print("Check this image. If the Dinosaur or obstacles are outside the Green Box, adjust config.py.")
    
    driver.quit()

if __name__ == "__main__":
    main()
