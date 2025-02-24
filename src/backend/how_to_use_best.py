import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
import cvzone
import torch
import datetime
def create_video_writer(video_cap, output_filename):

    # grab the width, height, and fps of the frames in the video stream.
    frame_width = int(640)
    frame_height = int(480)
    fps = int(video_cap.get(cv2.CAP_PROP_FPS))

    # initialize the FourCC and a video writer object
    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    writer = cv2.VideoWriter(output_filename, fourcc, fps,
                             (frame_width, frame_height))

    return writer


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = YOLO("best.pt").to(device)
frame_width = 640
frame_height = 480

video = cv2.VideoCapture("./videos/1.mp4")

if (video.isOpened()== False):
    print("Error opening video file")

start = datetime.datetime.now()
frame_skip = 3
frame_count = 0
writer = create_video_writer(video, "output.mp4")
preds = []

while True:    
    ret, frame = video.read()
    if not ret:
        break
    
    frame_count += 1
    if frame_count % frame_skip != 0:
        continue

    frame = cv2.resize(frame, (frame_width, frame_height))
    
    results = model.predict(frame, conf=0.3, agnostic_nms=False)
    anno = results[0]
    class_list = anno.names
    bboxes = pd.DataFrame(anno.boxes.data).astype("float")
   
    for index, row in bboxes.iterrows():
        x1 = int(row[0])
        y1 = int(row[1])
        x2 = int(row[2])
        y2 = int(row[3])
        d = int(row[5])
        c = class_list[d]

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
        cvzone.putTextRect(frame, f'accident', (x1, y1), 1, 1)

        cropped_img = frame[y1:y2, x1:x2]
        # cv2.imshow("cropped", cropped_img)
        preds.append(["1.mp4", frame_count, [[x1, y1, x2, y2]]])
            
    writer.write(frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

df = pd.DataFrame(preds, columns=["Filename", "Frame", "Bbox"])
df.to_csv("predictions.csv", index=False)
end = datetime.datetime.now()
print(f"Time to process: {(end - start).total_seconds() * 1000:.0f} milliseconds")
video.release()
writer.release()
cv2.destroyAllWindows()