import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
import torch
import datetime
import os
import shutil


def create_video_writer(video_cap, output_filename):
    frame_width = int(video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(video_cap.get(cv2.CAP_PROP_FPS))

    if fps == 0:
        fps = 30  # Default FPS if reading fails

    print(f"Creating VideoWriter - FPS: {fps}, Width: {frame_width}, Height: {frame_height}")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'mp4v' for compatibility
    return cv2.VideoWriter(output_filename, fourcc, fps, (frame_width, frame_height)), fps


# Select device
device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
model = YOLO("LongFineTune.pt").to(device)

video_filename = "./test_data/113.mov"
video = cv2.VideoCapture(video_filename)
if not video.isOpened():
    print("Error opening video file")
    exit()

# Ensure directory is recreated
output_dir = "top_confidence_frames"
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)  # Remove existing directory
os.makedirs(output_dir)  # Create new directory

start = datetime.datetime.now()
frame_skip = 1  # Process all frames (increase later if needed)

# Step 1: Process the video and detect objects
writer, fps = create_video_writer(video, "output_all_detections.mp4")

frame_skip = 3
frame_count = 0
frame_confidences = []  # Store frame indices and their highest confidence
saved_top_frames = []

while True:
    ret, frame = video.read()
    if not ret:
        break

    frame_count += 1
    if frame_count % frame_skip != 0:
        continue

    results = model.predict(frame, conf=0.7, agnostic_nms=False)
    anno = results[0]
    class_list = anno.names

    bboxes = pd.DataFrame(anno.boxes.data.cpu().numpy()).astype("float")

    max_conf = 0  # Track max confidence in the frame
    for _, row in bboxes.iterrows():
        confidence = row[4]
        d = int(row[5])
        x1, y1, x2, y2 = row[:4].astype(int).tolist()
        label = f"{class_list[d]}: {confidence:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        timestamp = frame_count / fps  # Convert frame index to seconds
        frame_confidences.append((frame_count, timestamp, confidence, frame.copy(), [[x1, y1, x2, y2]]))

    # Write processed frame
    if writer.isOpened():
        writer.write(frame)

video.release()
writer.release()
cv2.destroyAllWindows()

frame_confidences.sort(key=lambda x: x[2], reverse=True)  # Sort by confidence
top_frames = frame_confidences[:5]  # Get top 5

for i, (frame_idx, timestamp, conf, frame, bbox) in enumerate(top_frames):
    bbox = bbox[0]  # Unpack lis
    cropped_img = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
    filename = f"./top_confidence_frames/topframe_{i}_{timestamp}.jpg"
    cv2.imwrite(filename, cropped_img)

print(f"Saved top 5 frames: {saved_top_frames}")
end = datetime.datetime.now()
print(f"Time to process: {(end - start).total_seconds() * 1000:.0f} milliseconds")