"""Seed ChromaDB with corvit_data.json into 4 collections."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.vectordb.embedder import embed_documents, load_corvit_data
from src.vectordb.store import VectorStore


def main() -> None:
    print("Seeding ChromaDB...")
    store = VectorStore()
    data = load_corvit_data()

    total = 0

    # Courses collection
    courses = data.get("courses", [])
    docs = [f"{c['name']}: {c['description']} Duration: {c['duration']}. Fee: {c['fee']}. Category: {c['category']}. Prerequisites: {c.get('prerequisites', 'None')}. Certification: {c.get('certification', 'N/A')}." for c in courses]
    metas = [{"name": c["name"], "category": c["category"], "source": "courses"} for c in courses]
    n = embed_documents(store, "courses", docs, metas)
    print(f"  courses: {n} documents")
    total += n

    # Teachers collection
    teachers = data.get("teachers", [])
    docs = [f"{t['name']}: {t['specialization']}. {t['qualifications']} Teaches: {', '.join(t.get('courses', []))}." for t in teachers]
    metas = [{"name": t["name"], "specialization": t["specialization"], "source": "teachers"} for t in teachers]
    n = embed_documents(store, "teachers", docs, metas)
    print(f"  teachers: {n} documents")
    total += n

    # Infrastructure collection
    infra = data.get("infrastructure", [])
    docs = [f"{i['name']}: {i['description']} Capacity: {i['capacity']}. Equipment: {', '.join(i.get('equipment', []))}." for i in infra]
    metas = [{"name": i["name"], "capacity": i["capacity"], "source": "infrastructure"} for i in infra]
    n = embed_documents(store, "infrastructure", docs, metas)
    print(f"  infrastructure: {n} documents")
    total += n

    # Policies collection
    policies = data.get("policies", [])
    docs = [f"{p['title']}: {p['content']}" for p in policies]
    metas = [{"title": p["title"], "source": "policies"} for p in policies]
    n = embed_documents(store, "policies", docs, metas)
    print(f"  policies: {n} documents")
    total += n

    print(f"\nTotal: {total} documents across 4 collections.")


if __name__ == "__main__":
    main()
