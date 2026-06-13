# 🎓 MLS Case Exam Simulator
**AI-powered medical oral exam with Dr. Hiba Hamdar**  
Built by the Academy of Medical Learning Skills (MLS)

---

## What It Does

This is a **desktop exam simulator** where medical students sit a live oral exam with Dr. Hiba Hamdar — an AI avatar that asks questions, listens to spoken answers, grades them using a local LLM, and gives real-time feedback. Dr. Hiba's face appears on screen throughout the exam, reacting with the correct body language for each moment.

---

## How It Works

```
Student picks a case (from cases/)
        ↓
Dr. Hiba asks question (pre-recorded video loops + edge-tts voice)
        ↓
Student speaks their answer (microphone)
        ↓
Llama3 grades the answer against ideal keywords
        ↓
Dr. Hiba reacts (correct.mp4 or incorrect.mp4) + gives feedback
        ↓
Next question → repeat until case is complete
        ↓
Teaching points + closing
```

---

## Project Structure

```
Doctor_Avatar_Project/
├── main.py               ← Main exam simulator
├── generate_clips.py     ← Generates the 8 video clips (run once)
├── play-doctor.py        ← Video player utility
│
├── cases/                ← 16 medical exam cases (JSON)
│   ├── cardiology_001.json
│   ├── neurology_001.json
│   └── ...
│
├── clips/                ← Pre-recorded Dr. Hiba video clips
│   ├── intro.mp4
│   ├── thinking.mp4
│   ├── correct.mp4
│   ├── incorrect.mp4
│   ├── question.mp4
│   ├── explaining.mp4
│   ├── nodding.mp4
│   └── neutral.mp4
│
├── inputs/               ← Dr. Hiba's photo (doctor.png)
├── temp/                 ← Auto-generated audio files (temporary)
├── outputs/              ← SadTalker video output folder
└── SadTalker-main/       ← AI talking face generator
```

> ⚠️ `clips/`, `inputs/`, `temp/`, `outputs/`, and `SadTalker-main/` are excluded from Git (see `.gitignore`). Generate them locally following the setup steps below.

---

## Requirements

### Software
- Python 3.11
- [Ollama](https://ollama.com) — local LLM runner
- [SadTalker](https://github.com/OpenTalker/SadTalker) — AI talking face generator
- A working microphone

### Python Libraries

```bash
pip install speechrecognition edge-tts ollama pygame opencv-python pyaudio
```

---

## Setup (Run Once)

### 1. Add Dr. Hiba's photo
Place a clear, front-facing photo of Dr. Hiba in:
```
inputs/doctor.png
```

### 2. Install SadTalker
```bash
cd SadTalker-main
pip install -r requirements.txt
python scripts/download_models.py
```

### 3. Increase Windows virtual memory (important)
SadTalker needs extra memory. Go to:
`System Properties → Advanced → Performance → Virtual Memory`  
Set C: drive to **Initial: 8000 MB / Maximum: 16000 MB**  
Then restart your PC.

### 4. Generate the 8 video clips
```bash
cd Doctor_Avatar_Project
python generate_clips.py
```
This runs SadTalker for each clip and saves them to `clips/`. Takes about 10–20 minutes total. Only needs to be done once.

---

## Running the Exam

You need **two PowerShell windows** open at the same time.

**Window 1 — Start Ollama:**
```powershell
ollama serve
```

**Window 2 — Start the exam:**
```powershell
cd C:\Users\TD\Desktop\Doctor_Avatar_Project
python main.py
```

Then:
1. Pick a case number from the list
2. Listen to Dr. Hiba's question
3. Speak your answer into the microphone
4. Dr. Hiba will grade and give feedback
5. Continue until the case is complete

---

## Case JSON Format

Each case in `cases/` follows this structure:

```json
{
  "title": "Acute Myocardial Infarction",
  "specialty": "Cardiology",
  "difficulty": "intermediate",
  "patient_intro": "58-year-old male with crushing chest pain radiating to left arm for 2 hours.",
  "examiner_questions": [
    {
      "question": "What is your immediate management of this patient?",
      "ideal_answer_keywords": [
        "aspirin", "ECG", "troponin", "oxygen", "IV access", "cath lab"
      ]
    }
  ],
  "teaching_points": [
    "Door-to-balloon time must be under 90 minutes.",
    "Always give aspirin 300mg immediately unless contraindicated."
  ]
}
```

---

## The 8 Video Clips

| Clip | When it plays |
|------|--------------|
| `intro.mp4` | Opening of every exam |
| `question.mp4` | Dr. Hiba is asking a question |
| `thinking.mp4` | Waiting for the student to answer |
| `correct.mp4` | Student gave a good answer |
| `incorrect.mp4` | Student's answer was incomplete or wrong |
| `explaining.mp4` | Teaching points and explanations |
| `nodding.mp4` | Neutral listening |
| `neutral.mp4` | Fallback / transitions |

All 8 clips are reused across all 16 cases. They are generated once from Dr. Hiba's photo using SadTalker + edge-tts.

---

## Voice

Dr. Hiba's voice is `en-US-AriaNeural` via Microsoft edge-tts.  
To change the voice, update this line in `main.py`:
```python
DOCTOR_VOICE = "en-US-AriaNeural"
```

---

## Connection to MLS Virtual Hospital

This project is designed to work alongside the [MLS Virtual Hospital](https://github.com/hiba907/MLS-Virtual-Hospital) web platform.

To launch the exam from within the MLS hospital:
```python
# Add to app.py in MLS Virtual Hospital
elif p == "case_exam":
    if st.button("🚀 Launch Exam Simulator"):
        import subprocess
        subprocess.Popen(["python", r"C:\Users\TD\Desktop\Doctor_Avatar_Project\main.py"])
        st.success("✅ Exam launched! Check your desktop.")
```

Exam scores can be saved to a shared `scores.json` file and read back by the MLS leaderboard.

---

## Author

**Dr. Hiba Hamdar**  
Academy of Medical Learning Skills (MLS)  
📧 hamdarhiba95@gmail.com

---

© 2026 Hiba Hamdar — All rights reserved. Proprietary software.
