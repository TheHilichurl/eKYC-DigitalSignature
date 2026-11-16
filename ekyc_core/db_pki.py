import sqlite3
import os
import json
from datetime import datetime

class PkiDatabase:
    def __init__(self, db_path="data/ekyc_pki.db"):
        if not os.path.isabs(db_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, db_path)

        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_tables()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_tables(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                id_card TEXT,
                department TEXT,
                face_embedding TEXT,
                avatar_path TEXT,
                public_key_pem TEXT NOT NULL,
                private_key_pem TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_assets (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                asset_type TEXT NOT NULL, -- 'signature' | 'stamp'
                title TEXT NOT NULL,
                image_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS signed_documents (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                document_name TEXT NOT NULL,
                original_pdf_path TEXT,
                signed_pdf_path TEXT NOT NULL,
                original_sha256 TEXT NOT NULL,
                signed_sha256 TEXT NOT NULL,
                crypto_signature_hex TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                pos_x REAL NOT NULL,
                pos_y REAL NOT NULL,
                width REAL NOT NULL,
                height REAL NOT NULL,
                signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'VALID',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """)
            conn.commit()
        finally:
            conn.close()

    def add_user(self, user_id, name, id_card, department, embedding, avatar_path, public_key_pem, private_key_pem):
        emb_json = json.dumps(embedding.tolist() if hasattr(embedding, 'tolist') else embedding)
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO users (id, name, id_card, department, face_embedding, avatar_path, public_key_pem, private_key_pem)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, name, id_card, department, emb_json, avatar_path, public_key_pem, private_key_pem))
            conn.commit()
        finally:
            conn.close()

    def get_user(self, user_id):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d['face_embedding'] = json.loads(d['face_embedding']) if d['face_embedding'] else None
                return d
            return None
        finally:
            conn.close()

    def list_users(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, id_card, department, avatar_path, created_at FROM users ORDER BY created_at DESC")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def add_asset(self, asset_id, user_id, asset_type, title, image_path):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO user_assets (id, user_id, asset_type, title, image_path)
            VALUES (?, ?, ?, ?, ?)
            """, (asset_id, user_id, asset_type, title, image_path))
            conn.commit()
        finally:
            conn.close()

    def list_user_assets(self, user_id=None):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("""
                SELECT a.*, u.name as user_name 
                FROM user_assets a 
                JOIN users u ON a.user_id = u.id 
                WHERE a.user_id = ? 
                ORDER BY a.created_at DESC
                """, (user_id,))
            else:
                cursor.execute("""
                SELECT a.*, u.name as user_name 
                FROM user_assets a 
                JOIN users u ON a.user_id = u.id 
                ORDER BY a.created_at DESC
                """)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def record_signed_document(self, doc_id, user_id, doc_name, orig_path, signed_path, orig_sha, signed_sha, sig_hex, page, x, y, w, h):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO signed_documents (
                id, user_id, document_name, original_pdf_path, signed_pdf_path,
                original_sha256, signed_sha256, crypto_signature_hex,
                page_number, pos_x, pos_y, width, height
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (doc_id, user_id, doc_name, orig_path, signed_path, orig_sha, signed_sha, sig_hex, page, x, y, w, h))
            conn.commit()
        finally:
            conn.close()

    def list_signed_documents(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT s.*, u.name as signer_name, u.id_card, u.public_key_pem
            FROM signed_documents s
            JOIN users u ON s.user_id = u.id
            ORDER BY s.signed_at DESC
            """)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def delete_user(self, user_id):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_assets WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_asset(self, asset_id):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_assets WHERE id = ?", (asset_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
