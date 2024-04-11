import cv2  # We import the OpenCV library for image and video processing tasks.
import easyocr  # We import the easyocr library for extracting text from images.
import re  # We import the regular expressions library for text cleaning and validation.
from ..models import Vehicle, LoginLogout, EntryApproval # We assume we import our 'Vehicle' model from within our application. 
from flask_login import current_user, login_required
from datetime import datetime, timedelta
from.. import db, app, logging
from flask import Response, Blueprint, jsonify # We import necessary components from Flask.
from sqlalchemy import func 
import os

import os
file_path = os.path.join(app.root_path, 'static', '"plate_number.xml"')

system = Blueprint('system', __name__)  # We create a Flask blueprint named 'system'.

MIN_PLATE_AREA = 500  # We define the minimum area a detected region must have to be considered a potential license plate.
HAARCASCADE_FILE ="plate_number.xml"  # We specify the path to our Haar Cascade classifier file.
OCR_LANGUAGES = ['en']  # We indicate english as the language supported by our OCR system.
latest_plate = None  # We initialize a variable to store the most recently recognized plate.
plate_recognition_active = False  # We use a flag to track the plate recognition activity.

plate_cascade = cv2.CascadeClassifier(HAARCASCADE_FILE)  # We load our Haar Cascade classifier for license plate detection.
reader = easyocr.Reader(OCR_LANGUAGES)  # We initialize our OCR reader with the specified languages.
camera = None  # We initialize a variable to hold a camera object.
camera_active = False  # We have a flag to manage the camera's state.

def detect_plates(frame):
    """Detects potential license plates within a video frame."""

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # We convert the input frame to grayscale because Haar Cascades often work better on grayscale images.

    plates = plate_cascade.detectMultiScale(gray_frame, 1.1, 4)
    # We use our pre-loaded 'plate_cascade' (Haar Cascade Classifier) to detect potential license plate regions within the grayscale frame. The parameters (1.1, 4) control the detection sensitivity.

    detected_plates = []
    # We initialize an empty list to store the detected plates that meet our criteria.

    for (x, y, w, h) in plates:
        # We iterate through the potential regions returned by the 'detectMultiScale' function. 
        #  'x' and 'y' are the top-left coordinates of the region, 'w' is the width, and 'h' is the height.

        area = w * h
        # We calculate the area of the detected region.

        if area > MIN_PLATE_AREA:
            # We apply a threshold on the area to filter out small or irrelevant detections.
            detected_plates.append({
                'coordinates': (x, y, w, h), 
                # We store the coordinates of the region that passes the area check.
                'image': frame[y:y + h, x:x + w]  
                # We extract the image of the detected plate region from the original frame.
            })

    return detected_plates
    # We return the list of detected plates, each represented as a dictionary containing coordinates and the extracted plate image data. 

def extract_plate_text(plate_image):
    """Extracts and processes text from a license plate image."""

    result = reader.readtext(plate_image) 
    # We use our 'reader' (from the easyocr library) to attempt to extract text from the license plate image.

    if result: 
        # We check if the OCR reader was able to detect any text.
        raw_text = result[0][1]  
        # We retrieve the raw text from the first detected text region (easyocr can return multiple results).

        cleaned_text = re.sub(r'[^A-Za-z0-9]', '', raw_text) 
        # We use a regular expression to remove any non-alphanumeric characters from the raw text.
  
        if re.match(r'^[A-Z]{3}\d{4}$', cleaned_text):
            # We check if the cleaned text matches a specific pattern (like three uppercase letters followed by four digits). 
            return cleaned_text  
            # If the format is valid, we return the cleaned text.

    return None 
    # If no text is detected or the format is invalid, we return None.

def annotate_frame(frame, plates):
    """Adds annotations (bounding boxes and text) to a frame based on detected plates."""

    for plate in plates: 
        # We iterate through each plate in the list of detected plates.

        x, y, w, h = plate['coordinates'] 
        # We extract the coordinates (x, y, width, height) of the detected plate region from the 'plate' dictionary.

        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2) 
        # We draw a green (0, 255, 0) bounding box around the detected plate region using OpenCV's rectangle function.

        if 'text' in plate: 
            # We check if the OCR process was able to extract text for this plate.
            cv2.putText(frame, plate['text'], (x, y - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2) 
            # We add the recognized plate text above the bounding box using OpenCV's putText function. 

    return frame
    # We return the modified frame with annotations. 

def process_frame(frame): 
    """Processes a single video frame, performing plate detection, text extraction, and annotation."""

    if plate_recognition_active:  
        # We check if our global 'plate_recognition_active' flag is True. If not, we skip the processing.

        plates = detect_plates(frame)  
        # We call our 'detect_plates' function to find potential license plate regions within the frame.

        for plate in plates: 
            # We iterate through each detected plate.
            plate['text'] = extract_plate_text(plate['image'])  
            # We attempt to extract text from the plate's image using our 'extract_plate_text' function.

            if plate['text']: 
                # We check if text was successfully extracted.
                global latest_plate
                latest_plate = plate['text']   
                # We update our global 'latest_plate' variable with the recognized text.

        frame = annotate_frame(frame, plates)  
        # We add annotations (bounding boxes and text) to the frame based on the detected plates.

    return frame 
    # We return the processed frame, either with or without annotations.

def generate_frames():
    """Generates a continuous stream of JPEG-encoded video frames."""

    global camera_active  # We access the global 'camera_active' flag.

    while True:  
        # We create an infinite loop for continuous frame generation.

        if camera_active: 
            # We check if the camera is supposed to be active.
            success, frame = camera.read() 
            # We attempt to read a frame from the camera, 'success' will indicate if it worked.

            frame = process_frame(frame) 
            # We process the retrieved frame (detecting plates, adding annotations, etc.).

            if not success: 
                # We handle the case where the camera failed to provide a frame.
                break  # We exit the loop if the camera stops working.

            else:
                ret, buffer = cv2.imencode('.jpg', frame) 
                # We encode the processed frame as a JPEG image for efficient streaming.

                frame = buffer.tobytes() 
                # We convert the encoded buffer into a byte string.

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n') 
                # We yield the frame data in a format suitable for multipart HTTP video streaming.

 
def check_plate_in_database(plate_text): 
    """Checks if a given license plate number exists in the database (case-insensitive)."""

    vehicle = Vehicle.query.filter(Vehicle.plate_num.ilike(plate_text)).first()
    #  We use '.ilike()' for case-insensitive matching

    if vehicle:
        return True 
    else:  # Alternatively, you can remove the else block and simply 'return vehicle', since it will evaluate to True or False on its own
        return False 
    
@system.route('/turn_on')
def turn_on():
    global camera_active, camera

    # Initialize the camera if it doesn't exist 
    camera = None  
    if not camera:  
        camera = cv2.VideoCapture(1)  # Assuming '1' corresponds to your camera device

    # Activate the camera
    camera_active = True 
    return "Camera turned on"

@system.route('/turn_off')
def turn_off():
    global camera_active

    # Deactivate the camera  
    camera_active = False  

    # Release resources if camera was opened
    if camera.isOpened():  
        camera.release()
        cv2.destroyAllWindows()  # Close any OpenCV windows

    return "Camera turned off"

@system.route('/video_feed')
def video_feed():
    # Provide a streaming video feed using the generator function
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@system.route('/start_recognition')
def start_recognition():
    global plate_recognition_active

    # Enable the plate recognition process 
    plate_recognition_active = True  
    logging.info(f"Plate recognition activated by user: {current_user.username}")
    return "Plate Recognition Started"

@system.route('/stop_recognition')
def stop_recognition():
    global plate_recognition_active

    # Disable the plate recognition process
    plate_recognition_active = False  
    logging.info(f"Plate recognition deactivated by user: {current_user.username}")
    return "Plate Recognition Stopped"

@system.route('/get_latest_plate')
def get_latest_plate():
    global latest_plate, plate_recognition_active

    if plate_recognition_active and latest_plate:

        # Approval Logic
        approval_status = check_plate_in_database(latest_plate)  

        # Create EntryApproval record (always create new)
        client_id = None  
        vehicle = Vehicle.query.filter_by(plate_num=latest_plate).first()
        if vehicle:
            client_id = vehicle.client_id

        new_approval = EntryApproval(
            client_id=client_id,
            guard_id=current_user.guard_id,
            approval_status=approval_status,
            approval_time=datetime.now()
        )
        db.session.add(new_approval)

        # Login/Logout Logic (only if approved)
        if approval_status:  
            existing_login = LoginLogout.query.filter_by(
                client_id=client_id 
            ).order_by(LoginLogout.entry_id.desc()).first()

            if existing_login and existing_login.logout_time is None:
                existing_login.logout_time = datetime.now()
            else:
                new_login = LoginLogout(
                    client_id=client_id,
                    guard_id=current_user.guard_id,
                    login_time=datetime.now(),
                    plate_num = latest_plate
                )
                db.session.add(new_login)

        db.session.commit()
        temp = latest_plate
        latest_plate = None
        logging.info(f"Processed plate: {latest_plate}, status: {approval_status}")
        return jsonify({'status': 'approved' if approval_status else 'denied', 'plate': temp}) 
    else:
        return ''  


@system.route('/get_chart_data')
def get_chart_data():
    # Define time periods for analysis (dynamically get the current date)
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    morning_start = today_start + timedelta(hours=6)
    midmorning_start = today_start + timedelta(hours=9)
    midday_start = today_start + timedelta(hours=12)
    afternoon_start = today_start + timedelta(hours=15)
    night_start = today_start + timedelta(hours=18) 

    # Query for approval counts in each period
    morning_count = db.session.query(LoginLogout).filter(
        func.HOUR(LoginLogout.login_time) >= morning_start.hour,
        func.HOUR(LoginLogout.login_time) < midmorning_start.hour
    ).count()

    midmorning_count = db.session.query(LoginLogout).filter(
        func.HOUR(LoginLogout.login_time) >= midmorning_start.hour,
        func.HOUR(LoginLogout.login_time) < midday_start.hour
    ).count()

    midday_count = db.session.query(LoginLogout).filter(
        func.HOUR(LoginLogout.login_time) >= midday_start.hour,
        func.HOUR(LoginLogout.login_time) < afternoon_start.hour
    ).count()

    afternoon_count = db.session.query(LoginLogout).filter(
        func.HOUR(LoginLogout.login_time) >= afternoon_start.hour,
        func.HOUR(LoginLogout.login_time) < night_start.hour
    ).count()

    night_count = db.session.query(LoginLogout).filter(
        func.HOUR(LoginLogout.login_time) >= night_start.hour,
    ).count()  # Note: No upper bound since it's up to the end of the day

    # Create the data dictionary to return as JSON
    data = {
        'morning': morning_count,
        'midmorning': midmorning_count,
        'midday': midday_count,
        'afternoon': afternoon_count,
        'night': night_count
    }
    logging.info(data)
    return jsonify(data)

if __name__ == '__main__':
    None