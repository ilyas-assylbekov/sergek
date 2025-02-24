import pandas as pd
import cv2
from vlm import get_desc
from os import walk

filenames = next(walk("./top_confidence_frames/"), (None, None, []))[2]

results = []

for fn in filenames:
    time = fn.split("_")[-1].split(".")[0]
    filename = "video1.mp4"

    desc = get_desc("./top_confidence_frames/" + fn)
    results.append((filename, time, desc))
    print(desc)

df = pd.DataFrame(results, columns=["Filename", "Time", "Description"])
df.to_csv("predictions.csv", index=False)
