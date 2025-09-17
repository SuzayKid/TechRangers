import os
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np

def get_db_connection():
    """Establishes a database connection and returns it."""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "sih_dss"),
        user=os.getenv("DB_USER", "sih_user"),
        password=os.getenv("DB_PASSWORD", "sih_password")
    )
    return conn

def fetch_village_dss_data(village_id=None, patta_holder_id=None):
    """
    Fetches DSS data for a given village_id or patta_holder_id from the materialized view.
    Note: For patta_holder_id, we assume a mapping exists to village_id or we fetch all
    patta holders for a village and then process. For now, we'll focus on village_id.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if village_id:
            cur.execute("SELECT * FROM village_dss_data WHERE village_id = %s", (village_id,))
        # elif patta_holder_id:
        #     # TODO: Implement logic to get village_id from patta_holder_id
        #     # For now, this path is not fully supported without patta_holder_data table
        #     raise NotImplementedError("Fetching by patta_holder_id is not yet implemented.")
        else:
            raise ValueError("Either village_id or patta_holder_id must be provided.")
        
        data = cur.fetchone()
        cur.close()
        return data
    except Exception as e:
        print(f"Error fetching DSS data: {e}")
        return None
    finally:
        if conn:
            conn.close()

def fetch_eligibility_rules():
    """Fetches all eligibility rules from the database."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT s.scheme_id, s.scheme_name, s.description, s.description_embedding, er.attribute, er.operator, er.value FROM eligibility_rules er JOIN schemes s ON er.scheme_id = s.scheme_id")
        rules = cur.fetchall()
        cur.close()
        return rules
    except Exception as e:
        print(f"Error fetching eligibility rules: {e}")
        return []
    finally:
        if conn:
            conn.close()

def upsert_scheme_embedding(scheme_id: int, embedding: np.ndarray):
    """Inserts or updates a scheme's description embedding."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO schemes (scheme_id, description_embedding) VALUES (%s, %s) ON CONFLICT (scheme_id) DO UPDATE SET description_embedding = EXCLUDED.description_embedding",
            (scheme_id, embedding.tolist())
        )
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"Error upserting scheme embedding: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def find_similar_schemes(query_embedding: np.ndarray, limit: int = 5):
    """
    Finds schemes similar to the query embedding using cosine similarity.
    Requires the pgvector extension to be enabled and description_embedding column to exist.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Use the <-> operator for L2 distance, which is equivalent to cosine similarity for normalized vectors
        # Or use <=> for cosine distance directly (1 - cosine similarity)
        cur.execute(
            "SELECT scheme_id, scheme_name, description, description_embedding FROM schemes ORDER BY description_embedding <=> %s LIMIT %s",
            (query_embedding.tolist(), limit)
        )
        schemes = cur.fetchall()
        cur.close()
        return schemes
    except Exception as e:
        print(f"Error finding similar schemes: {e}")
        return []
    finally:
        if conn:
            conn.close()