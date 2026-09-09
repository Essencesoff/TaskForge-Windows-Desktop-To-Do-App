from typing import List, Optional
from app.database import db
from app.models.task import Category


def list_categories() -> List[Category]:
    rows = db.query_all("SELECT * FROM categories ORDER BY name")
    return [Category(**r) for r in rows]


def create_category(name: str, icon: str = "", color: str = "#5C6BC0", description: str = "") -> Category:
    cur = db.execute("INSERT INTO categories (name, icon, color, description) VALUES (?,?,?,?)",
                      (name, icon, color, description))
    return Category(id=cur.lastrowid, name=name, icon=icon, color=color, description=description)


def update_category(cat: Category):
    db.execute("UPDATE categories SET name=?, icon=?, color=?, description=? WHERE id=?",
               (cat.name, cat.icon, cat.color, cat.description, cat.id))


def delete_category(cat_id: int):
    db.execute("UPDATE tasks SET category_id=NULL WHERE category_id=?", (cat_id,))
    db.execute("DELETE FROM categories WHERE id=?", (cat_id,))


def get_category(cat_id: Optional[int]) -> Optional[Category]:
    if cat_id is None:
        return None
    row = db.query_one("SELECT * FROM categories WHERE id=?", (cat_id,))
    return Category(**row) if row else None
