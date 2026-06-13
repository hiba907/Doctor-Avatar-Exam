import os
import glob

def play_video(video_path):
    """Plays a video file using the default Windows player"""
    if os.path.exists(video_path):
        print(f"▶️ Playing: {video_path}")
        os.startfile(os.path.abspath(video_path))
    else:
        print(f"❌ Video not found: {video_path}")

# Option 1: Play a specific video
# Change this to match your video filename:
play_video("outputs/male_doctor.mp4")  # or "outputs/female_doctor.mp4"

# Option 2: Play the most recent video automatically
# Uncomment the lines below (remove the #) to always play the newest video:
# list_of_files = glob.glob('outputs/*.mp4')
# if list_of_files:
#     latest_video = max(list_of_files, key=os.path.getctime)
#     play_video(latest_video)
# else:
#     print("No videos found in outputs folder!")