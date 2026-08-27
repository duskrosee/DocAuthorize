import os
import pandas as pd
import sqlite3
import sys
from pathlib import Path

if os.name == 'nt':  #Windows
    DATA_DIR = Path(os.getenv('APPDATA')) / "DocAuthorize"
else:  #macOS / Linux
    DATA_DIR = Path.home() / ".docauthorize"

DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "docauthorize.db"
DB_NAME = str(DB_PATH)

BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def get_connection():
    return sqlite3.connect(DB_NAME)

def create_tables():
    """Create database tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            nip TEXT,
            company_phone TEXT,
            contact_person TEXT,
            contact_phone TEXT,
            email TEXT,
            manager TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            file_name TEXT,
            file_path TEXT,
            contract_date TEXT,
            validity_period TEXT,
            price TEXT,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    """)

    conn.commit()
    conn.close()

create_tables()


def add_client(
    company_name,
    nip,
    company_phone=None,
    contact_person=None,
    contact_phone=None,
    email=None,
    manager=None,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO clients (company_name, nip, company_phone, contact_person, contact_phone, email, manager)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            company_name,
            nip,
            company_phone,
            contact_person,
            contact_phone,
            email,
            manager,
        ),
    )

    client_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return client_id


def add_document(
    client_id,
    file_name,
    file_path,
    contract_date=None,
    validity_period=None,
    price=None,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO documents (client_id, file_name, file_path, contract_date, validity_period, price)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            client_id,
            file_name,
            file_path,
            contract_date,
            validity_period,
            price,
        ),
    )

    conn.commit()
    conn.close()


def get_clients_with_all_documents():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM clients")
    clients_rows = cursor.fetchall()

    result = []

    for c in clients_rows:
        client_id = c[0]
        client_dict = {
            "id": c[0],
            "company_name": c[1],
            "nip": c[2],
            "company_phone": c[3],
            "contact_person": c[4],
            "contact_phone": c[5],
            "email": c[6],
            "manager": c[7],
        }

        cursor.execute(
            "SELECT id, file_name, file_path, contract_date, validity_period, price FROM documents WHERE client_id = ?",
            (client_id,),
        )
        docs_rows = cursor.fetchall()

        documents = []
        for d in docs_rows:
            documents.append(
                {
                    "id": d[0],
                    "file_name": d[1],
                    "file_path": d[2],
                    "contract_date": d[3],
                    "validity_period": d[4],
                    "price": d[5],
                }
            )

        result.append({"client": client_dict, "documents": documents})

    conn.close()
    return result


def delete_client(client_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM documents WHERE client_id = ?", (client_id,))
    cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))

    conn.commit()
    conn.close()


def save_analyzed_document(data, file_path, file_name):
    def clean(val):
        if not val or "Not found" in str(val):
            return None
        return str(val)
        
    company_name = clean(data.get("Company", {}).get("value"))
    nip = clean(data.get("NIP", {}).get("value"))
    company_phone = clean(data.get("Company phone", {}).get("value"))
    contact_person = clean(data.get("Contact person", {}).get("value"))
    contact_phone = clean(data.get("Contact phone", {}).get("value"))
    email = clean(data.get("Email", {}).get("value"))
    manager = clean(data.get("Manager", {}).get("value"))

    contract_date = clean(data.get("Contract date", {}).get("value"))
    validity_period = clean(data.get("Validity period", {}).get("value"))
    price = clean(data.get("Price", {}).get("value"))

    conn = get_connection()
    cursor = conn.cursor()

    client_id = None

    if nip:
        cursor.execute("SELECT id FROM clients WHERE nip = ?", (nip,))
        row = cursor.fetchone()
        if row:
            client_id = row[0]

    if not client_id and company_name:
        cursor.execute(
            "SELECT id FROM clients WHERE company_name = ?", (company_name,)
        )
        row = cursor.fetchone()
        if row:
            client_id = row[0]

    if not client_id:
        cursor.execute(
            """
            INSERT INTO clients (company_name, nip, company_phone, contact_person, contact_phone, email, manager)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                company_name,
                nip,
                company_phone,
                contact_person,
                contact_phone,
                email,
                manager,
            ),
        )
        client_id = cursor.lastrowid
    else:
        cursor.execute(
            """
            UPDATE clients
            SET company_phone = COALESCE(?, company_phone),
                contact_person = COALESCE(?, contact_person),
                contact_phone = COALESCE(?, contact_phone),
                email = COALESCE(?, email),
                manager = COALESCE(?, manager)
            WHERE id = ?
        """,
            (
                company_phone,
                contact_person,
                contact_phone,
                email,
                manager,
                client_id,
            ),
        )

    cursor.execute(
        """
        INSERT INTO documents (client_id, file_name, file_path, contract_date, validity_period, price)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (client_id, file_name, file_path, contract_date, validity_period, price),
    )

    conn.commit()
    conn.close()

    return client_id


def export_clients_to_excel(file_path):
    """Экспортирует всех клиентов и информацию о контрактах в Excel."""
    clients_data = get_clients_with_all_documents()
    rows = []

    for item in clients_data:
        client = item["client"]
        documents = item["documents"]
        
        if documents:
            for doc in documents:
                rows.append(
                    {
                        "NIP": client.get("nip") or "---",
                        "Company": client.get("company_name") or "---",
                        "Company phone": client.get("company_phone") or "---",
                        "Contact person": client.get("contact_person") or "---",
                        "Contact phone": client.get("contact_phone") or "---",
                        "Email": client.get("email") or "---",
                        "Contract date": doc.get("contract_date") or "---",
                        "Validity period": doc.get("validity_period") or "---",
                        "Price": doc.get("price") or "---",
                        "Manager": client.get("manager") or "---",
                    }
                )
        else:
            rows.append(
                {
                    "NIP": client.get("nip") or "---",
                    "Company": client.get("company_name") or "---",
                    "Company phone": client.get("company_phone") or "---",
                    "Contact person": client.get("contact_person") or "---",
                    "Contact phone": client.get("contact_phone") or "---",
                    "Email": client.get("email") or "---",
                    "Contract date": "---",
                    "Validity period": "---","Price": "---",
                    "Manager": client.get("manager") or "---",
                }
            )

    df = pd.DataFrame(rows)
    df.to_excel(file_path, index=False, engine="openpyxl")

def get_dashboard_stats():
    """Return basic statistics for the dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM clients")
    total_clients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM documents")
    total_documents = cursor.fetchone()[0]

    conn.close()

    return {
        "clients": total_clients,
        "documents": total_documents
    }


def search_client_by_nip(nip_query):
    """Searches for clients by NIP (partial or complete match)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM clients WHERE nip LIKE ?", (f"%{nip_query}%",))
    clients_rows = cursor.fetchall()

    result = []
    for c in clients_rows:
        client_id = c[0]
        client_dict = {
            "id": c[0],
            "company_name": c[1],
            "nip": c[2],
            "company_phone": c[3],
            "contact_person": c[4],
            "contact_phone": c[5],
            "email": c[6],
            "manager": c[7],
        }

        cursor.execute(
            "SELECT id, file_name, file_path, contract_date, validity_period, price FROM documents WHERE client_id = ?",
            (client_id,),
        )
        docs_rows = cursor.fetchall()

        documents = []
        for d in docs_rows:
            documents.append({
                "id": d[0],
                "file_name": d[1],
                "file_path": d[2],
                "contract_date": d[3],
                "validity_period": d[4],
                "price": d[5],
            })

        result.append({"client": client_dict, "documents": documents})

    conn.close()
    return result

def get_documents_by_client(client_id):
    """Return a list of documents for a specific client."""
    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute(
        "SELECT id, file_name, file_path, contract_date, validity_period, price FROM documents WHERE client_id = ?",
        (client_id,),
    )
    docs_rows = cursor.fetchall()
    conn.close()

    documents = []
    for d in docs_rows:
        documents.append({
            "id": d[0],
            "file_name": d[1],
            "file_path": d[2],
            "contract_date": d[3],
            "validity_period": d[4],
            "price": d[5],
        })
    return documents 

def get_documents_by_nips(nips_list: list) -> list:
    """Возвращает все договоры (и новые, и старые из БД) для переданных NIP."""
    if not nips_list:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ",".join(["?"] * len(nips_list))
    query = f"""
        SELECT c.nip, c.company_name, c.manager, d.file_name, d.file_path, d.contract_date, d.price
        FROM documents d
        JOIN clients c ON d.client_id = c.id
        WHERE c.nip IN ({placeholders})
    """

    cursor.execute(query, nips_list)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "nip": r[0] or "---",
            "company_name": r[1] or "---",
            "manager": r[2] or "---",
            "file_name": r[3] or "---",
            "file_path": r[4] or "",
            "contract_date": r[5] or "---",
            "price": r[6] or "---"
        })
    return result


#.