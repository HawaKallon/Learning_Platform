# 🎓 AI-Driven Personalized Tutor for SSS (Sierra Leone Curriculum)

This system is an intelligent tutor designed to generate highly personalized and structured lesson notes, including **WAEC-style solved examples and practice exercises**, based on the Sierra Leone Senior Secondary School (SSS) curriculum.

It uses **Retrieval-Augmented Generation (RAG)** to ensure the content is directly mapped to the official subject syllabi and leverages a powerful Large Language Model (LLM) to tailor the pace (Low, Moderate, Advance) for individual students.

## ✨ Features

- **Curriculum-Aligned:** All content is grounded in subject PDFs placed in the `curriculum_data` folder.
- **Multi-Subject Support:** Supports any number of subjects with automatic discovery and loading.
- **Intelligent Caching (Persistence):** Uses file hashing to automatically skip redundant chunking/embedding processes if a subject's curriculum files haven't changed.
- **Personalized Pace:** Generates lessons tailored for beginner (`low`), standard (`moderate`), or advanced (`advance`) learners.
- **WAEC Fidelity:** Solved examples and practice questions are generated to replicate the **style, phrasing, and difficulty** of actual WAEC past examination questions.
- **Step-by-Step Solutions:** For quantitative subjects (like Mathematics/Science), solutions are broken down into clear, instructional steps.

---

## ⚙️ System Requirements

- Python 3.9+
- Access to the internet (for the LLM API and model downloads)
- **HuggingFace API Token** (required for the LLM)

---

## 🚀 Setup and Installation

### 1. Install Dependencies

Install all required Python libraries using pip (recommended):

```bash
pip install -r requirements.txt
```

Alternatively, install the core packages manually:

```bash
pip install python-dotenv langchain langchain-huggingface pypdf faiss-cpu fastapi uvicorn
```

### 2. Configure the Environment

Create a file named **`.env`** in the root directory and add your HuggingFace API token:

```env
# Get your token from HuggingFace Settings -> Access Tokens
HUGGINGFACEHUB_API_TOKEN="hf_YOUR_SECRET_TOKEN_HERE" 
```

### 3. Setup Curriculum Data Structure

Create two required folders in your project root:

```text
.
├── curriculum_data/
└── vectorstores/
```

Populate the `curriculum_data` folder with your curriculum PDFs, organized by subject folder:

```text
curriculum_data/
├── Mathematics/
│   └── SSS-Syllabus-Mathematics-for-STEAMM.pdf
├── English/
│   └── SSS-Syllabus-English-Language.pdf
└── Science/
    └── SSS-Syllabus-Integrated-Science.pdf
```

*Note: The `vectorstores` folder will be populated automatically when you run the system.*

---

## ▶️ How to Run the Tutor

You can run the system in two ways: CLI mode or API server mode.

### Option A) CLI Mode (Interactive)

Run the interactive script from your terminal:

```bash
python rag.py
```

### Option B) API Server (FastAPI)

Start the HTTP API server (serves Swagger docs at /docs):

```bash
python main.py
```

The server defaults to `http://localhost:8002`.

### Initialization Process

1. **First Run (Batch Building):** The system will check all curriculum folders. For any subject that has not been processed or if a PDF has been changed, it will trigger **`BUILDING NEW VECTORSTORE`**. This is the initial chunking and embedding process, which can take a few minutes.
2. **Subsequent Runs (Cached Loading):** If the PDF files have not changed, the system will instantly print **`LOADING CACHED VECTORSTORE`** for all subjects, making the startup nearly instantaneous.

For the API server, vectorstores are lazily initialized on the first request for a subject.

---

## 📝 Usage Guide

### CLI Mode

Once the system is initialized, you will be prompted for the lesson details:

1. **Enter Subject:** Choose from the list of discovered subjects (e.g., `Mathematics`, `English`, `Science`).
2. **Enter Lesson Topic:** The specific concept (e.g., `Phrases`, `Matrices`, `Acids and Bases`).
3. **Enter SSS Level:** The year level (`1`, `2`, or `3`).
4. **Enter Learning Pace:** The depth and complexity of the lesson (`low`, `moderate`, or `advance`).

**Example Interaction:**

```text
================================================================================
🎓 AI-DRIVEN PERSONALIZED TUTOR (SSS CURRICULUM)
================================================================================
...
📚 Enter Subject (English/Mathematics/Science): Mathematics
📝 Enter Lesson Topic: Matrices
🧑‍🎓 Enter SSS Level (1, 2, or 3): 3
🏃‍♀️ Enter Learning Pace (low, moderate, advance): advance

⚙️ Generating lesson for Subject: Mathematics | Topic: Matrices | Level: SSS 3 | Pace: advance...

# ... (Full personalized lesson is generated here) ...
```

### API Mode

- Swagger UI: `http://localhost:8002/docs`
- Redoc: `http://localhost:8002/redoc`

Key endpoints:

- `GET /` — Basic service info
- `GET /health` — Health check
- `GET /status` — Current subjects and initialization status
- `POST /lesson` — Generate a personalized lesson

Example request to generate a lesson:

```bash
curl -X POST http://localhost:8002/lesson \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Mathematics",
    "topic": "Matrices",
    "sss_level": "SSS 3",
    "learning_pace": "advance"
  }'
```

Example response (truncated):

```json
{
  "subject": "Mathematics",
  "topic": "Matrices",
  "sss_level": "SSS 3",
  "learning_pace": "advance",
  "lesson_notes": "# Introduction...",
  "status": "success"
}
```

---

## ⚠️ Troubleshooting Common Issues

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| **`Remote end closed connection without response`** | Hugging Face LLM API timeout. The generated lesson was too long. | In `rag.py`, reduce `max_new_tokens` in `initialize_hf_llm` to `800` or less. |
| **`File hash mismatch... Rebuilding`** | This is the cache mechanism working. A PDF file was modified, added, or deleted. | **No action needed.** Let the system rebuild. The cache will be restored for the next run. |
| **`Error loading vectorstore... Attempting rebuild`** | The FAISS index files (`index.faiss`/`index.pkl`) are corrupted or missing. | **No action needed.** The system automatically triggers a full rebuild to correct the corrupted cache. |
| **Lesson content is too brief** | The LLM needs more space to write. | In `rag.py`, increase `max_new_tokens` in `initialize_hf_llm` (e.g., from 800 to 1000). |

API-specific notes:

- If the first request for a subject is slow, it is performing lazy initialization (vectorstore load/build).
- Ensure the `HUGGINGFACEHUB_API_TOKEN` is set in `.env` before starting the server.

---

## 📁 Project Structure

```text
learning_Platform/
├── curriculum_data/           # Curriculum PDFs organized by subject
│   ├── Mathematics/
│   ├── English/
│   └── Science/
├── vectorstores/             # Generated vector stores for RAG
│   ├── Mathematics_faiss/
│   ├── English_faiss/
│   └── Science_faiss/
├── dataLoading.py            # Data loading and processing utilities
├── rag.py                   # RAG implementation + CLI mode
├── main.py                  # FastAPI server (HTTP API)
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🤝 Contributing

Feel free to contribute to this project by:

- Adding new subjects to the curriculum
- Improving the lesson generation prompts
- Enhancing the user interface
- Reporting bugs or suggesting features

## 📄 License

This project is open source and available under the MIT License.