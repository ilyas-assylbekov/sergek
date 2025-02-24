# src/backend/utils/frame_utils.py
import cv2
import pandas as pd
import os
import shutil

def save_top_frames(frame_confidences, output_dir, max_frames=5):
    """Save top confidence frames to directory"""
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # Sort by confidence and get top frames
    frame_confidences.sort(key=lambda x: x[2], reverse=True)
    top_frames = frame_confidences[:max_frames]
    
    saved_frames = []
    for i, (frame_idx, timestamp, conf, frame, bbox) in enumerate(top_frames):
        bbox = bbox[0]  # Unpack list
        cropped_img = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        filename = f"frame_{i}_{timestamp}.jpg"
        filepath = os.path.join(output_dir, filename)
        cv2.imwrite(filepath, cropped_img)
        saved_frames.append({
            "filename": filename,
            "timestamp": timestamp,
            "confidence": float(conf),
            "bbox": bbox
        })
    
    return saved_frames
