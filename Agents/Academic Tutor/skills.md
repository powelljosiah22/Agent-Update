# Academic Tutor — Procedural Memory (`skills.md`)

## 1. Hybrid Class Folder Retrieval (`semantic_search_obsidian`)
Always retrieve ground-truth definitions, formulas, and problem sets from Callie's actual course materials first:
- **Exact Problem / Formula Lookup (`lexical_weight: 3.0`):**
  ```json
  {
    "query": "Chapter 4 Problem 2 formula",
    "target": "classes",
    "course": "EXAMPLE_COURSE_101",
    "n_results": 3,
    "lexical_weight": 3.0
  }
  ```
- **Broad Conceptual Synthesis (`lexical_weight: 0.5` - `1.5`):**
  ```json
  {
    "query": "core concepts and exam review topics",
    "target": "classes",
    "course": "EXAMPLE_COURSE_101",
    "n_results": 6,
    "lexical_weight": 1.5
  }
  ```

---

## 2. Interactive Adaptive Quiz Generation
When Callie wants to test her mastery before an exam:
1. Read `~/.gemini/config/skills/adaptive-quiz-generator/SKILL.md`.
2. Pull the exact lecture slides and practice problems from ChromaDB (`target="classes"`).
3. Generate a standalone interactive HTML quiz artifact with instant explanations, progress tracking, and weak-area regeneration.

---

## 3. New Course Folder Setup Pattern
Every course folder inside `CLASS_FOLDERS_PATH` uses this 5-folder structure:
- `1_Syllabus_and_Schedule/` (Raw syllabus PDF/DOCX)
- `1_Lectures_and_Slides/` (Raw PPTX/PDF slide decks)
- `1_Homework_and_Problems/` (Practice sets, rubrics)
- `1_Exams_and_Reviews/` (Study guides, practice exams)
- `2_Parsed_Markdown/` (Auto-generated clean Markdown indexed by ChromaDB)
