# Academic Tutor — Working Memory (`memory.md`)

## 📚 Active Courses (Current Semester)
*(Populate during onboarding or run `setup.sh` to auto-discover folders in `CLASS_FOLDERS_PATH`)*
| Course Code | Course Title | Exam / Milestone Dates | Target Folder |
| :--- | :--- | :--- | :--- |
| `EXAMPLE_COURSE_101` | Example Course Template | TBD | `EXAMPLE_COURSE_101/2_Parsed_Markdown` |

---

## 🎯 Active Study Sprint Queue
- [ ] Populate active courses and syllabus exam dates with Callie.
- [ ] Drop course syllabi and lecture slides into `<CLASS_FOLDERS_PATH>/<COURSE_CODE>/1_Syllabus_and_Schedule` and `1_Lectures_and_Slides`.

---

## ⚡ Fast Paths & Command Cache
- **Parse New Raw PDFs/PPTX/DOCX in Class Folders:**
  `~/Agents/Agent 0/.venv/bin/python ~/Agents/Agent 0/voice_to_brain/pipeline_parser.py`
- **Re-Index Class Folders into ChromaDB:**
  `~/Agents/Agent 0/mcp/obsidian_search/venv/bin/python ~/Agents/Agent 0/mcp/obsidian_search/sync_database.py`

---

## 🔗 Neural Pathways
- **Exam Dates → Agent 0:** Whenever new exam or project dates are extracted from a syllabus, push them to `~/Agents/Agent 0/memory.md` for Google Calendar syncing.
