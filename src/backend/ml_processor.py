# src/backend/ml_processor.py
import asyncio
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO
import torch
import cvzone
import os
import pandas as pd
import sys

async def process_video(input_path: str, output_path: str, show_preview: bool = False):
    """Process video using YOLO model"""
    try:
        # Initialize YOLO model
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = YOLO("LongFineTune.pt").to(device)
        
        # Open video
        video = cv2.VideoCapture(input_path)
        fps = int(video.get(cv2.CAP_PROP_FPS))
        if not video.isOpened():
            raise Exception("Error opening video file")
            
        # Get video properties
        frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(video.get(cv2.CAP_PROP_FPS))
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(
            output_path,
            fourcc,
            fps,
            (frame_width, frame_height)
        )
        
        frame_count = 0
        preds = []  # Store predictions
        
        while True:
            ret, frame = video.read()
            if not ret:
                break
                
            frame_count += 1
                
            # Run detection
            results = model.predict(frame, conf=0.3, agnostic_nms=False)
            anno = results[0].cpu()
            class_list = anno.names
            
            # Convert boxes to DataFrame for easier processing
            bboxes = pd.DataFrame(anno.boxes.data).astype("float")
            
            # Draw detections
            annotated_frame = frame.copy()
            for index, row in bboxes.iterrows():
                x1, y1, x2, y2 = map(int, row[:4])
                conf = row[4]
                cls_id = int(row[5])
                cls_name = class_list[cls_id]
                
                # Draw rectangle and label
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cvzone.putTextRect(
                    annotated_frame,
                    f'accident {conf:.2f}',  # Changed label to 'accident'
                    (x1, y1),
                    1,
                    1
                )
                
                # Store prediction
                preds.append([
                    os.path.basename(input_path),
                    frame_count,
                    [[x1, y1, x2, y2]]
                ])
            
            # Write frame
            out.write(annotated_frame)

            # Show preview if requested
            if show_preview:
                preview_width = 800
                aspect_ratio = frame_width / frame_height
                preview_height = int(preview_width / aspect_ratio)
                preview_frame = cv2.resize(annotated_frame, (preview_width, preview_height))
                cv2.imshow('Processing Preview', preview_frame)
                # Break loop if 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\nProcessing interrupted by user")
                    break
            
        # Release resources
        video.release()
        out.release()
        if show_preview:
            cv2.destroyAllWindows()

        # Save predictions to CSV
        pred_df = pd.DataFrame(preds, columns=["Filename", "Frame", "Bbox"])
        pred_df["FPS"] = fps
        csv_path = output_path.rsplit('.', 1)[0] + '_predictions.csv'
        pred_df.to_csv(csv_path, index=False)

        # Convert to compatible format
        if not output_path.endswith('.mp4'):
            mp4_output = output_path.rsplit('.', 1)[0] + '.mp4'
            os.system(f'ffmpeg -i {output_path} -vcodec h264 {mp4_output}')
            os.replace(mp4_output, output_path)

        temp_output = output_path + "_temp.mp4"
        os.system(f'ffmpeg -i {output_path} -vcodec libx264 -acodec aac {temp_output}')
        os.replace(temp_output, output_path)
        
        print(f"Video saved at: {output_path}")
        print(f"Predictions saved at: {csv_path}")
        print(f"File exists: {os.path.exists(output_path)}")
        
    except Exception as e:
        print(f"Error processing video: {e}")
        raise

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python -m ml_processor <input_path> [output_path]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) == 3 else "processed.mp4"
    asyncio.run(process_video(input_path, output_path, show_preview=True))