# 🖥️ PC Hardware Inventory Manager

A high-performance, asynchronous full-stack, desktop-optimized web dashboard application engineered to map, search, and manage spare physical PC components hidden across physical storage bins.

Instead of navigating abstract spreadsheet rows, this application organizes a physical storage closet layout into an interactive grid interface. It features dynamic spec-label morphing, a global cross-box keyword search engine, and instant database stock increment controls.

## 🚀 Live Portfolio Page
👉 **[View the Live Landing Page]([https://github.com/cptdiamond/pc-hardware-inventory-manager])**

---

## 🛠️ Features
- **Component Tracking:** Log hardware (CPUs, GPUs, RAM, Storage) with automatic schema verification.
- **Physical Shelf Grid Mapping:** Automatically tracks and maps physical storage boxes (`Box A`, `Box B`) into clickable workspace targets to instantly fetch indexed parts.
- **Context-Aware Smart Inputs:** Built-in form control optimization changes text fields and placeholders dynamically using native JavaScript based on your hardware category selection (e.g., hiding storage form factor fields when logging a CPU socket).
- **Global Keyword Search Engine:** A backend query engine executing composite SQLite conditional matching patterns across categories, brands, models, or nested hardware specification values simultaneously.
- **Instant Stock Controls:** Micro-forms built right onto hardware component cards allow you to increment or decrement stock metrics instantly via background POST request cycles. Zero stock automatically executes an intentional cascade database delete.
- **Auto-Generated REST Docs:** Out-of-the-box Interactive API exploration via Swagger UI and ReDoc.
- **Data Validation:** Strict input handling and error parsing backed by Pydantic.

## 🧰 Tech Stack
- **Backend Framework:** Python & FastAPI (Python 3.11+)
- **Database Engine:** SQLite (Relational structure tracking attributes and hardware entities via custom foreign key mappings)
- **Data Validation:** Pydantic v2
- **Frontend Design Layer:** HTML5 & Tailwind CSS Framework
- **ASGI Server:** Uvicorn
- **Templating Compilation Engine:** Jinja2

---

## ⚙️ Local Installation & Setup

Follow these quick steps to pull down and run this project locally on your machine.

### 1. Clone the Repository
```bash
git clone https://github.com/CptDiamond/pc-hardware-inventory-manager.git
cd pc-hardware-inventory-manager
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Development Server
```bash
uvicorn main:app --reload
```
Once the server boots up, open your choice of browser engine and navigate to: `http://127.0.0.1:8000` to explore the live API interactively.

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
