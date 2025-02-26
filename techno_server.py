from flask import Flask, render_template, jsonify, request
from techno_modbus_controller import TechnoModbusLiftController
import feedparser
import configparser
import os
import glob
from serial.tools import list_ports
from flask import Flask, send_from_directory
import time
# from flask_cors import CORS

app = Flask(__name__)

# CORS(app)

current_news_index = 0  # Global variable to track the current news index
news_items = []  # Cached list of news headlines

# Initialize Modbus controller instance
controller = TechnoModbusLiftController()

# Path to config.ini file
UPLOAD_FOLDER = 'static'
print(f"upload folder {UPLOAD_FOLDER}")
CONFIG_FILE = 'config.ini'

# Ensure the uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize ConfigParser
config = configparser.ConfigParser()


def load_config():
    """Load configuration from the config.ini file."""
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    else:
        # Initialize default configuration
        config['GENERAL'] = {
            'com_port': '',
            'company_name': ''
        }
        config['FILES'] = {
            'logo_path': '',
            'up_gif_path': '',
            'down_gif_path': '',
            'video_path': ''
        }
        save_config()


def save_config():
    """Save configuration to the config.ini file."""
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


@app.route('/get-config', methods=['GET'])
def get_config():
    """Return the current configuration as JSON."""
    load_config()
    response = {
        'GENERAL': dict(config['GENERAL']),
        'FILES': dict(config['FILES']),
    }
    return jsonify(response)

@app.route('/get-dropdown-options', methods=['GET'])
def get_dropdown_options():
    """Provide options for COM ports, GIF files, and video files."""
    # Fetch COM ports
    available_ports = [port.device for port in list_ports.comports()]

    # Fetch GIF files
    gif_files = [os.path.basename(file) for file in glob.glob(os.path.join(UPLOAD_FOLDER, "*.gif"))]

    # Fetch video files
    video_files = [os.path.basename(file) for file in glob.glob(os.path.join(UPLOAD_FOLDER, "*.mp4"))]

    return jsonify({
        'com_ports': available_ports,
        'gif_files': gif_files,
        'video_files': video_files,
    })
    
def allowed_file(filename, extensions):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

@app.route('/update-config', methods=['POST'])
def update_config():
    """Update the configuration based on user input."""
    load_config()  # Load the existing configuration

    # Preserve or update GENERAL settings
    current_com_port = config['GENERAL'].get('com_port', '')  # Get current COM port
    current_company_name = config['GENERAL'].get('company_name', '')  # Get current company name

    new_com_port = request.form.get('com_port', '').strip()
    new_company_name = request.form.get('company_name', '').strip()

    # Update only if new values are provided
    config['GENERAL']['com_port'] = new_com_port if new_com_port else current_com_port
    config['GENERAL']['company_name'] = new_company_name if new_company_name else current_company_name

    # Allowed extensions
    allowed_gif = {'gif'}
    allowed_video = {'mp4', 'mkv', 'avi', 'mov', 'webm', 'ts'}
    allowed_image = {'jpg', 'jpeg', 'png'}

    # Update FILES settings, preserving old paths if no new file is uploaded
    config['FILES']['up_gif_path'] = request.form.get('up_gif_file', config['FILES'].get('up_gif_path', ''))
    config['FILES']['down_gif_path'] = request.form.get('down_gif_file', config['FILES'].get('down_gif_path', ''))
    
    
    # --- Handle Video Source (File, Link, or Live TV) ---
    video_source = request.form.get("video_source", "file").strip().lower()
    print("DEBUG: video_source =", video_source)  # Debug print

    if video_source == "live_tv":
        # Use the selected live TV channel from the form
        live_tv_channel = request.form.get("live_tv_channel", "").strip()
        if live_tv_channel:
            config['FILES']['video_path'] = "live_tv"
            print("DEBUG: Setting video_path to live TV channel:", live_tv_channel)
    elif video_source == "link":
        video_link = request.form.get("video_link", "").strip()
        print("DEBUG: video_link =", video_link)
        if video_link:
            config['FILES']['video_path'] = video_link
            print("DEBUG: Setting video_path to video_link")
        else:
            print("DEBUG: No valid video link provided.")
            return jsonify({'status': 'error', 'message': 'Please enter a valid video link.'})
    elif video_source == "file":
        if 'video_file' in request.files and request.files['video_file'].filename:
            file = request.files['video_file']
            if allowed_file(file.filename, allowed_video):
                video_path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(video_path)
                config['FILES']['video_path'] = video_path
                print("DEBUG: Setting video_path to uploaded file:", video_path)
            else:
                return jsonify({'status': 'error', 'message': 'Invalid video file type.'})
        else:
            # No file uploaded; keep the previous value.
            print("DEBUG: No video file uploaded; keeping previous video_path.")
    else:
        print("DEBUG: Unrecognized video_source; keeping previous video_path.")
    # ---------------------------------------------------------

    # Handle logo file
    if 'company_logo' in request.files and request.files['company_logo'].filename:
        file = request.files['company_logo']
        if allowed_file(file.filename, allowed_image):
            logo_path = os.path.join(UPLOAD_FOLDER, file.filename)
            os.makedirs(os.path.dirname(logo_path), exist_ok=True)
            file.save(logo_path)
            config['FILES']['logo_path'] = logo_path
        else:
            return jsonify({'status': 'error', 'message': 'Invalid file type for company logo. Only JPG, JPEG, and PNG are allowed.'})
    else:
        # Keep the current logo path if no file is uploaded
        config['FILES']['logo_path'] = config['FILES'].get('logo_path', '')

    # Handle up arrow GIF
    if 'up_gif_file' in request.files and request.files['up_gif_file'].filename:
        file = request.files['up_gif_file']
        if allowed_file(file.filename, allowed_gif):
            up_gif_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(up_gif_path)
            config['FILES']['up_gif_path'] = up_gif_path
        else:
            return jsonify({'status': 'error', 'message': 'Invalid file type for Up Arrow GIF. Only GIF files are allowed.'})
    else:
        config['FILES']['up_gif_path'] = config['FILES'].get('up_gif_path', '')

    # Handle down arrow GIF
    if 'down_gif_file' in request.files and request.files['down_gif_file'].filename:
        file = request.files['down_gif_file']
        if allowed_file(file.filename, allowed_gif):
            down_gif_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(down_gif_path)
            config['FILES']['down_gif_path'] = down_gif_path
        else:
            return jsonify({'status': 'error', 'message': 'Invalid file type for Down Arrow GIF. Only GIF files are allowed.'})
    else:
        config['FILES']['down_gif_path'] = config['FILES'].get('down_gif_path', '')

    
    # ----- Handle folder upload for images -----
    image_files = request.files.getlist("image_folder")
    if image_files:
        # Get the folder name from the first file's relative path.
        first_file = image_files[0]
        folder_name_from_upload = os.path.dirname(first_file.filename).strip()
        # Browsers often return "C:\fakepath" if no actual folder is provided.
        if not folder_name_from_upload or "fakepath" in folder_name_from_upload.lower():
            folder_name_from_upload = "uploaded_images_" + str(int(time.time()))
        
        # Check if there is an existing folder in the configuration with the same base name.
        previous_folder = config['FILES'].get('image_folder', '')
        if previous_folder and os.path.basename(previous_folder) == folder_name_from_upload:
            # Replace the existing folder: remove it and recreate it.
            import shutil
            try:
                shutil.rmtree(previous_folder)
            except Exception as e:
                print(f"Error removing folder {previous_folder}: {e}")
            upload_dir = previous_folder
            os.makedirs(upload_dir, exist_ok=True)
        else:
            # Otherwise, create a new directory using the new folder name.
            upload_dir = os.path.join(UPLOAD_FOLDER, "images", folder_name_from_upload)
            os.makedirs(upload_dir, exist_ok=True)
        
        # Process each file: only save valid image files and skip others.
        saved_any = False
        for file in image_files:
            if allowed_file(file.filename, allowed_image):
                filename = os.path.basename(file.filename)
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                saved_any = True
            else:
                print(f"Skipping file {file.filename} due to invalid type.")
        
        # Update the configuration only if at least one valid image was saved.
        if saved_any:
            config['FILES']['image_folder'] = upload_dir
        else:
            print("No valid image files were uploaded; keeping previous folder setting.")
    # ---------------------------------------------
    # Save updated configuration
    save_config()

    # Return the updated configuration as JSON
    return jsonify({
        'status': 'success',
        'current_files': {
            'com_port': config['GENERAL']['com_port'],
            'company_name': config['GENERAL']['company_name'],
            'logo_path': config['FILES'].get('logo_path', ''),
            'up_gif_path': config['FILES'].get('up_gif_path', ''),
            'down_gif_path': config['FILES'].get('down_gif_path', ''),
            'video_path': config['FILES'].get('video_path', ''),
            'image_folder': config['FILES'].get('image_folder', '')
        }
    })


config.read("config.ini")



com_port = config.get("GENERAL", "com_port", fallback="/dev/ttyUSB0")
print("COMM port: ", com_port)
if not com_port:  # In case the value is empty or None
    com_port = "/dev/ttyUSB0"
# Connect to the COM port
if not controller.techno_set_com_port(com_port):
    print(".....Failed to connect to Modbus device. Port:", com_port)
    # exit(1)


# Fetch values from config.ini
def get_config_values():
    com_port = config.get("GENERAL", "com_port", fallback="COM1")  # Default COM1 if not set
    company_name = config.get("GENERAL", "company_name", fallback="RTECH Enterprises")
    logo_path = config.get("FILES", "company_logo", fallback="logo.png")
    # Get the video path value from config
    video_path_raw = config.get("FILES", "video_path", fallback="static/sample2_1080.mp4")
    
    # Determine the correct video source based on the configuration value
    if video_path_raw.lower() == "live_tv":
        # Option: retrieve a separate URL for live TV (you can store it in config too)
        video_path = config.get("FILES", "live_tv_url", fallback="http://example.com/live")
    elif video_path_raw.startswith("http://") or video_path_raw.startswith("https://"):
        # This is an online video link (e.g., YouTube or another website)
        video_path = video_path_raw
    else:
        # Otherwise, assume it's a local file path
        video_path = video_path_raw

    up_arrow_location = config.get("FILES", "up_gif_path", fallback="up_arrow.gif")
    down_arrow_location = config.get("FILES", "down_gif_path", fallback="down_arrow.gif")
    return {
        "com_port": com_port,
        "company_name": company_name,
        "logo_path": logo_path,
        "video_path": video_path,
        "up_arrow_location": up_arrow_location,
        "down_arrow_location": down_arrow_location
    }


@app.route("/")
# def serve_static(filename):
#     return send_from_directory('/home/pi/Desktop/Display_Project_Pysignage/', filename)
def index():
    """Main page to display lift data, video, and news feed."""
    config_values = get_config_values()
    print("config values: ", config_values)
    company_name = config.get('GENERAL', 'company_name')
    up_arrow_gif = config.get('FILES', 'up_gif_path')
    down_arrow_gif = config.get('FILES', 'down_gif_path')
    video_path = config['FILES'].get('video_path', '')  # Fetch the video path from config
    logo_path = config.get('FILES', 'logo_path')
    return render_template("new_alignment.html", company_name=company_name, up_arrow_gif=up_arrow_gif, down_arrow_gif=down_arrow_gif, video_path=video_path, logo_path=logo_path)  # Pass the video_path directly as a string


@app.route("/Configuration Page")
def config_page():
    """Configuration page to config gif, port number, video, and news feed."""
    return render_template("config_html.html")


@app.route('/lift-data', methods=['GET'])
def get_lift_data():
    # Simulate Modbus data
    floor = controller.techno_get_floor_number() # Replace with actual Modbus read
    direction = controller.techno_get_movement_status()  # Replace with actual Modbus read
    
    # Fetch GIF paths from configuration
    up_arrow_gif = config.get("FILES", "up_gif_path", fallback="static/up_arrow.gif")
    down_arrow_gif = config.get("FILES", "down_gif_path", fallback="static/down_arrow.gif")
     # Get the video path value from config
    video_path_raw = config.get("FILES", "video_path", fallback="static/sample2_1080.mp4")
    
    # Determine the correct video source based on the configuration value
    if video_path_raw.lower() == "live_tv":
        # Option: retrieve a separate URL for live TV (you can store it in config too)
        video_path = config.get("FILES", "live_tv_url", fallback="http://example.com/live")
    elif video_path_raw.startswith("http://") or video_path_raw.startswith("https://"):
        # This is an online video link (e.g., YouTube or another website)
        video_path = video_path_raw
    else:
        # Otherwise, assume it's a local file path
        video_path = video_path_raw

    print(f"Direction: {direction}, floor: {floor}")
    return jsonify({
        "floor": floor,
        "direction": direction,
        "up_arrow_gif": up_arrow_gif,
        "down_arrow_gif": down_arrow_gif,
        "video_path": video_path
    })
    
@app.route('/get-video-path', methods=['GET'])
def get_video_path():
    video_path = config.get("FILES", "video_path", fallback="static/sample_video.mp4")
    return jsonify({"video_path": video_path})

@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(directory="/path/to/videos", path=filename)

@app.route('/get-logo-path', methods=['GET'])
def get_logo_path():
    logo_path = config.get("FILES", "logo_path", fallback="static/logo.png")
    return jsonify({"logo_path": logo_path})


    
@app.route('/files/<path:filename>')
def serve_files(filename):
    # Serve files from any local directory
    return send_from_directory(directory='/', path=filename)


def get_faults():
    # Fetch faults from the lift controller
    techno_faults = controller.techno_read_faults()
    return techno_faults
    # return [
    #      ('MIMO', 0),
    #      ('FAULT(ALARM MESSAGE)', 1),
    #      ('FM RETURN', 0),
    #      ('FM EMERGENCY', 0),
    #      ('FIREMAN OPERATION', 0),
    #      ('MAINTENANCE', 1),
    #      ('OVERLOAD', 0),
    #      ('INDEPENDENT', 0),
    #      ('ATTENDANT', 0),
    #      ('MANUAL', 0),
    #      ('STOP/RUN', 0)
    #  ]
    
@app.route('/faults', methods=['GET'])
def fetch_faults():
    techno_faults = get_faults()

    # Map faults to human-readable messages
    fault_messages = {
        'MIMO': "Multi-Input Multi-Output fault",
        'FAULT(ALARM MESSAGE)': "Alarm triggered",
        'FM RETURN': "Fault in Floor Management Return",
        'FM EMERGENCY': "Emergency in Floor Management",
        'FIREMAN OPERATION': "Fireman operation activated",
        'MAINTENANCE': "Elevator in maintenance mode",
        'OVERLOAD': "Elevator overloaded",
        'INDEPENDENT': "Independent operation mode active",
        'ATTENDANT': "Attendant mode active",
        'MANUAL': "Manual mode active",
        'STOP/RUN': "Elevator stopped or in run mode"
    }

    # Extract active faults
    active_faults = [
        fault_messages[label]
        for label, value in techno_faults
        if value != 0  # Active faults only
    ]

    # Prepare the response
    return jsonify({
        "faults": active_faults
    })
    
def fetch_news():
    """Fetch and cache the latest news headlines."""
    global news_items
    feed_url = "https://news.google.com/rss"
    feed = feedparser.parse(feed_url)
    news_items = [entry.title for entry in feed.entries[:5]]


@app.route("/news")
def news():
    """Serve a single headline at a time."""
    global current_news_index, news_items
    try:
        # Fetch news if the cache is empty
        if not news_items:
            fetch_news()

        # Serve the current headline
        headline = news_items[current_news_index]

        # Update index to point to the next headline
        current_news_index = (current_news_index + 1) % len(news_items)

        return jsonify({"headline": headline})
    except Exception as e:
        print(f"Error fetching news: {e}")
        return jsonify({"error": "Failed to load news."})
    
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
