# Task Management API + AI Agent Skills

This project is part of the AI-400 course, Class 4. It demonstrates a complete Task Management API integrated with custom Agent Skills, built using a modern Python stack.

## 🚀 Technologies Used

- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **ORM**: [SQLModel](https://sqlmodel.tiangolo.com/) (SQLAlchemy + Pydantic)
- **Database**: SQLite
- **Testing**: [pytest](https://docs.pytest.org/)

## 🛠 Project Structure

- `main.py`: API entry point and endpoint definitions.
- `models.py`: Data models for Tasks.
- `database.py`: DB engine and session management.
- `skills/`: Directory containing reusable agent skills.
  - `priority.py`: Auto-prioritization logic.
  - `cleanup.py`: Database hygiene and archiving.
  - `daily_brief.py`: Workflow automation for daily summaries.
  - `search.py`: Advanced string search.
  - `reporter.py`: Markdown report generation.
- `tests/`: Pytest suite for API and Skill verification.
- `demo.py`: Interactive demo script.

## 🌟 Agent Skills

1. **Auto-Prioritize**: Analyzes deadlines and automatically upgrades priority for tasks due within 24 hours (Priority 5) or 3 days (Priority 4).
2. **Database Cleanup**: Workflow skill to remove/archive tasks completed over 7 days ago.
3. **Daily Brief**: Generates a natural language summary of the day's most important work.
4. **Advanced Search**: technical skill to find tasks matching complex queries.
5. **Markdown Reporter**: technical skill to output a formatted report of active tasks.

## ⚙️ How to Run

1. **Setup Environment**:
   ```bash
   uv sync
   ```
2. **Run Tests**:
   ```bash
   uv run pytest
   ```
3. **Start API Server**:
   ```bash
   uv run uvicorn main:app --reload
   ```
4. **Run Local Demo**:
   ```bash
   uv run demo.py
   ```

## 📝 API Documentation

Once the server is running, visit `http://127.0.0.1:8000/docs` to interact with the Swagger UI.
