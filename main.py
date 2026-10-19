from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from typing import Dict, Optional
import database

app = FastAPI(title="PC Hardware Inventory API")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ItemCreate(BaseModel):
    category: str
    brand: str
    model: str
    quantity: int
    box_number: str
    specs: Dict[str, str]


@app.on_event("startup")
def startup_event():
    database.init_db()


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, selected_box: str = "Box A", q: str = None):
    """Serves the central inventory dashboard with live cross-box search capabilities."""
    conn = database.get_db_connection()
    locations = conn.execute("SELECT * FROM locations").fetchall()

    if q:
        search_term = f"%{q}%"
        query = """
                SELECT DISTINCT h.*, l.shelf_name, l.box_number
                FROM hardware_items h
                         LEFT JOIN locations l ON h.location_id = l.id
                         LEFT JOIN technical_specs s ON h.id = s.item_id
                WHERE h.category LIKE ?
                   OR h.brand LIKE ?
                   OR h.model LIKE ?
                   OR s.spec_value LIKE ? \
                """
        items = conn.execute(query, (search_term, search_term, search_term, search_term)).fetchall()
        selected_box = None
    else:
        query = """
                SELECT h.*, l.shelf_name, l.box_number
                FROM hardware_items h
                         LEFT JOIN locations l ON h.location_id = l.id
                WHERE l.box_number = ? \
                """
        items = conn.execute(query, (selected_box,)).fetchall()

    result_items = []
    for item in items:
        item_dict = dict(item)
        specs = conn.execute(
            "SELECT spec_key, spec_value FROM technical_specs WHERE item_id = ?",
            (item_dict['id'],)
        ).fetchall()
        item_dict['specs'] = {spec['spec_key']: spec['spec_value'] for spec in specs}
        result_items.append(item_dict)

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "locations": [dict(l) for l in locations],
            "items": result_items,
            "selected_box": selected_box,
            "search_query": q
        }
    )


@app.post("/web/add-item")
def web_add_item(
        category: str = Form(...),
        brand: str = Form(...),
        model: str = Form(...),
        quantity: int = Form(...),
        box_number: str = Form(...),
        spec1: Optional[str] = Form(None),
        spec2: Optional[str] = Form(None),
        spec3: Optional[str] = Form(None)
):
    """Saves new items using position-based technical field mapping schemas."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    location = cursor.execute("SELECT id FROM locations WHERE box_number = ?", (box_number,)).fetchone()
    if not location:
        conn.close()
        raise HTTPException(status_code=400, detail="Target container context not found.")

    cursor.execute(
        "INSERT INTO hardware_items (category, brand, model, quantity, location_id) VALUES (?, ?, ?, ?, ?)",
        (category, brand, model, quantity, location['id'])
    )
    new_item_id = cursor.lastrowid

    specs_to_add = {}
    if category == "RAM":
        if spec1: specs_to_add["Generation"] = spec1
        if spec2: specs_to_add["Speed"] = f"{spec2}MHz" if "mhz" not in spec2.lower() else spec2
        if spec3: specs_to_add["Capacity"] = f"{spec3}GB" if "gb" not in spec3.lower() else spec3
    elif category in ["SSD", "HDD"]:
        if spec1: specs_to_add["Type"] = spec1
        if spec2: specs_to_add["Capacity"] = spec2
        if spec3: specs_to_add["Form Factor"] = spec3
    elif category == "CPU":
        if spec1: specs_to_add["Socket"] = spec1
        if spec2: specs_to_add["Cores"] = spec2

    for k, v in specs_to_add.items():
        if v:
            cursor.execute("INSERT INTO technical_specs (item_id, spec_key, spec_value) VALUES (?, ?, ?)",
                           (new_item_id, k, v))

    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/?selected_box={box_number}", status_code=303)


@app.post("/web/adjust-quantity/{item_id}/{action}")
def web_adjust_quantity(item_id: int, action: str, current_box: Optional[str] = "Box A"):
    """API endpoint to instantly bump or lower quantities from dashboard cards."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    item = cursor.execute("SELECT quantity, location_id FROM hardware_items WHERE id = ?", (item_id,)).fetchone()

    if item:
        current_qty = item["quantity"]
        loc_id = item["location_id"]

        box_record = cursor.execute("SELECT box_number FROM locations WHERE id = ?", (loc_id,)).fetchone()
        box_str = box_record["box_number"] if box_record else current_box

        if action == "increment":
            new_qty = current_qty + 1
            cursor.execute("UPDATE hardware_items SET quantity = ? WHERE id = ?", (new_qty, item_id))
        elif action == "decrement":
            new_qty = current_qty - 1
            if new_qty <= 0:
                cursor.execute("DELETE FROM hardware_items WHERE id = ?", (item_id,))
            else:
                cursor.execute("UPDATE hardware_items SET quantity = ? WHERE id = ?", (new_qty, item_id))

        conn.commit()
    else:
        box_str = current_box

    conn.close()
    return RedirectResponse(url=f"/?selected_box={box_str}", status_code=303)


@app.get("/locations")
def get_locations():
    conn = database.get_db_connection()
    locations = conn.execute("SELECT * FROM locations").fetchall()
    conn.close()
    return [dict(loc) for loc in locations]


@app.post("/web/add-box")
def web_add_box(
        box_number: str = Form(...),
        shelf_name: str = Form(...)
):
    """Inserts a brand new physical storage container bin into the shelf grid mapping."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    # 1. Clean strings and check if this exact box label name already exists
    box_clean = box_number.strip()
    shelf_clean = shelf_name.strip()

    existing = cursor.execute("SELECT id FROM locations WHERE box_number = ?", (box_clean,)).fetchone()
    if existing:
        conn.close()
        # Gracefully handle duplicates by redirecting back with an error indicator if you want,
        # or simply redirect to avoid crashing.
        return RedirectResponse(url=f"/?selected_box={box_clean}", status_code=303)

    # 2. Insert the new box row records
    cursor.execute(
        "INSERT INTO locations (shelf_name, box_number) VALUES (?, ?)",
        (shelf_clean, box_clean)
    )

    conn.commit()
    conn.close()

    # Refresh the dashboard, auto-selecting our brand new empty box slot!
    return RedirectResponse(url=f"/?selected_box={box_clean}", status_code=303)


@app.post("/web/edit-box")
def web_edit_box(
        current_box_number: str = Form(...),
        new_box_number: str = Form(...),
        new_shelf_name: str = Form(...)
):
    """Updates the name or shelf location of an existing storage bin row."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    box_clean = new_box_number.strip()
    shelf_clean = new_shelf_name.strip()

    # Update the target location record
    cursor.execute(
        "UPDATE locations SET box_number = ?, shelf_name = ? WHERE box_number = ?",
        (box_clean, shelf_clean, current_box_number)
    )

    conn.commit()
    conn.close()

    # Refresh dashboard displaying your updated container node box name
    return RedirectResponse(url=f"/?selected_box={box_clean}", status_code=303)


@app.post("/web/delete-box")
def web_delete_box(
        box_number: str = Form(...)
):
    """Removes a box. Warning: SQLite foreign keys delete all nested items too!"""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    # Enable foreign keys so nested items and specs are safely cascade deleted
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("DELETE FROM locations WHERE box_number = ?", (box_number,))

    # Sniff out the first remaining alternate box to avoid landing on a missing page
    fallback = cursor.execute("SELECT box_number FROM locations LIMIT 1").fetchone()
    fallback_box = fallback["box_number"] if fallback else "Box A"

    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/?selected_box={fallback_box}", status_code=303)

    # Force a secure fallback box value if a global search (q) clears it out
    display_box = selected_box if selected_box else "Box A"

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "locations": [dict(l) for l in locations],
            "items": result_items,
            "selected_box": display_box, # Always populated!
            "search_query": q
        }
    )
