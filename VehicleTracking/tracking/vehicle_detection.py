import cv2
import easyocr
from ultralytics import YOLO

# Initialize EasyOCR reader for English text
reader = easyocr.Reader(['en'])

def detect_number_plate(frame, bounding_box):
    x1, y1, x2, y2 = bounding_box
    vehicle_region = frame[y1:y2, x1:x2]
    result = reader.readtext(vehicle_region)
    for detection in result:
        text = detection[1]
        if len(text) > 5 and any(char.isdigit() for char in text):
            return text
    return None

def calculate_speed(prev_position, current_position, fps, meters_per_pixel):
    if not prev_position or not current_position:
        return 0  # No speed if position data is incomplete

    # Distance between two positions in pixels
    pixel_distance = ((current_position[0] - prev_position[0]) ** 2 +
                      (current_position[1] - prev_position[1]) ** 2) ** 0.5

    # Convert pixel distance to meters
    distance_meters = pixel_distance * meters_per_pixel

    # Time between frames in seconds
    time_seconds = 1 / fps

    if time_seconds == 0:  # Avoid division by zero
        return 0

    # Speed in meters per second
    speed_mps = distance_meters / time_seconds

    # Convert to kilometers per hour (km/h)
    speed_kmh = speed_mps * 3.6

    # Apply a sanity check to filter out unrealistic speeds
    if speed_kmh > 300:  # 300 km/h is an upper bound for typical vehicles
        return 0

    return round(speed_kmh, 2)

def detect_vehicles(video_path, speed_limit, meters_per_pixel):
    model = YOLO("yolov8n.pt")  # Load the YOLOv8 model
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return {"status": "error", "message": "Could not open video file"}

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        return {"status": "error", "message": "Invalid FPS value from the video"}

    frame_count = 0
    prev_positions = {}
    overspeeding_vehicles = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Process every 20th frame for performance
        if frame_count % 20 == 0:
            results = model(frame)

            for i, box in enumerate(results[0].boxes.xyxy):
                box = box.cpu().numpy() if hasattr(box, "cpu") else box.numpy()

                if len(box) < 4:
                    continue

                x1, y1, x2, y2 = map(int, box[:4])  # Extract coordinates safely
                vehicle_position = ((x1 + x2) // 2, (y1 + y2) // 2)  # Center of the box

                if i in prev_positions:
                    prev_position = prev_positions[i]
                    speed = calculate_speed(prev_position, vehicle_position, fps, meters_per_pixel)

                    if speed > speed_limit:
                        number_plate = detect_number_plate(frame, (x1, y1, x2, y2))
                        if number_plate:
                            overspeeding_vehicles.append({
                                "vehicle_id": number_plate,
                                "speed": speed,
                            })

                prev_positions[i] = vehicle_position

    cap.release()

    if not overspeeding_vehicles:
        return {
            "status": "success",
            "message": "No overspeeding vehicles detected.",
            "data": []
        }

    return {
        "status": "success",
        "message": f"{len(overspeeding_vehicles)} overspeeding vehicle(s) detected.",
        "data": overspeeding_vehicles
    }
