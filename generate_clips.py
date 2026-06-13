import asyncio
import edge_tts
import subprocess
import os
import glob
from pathlib import Path

# Configuration
DOCTOR_IMAGE = "inputs/doctor.png"
DOCTOR_VOICE = "en-US-AriaNeural"
SADTALKER_DIR = "SadTalker-main"
CLIPS_DIR = "clips"

os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs("temp", exist_ok=True)

# The 8 short phrases for each clip type
CLIP_PHRASES = {
    "intro":      "Welcome to your medical exam. I am Dr. Hiba Hamdar.",
    "thinking":   "Hmm, let me consider your answer carefully.",
    "correct":    "Excellent answer! That is correct. Well done.",
    "incorrect":  "That is not quite right. Let me help you.",
    "question":   "Here is your next question. Please think carefully.",
    "explaining": "The key concept here is very important to understand.",
    "nodding":    "I see. Please continue with your answer.",
    "neutral":    "Take your time. I am listening.",
}

async def generate_audio(phrase, voice, output_path):
    """Generate audio file using edge-tts"""
    communicate = edge_tts.Communicate(phrase, voice)
    await communicate.save(output_path)
    print(f"✅ Audio generated: {output_path}")

def run_sadtalker(audio_path, image_path, output_dir):
    """Run SadTalker to generate a lip-sync video"""
    print(f"🎬 Running SadTalker for: {audio_path}")
    command = (
        f"cd {SADTALKER_DIR} && "
        f"python inference.py "
        f"--driven_audio ../{audio_path} "
        f"--source_image ../{image_path} "
        f"--result_dir ../{output_dir} "
        f"--still "
        f"--size 256 "
        f"--preprocess crop "
        f"--batch_size 1"
    )
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ SadTalker error: {result.stderr}")
        return False
    return True

def stitch_video_ffmpeg(frames_dir, output_path):
    """Use ffmpeg to stitch PNG frames into a video"""
    print(f"🎞️ Stitching frames into: {output_path}")
    command = (
        f'ffmpeg -y -framerate 25 -i "{frames_dir}/%04d.png" '
        f'-c:v libx264 -pix_fmt yuv420p "{output_path}"'
    )
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ FFmpeg error: {result.stderr}")
        return False
    print(f"✅ Video saved: {output_path}")
    return True

def find_latest_output_folder():
    """Find the most recently created folder in outputs/"""
    folders = [f for f in Path("outputs").iterdir() if f.is_dir()]
    if not folders:
        return None
    return max(folders, key=os.path.getctime)

def generate_clip(clip_name, phrase):
    """Full pipeline: text → audio → SadTalker → ffmpeg → final clip"""
    print(f"\n{'='*60}")
    print(f"🎬 Generating clip: {clip_name}")
    print(f"📝 Phrase: {phrase}")
    print(f"{'='*60}")

    # Step 1: Generate audio
    audio_path = f"temp/{clip_name}_audio.wav"
    asyncio.run(generate_audio(phrase, DOCTOR_VOICE, audio_path))

    # Step 2: Run SadTalker
    success = run_sadtalker(audio_path, DOCTOR_IMAGE, "outputs")
    if not success:
        print(f"❌ SadTalker failed for {clip_name}")
        return False

    # Step 3: Find the output folder SadTalker just created
    latest_folder = find_latest_output_folder()
    if not latest_folder:
        print(f"❌ Could not find SadTalker output folder")
        return False

    # Step 4: Find frames folder
    frames_dir = latest_folder / "first_frame_dir"
    if not frames_dir.exists():
        print(f"❌ Frames folder not found: {frames_dir}")
        return False

    # Step 5: Stitch frames into video
    final_clip_path = f"{CLIPS_DIR}/{clip_name}.mp4"
    success = stitch_video_ffmpeg(str(frames_dir), final_clip_path)
    if not success:
        print(f"❌ FFmpeg failed for {clip_name}")
        return False

    print(f"✅ Clip ready: {final_clip_path}")
    return True

def generate_all_clips():
    print("\n" + "="*60)
    print("🏥 DR. HIBA HAMDAR - CLIP GENERATOR")
    print("This will generate 8 short video clips.")
    print("Each clip takes about 10-20 minutes.")
    print("Total time: approximately 2-3 hours.")
    print("You only need to do this ONCE!")
    print("="*60)

    # Check if clips already exist
    existing = []
    missing = []
    for name in CLIP_PHRASES:
        clip_path = f"{CLIPS_DIR}/{name}.mp4"
        if os.path.exists(clip_path):
            existing.append(name)
        else:
            missing.append(name)

    if existing:
        print(f"\n✅ Already generated: {', '.join(existing)}")
    if missing:
        print(f"⏳ Still need to generate: {', '.join(missing)}")

    if not missing:
        print("\n🎉 All clips already exist! You are ready to run main.py")
        return

    print(f"\nGenerating {len(missing)} missing clips...")
    input("Press Enter to start generating clips (Ctrl+C to cancel)...")

    failed = []
    for name in missing:
        phrase = CLIP_PHRASES[name]
        success = generate_clip(name, phrase)
        if not success:
            failed.append(name)

    print("\n" + "="*60)
    print("📊 GENERATION COMPLETE!")
    print(f"✅ Successfully generated: "
          f"{len(missing) - len(failed)}/{len(missing)} clips")
    if failed:
        print(f"❌ Failed clips: {', '.join(failed)}")
        print("You can re-run this script to retry failed clips.")
    else:
        print("🎉 All clips ready! Run: python main.py")
    print("="*60)

if __name__ == "__main__":
    generate_all_clips()