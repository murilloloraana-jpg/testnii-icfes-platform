# Testnii: AI-Powered ICFES Preparation Platform

Testnii is a full-stack educational platform built to modernize how students 
prepare for the ICFES — Colombia's national university entrance exam. Designed 
with a focus on software architecture, scalability, and real pedagogical impact, 
it integrates AI to give students instant, meaningful feedback on their 
performance — not just a score, but an explanation of where their reasoning 
went wrong and why.

Built for students who don't have access to expensive tutoring. Awarded **Best 
Graduation Project 2025** at SENA.

---

## Project Showcase

[![Testnii Platform Demo](https://img.youtube.com/vi/GfXuwZjTPQQ/0.jpg)](https://www.youtube.com/watch?v=GfXuwZjTPQQ)
*Click the image above to watch the full platform walkthrough.*

---

## Key Features

### For Students
- **Smart Simulations:** Mock exams across all five ICFES subjects — Mathematics, 
Critical Reading, Natural Sciences, Social Studies, and English — with real-time 
timers that track time per question, mirroring real exam conditions.
- **AI-Driven Feedback:** Google Gemini API integration that explains exactly why 
an answer was wrong and walks through the correct reasoning.
- **Performance Analytics:** Dashboards showing historical progress, normalized 
scores, and proficiency levels per subject.

### For Teachers
- **Module Management:** Full control over creating, editing, and deleting exam 
modules and question banks (multiple choice and true/false).
- **Classroom System:** Teachers register their classroom; students join it and 
automatically see the assigned exams.
- **Student Monitoring:** Aggregated performance reports with individual scores 
across grades.

### For Administrators
- **System Administration:** Full CRUD over the entire user ecosystem — students, 
teachers, and admins.
- **Global Statistics:** Platform-wide engagement metrics and academic results 
across all institutions in one dashboard.

---

## Technical Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Django 5.x |
| Frontend | HTML5, CSS3 (Bootstrap 5), Vanilla JavaScript |
| AI Integration | Google Gemini API (google-genai) |
| Database | SQLite (development) |
| Configuration | Virtualenv, python-dotenv |

---

## Getting Started

### Prerequisites
- Python 3.10 or higher
- A valid Google Gemini API Key

### Installation

1. **Clone the repository:**
```bash
   git clone https://github.com/yourusername/testnii-icfes-platform.git
   cd testnii-icfes-platform
```

2. **Initialize the virtual environment:**
```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
```

3. **Install dependencies:**
```bash
   pip install django google-genai python-dotenv
```

4. **Configure environment variables:**
   Create a `.env` file in the root directory (alongside `manage.py`):
GEMINI_API_KEY=your_api_key_here

5. **Run migrations and start the server:**
```bash
   python manage.py migrate
   python manage.py runserver
```

---

## About

Built by **Ana María Murillo Lora** — software developer from Cali, Colombia.

I built Testnii because I saw firsthand how unequal access to quality exam 
preparation affects students from low-income backgrounds. The ICFES determines 
university admission in Colombia, and expensive tutoring shouldn't be the only 
way to be ready for it.

This project was awarded **Best Graduation Project 2025** at SENA (Servicio 
Nacional de Aprendizaje), recognized for technical quality and social impact.

→ [GitHub](https://github.com/murilloloraana-jpg)
