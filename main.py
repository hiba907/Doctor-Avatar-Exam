import os
import json
import asyncio
import speech_recognition as sr
import edge_tts
import ollama
import threading
import pygame
import cv2
from pathlib import Path

# ---------- DOCTOR CONFIGURATION ----------
DOCTOR_NAME  = "Dr. Hiba Hamdar"
DOCTOR_IMAGE = "inputs/doctor.png"
DOCTOR_VOICE = "en-US-AriaNeural"
CASES_DIR    = "cases"

# ---------- VIDEO CLIPS CONFIGURATION ----------
CLIPS = {
    "intro":      "clips/intro.mp4",
    "thinking":   "clips/thinking.mp4",
    "correct":    "clips/correct.mp4",
    "incorrect":  "clips/incorrect.mp4",
    "question":   "clips/question.mp4",
    "explaining": "clips/explaining.mp4",
    "nodding":    "clips/nodding.mp4",
    "neutral":    "clips/neutral.mp4",
}

# Global stop flag
stop_video = False

os.makedirs("temp", exist_ok=True)
os.makedirs("clips", exist_ok=True)

# ---------- SMART CLIP SELECTOR ----------
def select_clip(text):
    text_lower = text.lower()

    if any(w in text_lower for w in ["welcome", "i am dr", "today we"]):
        return CLIPS["intro"]
    elif any(w in text_lower for w in ["correct", "well done", "excellent",
                                        "good", "right", "perfect"]):
        return CLIPS["correct"]
    elif any(w in text_lower for w in ["incorrect", "not quite", "wrong",
                                        "unfortunately", "missed"]):
        return CLIPS["incorrect"]
    elif any(w in text_lower for w in ["question", "what is", "how would",
                                        "explain", "describe", "can you"]):
        return CLIPS["question"]
    elif any(w in text_lower for w in ["because", "mechanism", "therefore",
                                        "the reason", "this means"]):
        return CLIPS["explaining"]
    elif any(w in text_lower for w in ["let me think", "interesting", "hmm"]):
        return CLIPS["thinking"]
    else:
        return CLIPS["nodding"]

# ---------- 1. VIDEO PLAYER (OpenCV - Python Controlled) ----------
def play_clip_controlled(clip_path):
    """
    Play a video clip using OpenCV.
    Loops the clip until stop_video is True.
    """
    global stop_video

    if not os.path.exists(clip_path):
        print(f"⚠️ Clip not found: {clip_path}")
        return

    cap = cv2.VideoCapture(clip_path)
    if not cap.isOpened():
        print(f"❌ Could not open clip: {clip_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    wait_ms = int(1000 / fps) if fps > 0 else 33

    print(f"🎬 Playing: {clip_path}")

    while not stop_video:
        ret, frame = cap.read()

        # Loop clip when it ends
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # Show frame
        cv2.imshow("Dr. Hiba Hamdar - Medical Exam", frame)

        # Press Q to quit
        if cv2.waitKey(wait_ms) & 0xFF == ord('q'):
            break

    cap.release()

def stop_current_clip():
    """Stop the currently playing clip instantly"""
    global stop_video
    stop_video = True

def start_clip(clip_path):
    """Start a clip in a background thread"""
    global stop_video
    stop_video = False
    t = threading.Thread(
        target=play_clip_controlled,
        args=(clip_path,),
        daemon=True
    )
    t.start()
    return t

# ---------- 2. THE VOICE (edge-tts + pygame) ----------
async def generate_audio(text):
    temp_file = "temp/response.mp3"
    communicate = edge_tts.Communicate(text, DOCTOR_VOICE)
    await communicate.save(temp_file)
    return temp_file

def play_audio(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()

def speak(text):
    """Generate and play voice audio"""
    audio_file = asyncio.run(generate_audio(text))
    play_audio(audio_file)

# ---------- 3. PLAY CLIP + SPEAK TOGETHER ----------
def play_clip_and_speak(text):
    """
    1. Pick the correct body language clip
    2. Start playing it in background
    3. Speak the text
    4. Stop the clip when speech ends
    """
    global stop_video

    # Pick correct clip based on what Dr Hiba is saying
    clip = select_clip(text)

    # Start clip in background
    start_clip(clip)

    # Speak (blocks until finished)
    speak(text)

    # Speech done - stop clip
    stop_current_clip()
    cv2.destroyAllWindows()

# ---------- 4. THE EAR (LISTEN) ----------
def listen_to_student():
    """
    While listening, play the thinking clip.
    Stop it when student finishes speaking.
    """
    global stop_video

    recognizer = sr.Recognizer()

    # Play thinking clip while waiting for student
    start_clip(CLIPS["thinking"])

    print("\n" + "="*60)
    print(f"🎤 {DOCTOR_NAME} IS LISTENING... (speak now)")
    print("="*60)

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    # Student finished - stop thinking clip
    stop_current_clip()
    cv2.destroyAllWindows()

    try:
        text = recognizer.recognize_google(audio)
        print(f"👨‍🎓 STUDENT: {text}")
        return text
    except sr.UnknownValueError:
        print("❌ Could not understand. Try again.")
        return ""
    except sr.RequestError:
        print("❌ Network error.")
        return ""

# ---------- 5. THE BRAIN (LLM GRADING) ----------
def grade_answer_with_llm(question_text, ideal_keywords, student_answer):
    """
    Use Llama3 to grade the student's answer
    based on ideal_answer_keywords from the JSON.
    """
    kw_text = ", ".join(ideal_keywords)

    system_prompt = (
        f"You are {DOCTOR_NAME}, a strict but supportive medical examiner.\n"
        "You are given:\n"
        "- The exam question.\n"
        "- A list of ideal answer keywords.\n"
        "- The student's spoken answer.\n\n"
        "Your job:\n"
        "1. State in one short sentence if the answer is "
        "excellent, good, partial, or incorrect.\n"
        "2. Briefly list the most important concepts "
        "they missed or got wrong.\n"
        "3. Provide a concise model answer (1-2 sentences) "
        "that covers the key points.\n"
        "Keep your total reply under 4 sentences."
    )

    user_prompt = (
        f"Question: {question_text}\n\n"
        f"Ideal answer keywords: {kw_text}\n\n"
        f"Student answer: {student_answer}\n"
    )

    try:
        response = ollama.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
        )
        return response["message"]["content"]
    except Exception as e:
        print(f"❌ Ollama error: {e}")
        return "I am experiencing a technical issue grading this answer."

# ---------- 6. CASE LOADING ----------
def load_cases():
    cases = []
    cases_path = Path(CASES_DIR)

    if not cases_path.exists():
        print(f"❌ Folder '{CASES_DIR}' not found.")
        raise SystemExit

    for p in sorted(cases_path.glob("*.json")):
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        title = data.get("title", p.name)
        cases.append({"path": p, "data": data, "title": title})

    if not cases:
        print(f"❌ No JSON files found in '{CASES_DIR}'.")
        raise SystemExit

    return cases

def choose_case(cases):
    print("\n📋 Available cases:\n")
    for i, c in enumerate(cases, start=1):
        title      = c["title"]
        specialty  = c["data"].get("specialty", "Unknown")
        difficulty = c["data"].get("difficulty", "unknown")
        print(f"  {i}. {title}")
        print(f"     [{specialty} | Difficulty: {difficulty}]\n")

    while True:
        choice = input(f"Type the case number (1–{len(cases)}): ")
        try:
            idx = int(choice)
            if 1 <= idx <= len(cases):
                return cases[idx - 1]
        except ValueError:
            pass
        print("Invalid choice. Try again.")

# ---------- 7. RUN ONE CASE EXAM ----------
def run_case_exam(case_data):
    title      = case_data.get("title",      "Untitled case")
    specialty  = case_data.get("specialty",  "Unknown specialty")
    difficulty = case_data.get("difficulty", "unknown")
    exam_qs    = case_data.get("examiner_questions", [])
    teaching   = case_data.get("teaching_points",    [])

    # --- Intro ---
    intro = (
        f"Welcome to your exam. I am {DOCTOR_NAME}. "
        f"You have selected the case titled: {title}, "
        f"in the field of {specialty}, "
        f"with difficulty level {difficulty}. "
        f"I will ask you {len(exam_qs)} structured questions "
        f"based on this case. Let us begin."
    )
    print(f"\n👩‍⚕️ {DOCTOR_NAME}: {intro}")
    play_clip_and_speak(intro)

    # --- Questions loop ---
    for i, q in enumerate(exam_qs, start=1):
        q_text         = q.get("question", "").strip()
        ideal_keywords = q.get("ideal_answer_keywords", [])

        if not q_text:
            continue

        # Ask question
        question_spoken = f"Question {i}. {q_text}"
        print(f"\n👩‍⚕️ {DOCTOR_NAME}: {question_spoken}")
        play_clip_and_speak(question_spoken)

        # Listen to student
        student_answer = listen_to_student()
        if not student_answer:
            # Could not hear - ask again politely
            play_clip_and_speak(
                "I did not catch that. Could you please repeat your answer?"
            )
            student_answer = listen_to_student()
            if not student_answer:
                play_clip_and_speak(
                    "Let us move on to the next question."
                )
                continue

        # Grade answer
        feedback = grade_answer_with_llm(q_text, ideal_keywords, student_answer)
        print(f"\n👩‍⚕️ {DOCTOR_NAME}: {feedback}")
        play_clip_and_speak(feedback)

    # --- Teaching points at the end ---
    if teaching:
        tp_text = (
            "We have reached the end of this case. "
            "Here are the key teaching points: "
            + " ".join(teaching)
        )
        print(f"\n👩‍⚕️ {DOCTOR_NAME}: {tp_text}")
        play_clip_and_speak(tp_text)

    # --- Closing ---
    closing = (
        f"That concludes your exam on this case. "
        f"Well done for completing it. "
        f"I hope this was a valuable learning experience. "
        f"Goodbye."
    )
    print(f"\n👩‍⚕️ {DOCTOR_NAME}: {closing}")
    play_clip_and_speak(closing)

# ---------- 8. MAIN ----------
def run_exam():
    print("\n" + "="*60)
    print("🏥  MEDICAL EXAM SIMULATOR")
    print(f"👩‍⚕️  Examiner : {DOCTOR_NAME}")
    print(f"🎙️  Voice    : {DOCTOR_VOICE}")
    print(f"📁  Cases    : {CASES_DIR}/")
    print("="*60)

    cases    = load_cases()
    selected = choose_case(cases)
    print(f"\n📄 Selected: {selected['path'].name}\n")

    run_case_exam(selected["data"])

if __name__ == "__main__":
    run_exam()