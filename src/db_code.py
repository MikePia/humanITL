import os
import psycopg2
import psycopg2.extras
from psycopg2 import OperationalError


def pg_connect():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        return None


def update_tags(url, new_status=None, title=None, author=None, sector=None, date=None)->bool:
    conn = pg_connect()
    if conn is None:
        print("Failed to get database connection")
        return False

    try:
        cur = conn.cursor()
        # Prepare the SQL statement based on provided data
        columns = []
        values = []

        if title:
            columns.append("title = %s")
            values.append(title)
        if author:
            columns.append("author = %s")
            values.append(author)
        if sector:
            columns.append("sector = %s")
            values.append(sector)
        if date:
            columns.append("date = %s")
            values.append(date)
        if new_status:
            columns.append("status = %s")
            values.append(new_status)

        if not columns:
            print("No data provided to update.")
            return False

        # Build SQL query
        sql_query = (
            "UPDATE pdf_links SET " + ", ".join(columns) + " WHERE pdf_link = %s;"
        )
        values.append(url)  # Append URL at the end for WHERE clause

        # Execute the SQL command
        cur.execute(sql_query, tuple(values))
        conn.commit()
        return True
    except psycopg2.Error as e:
        print(f"Error updating database: {e}")
        conn.rollback()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def fetchPdfLinksForTagging(batch_size):
    conn = pg_connect()
    if conn is None:
        print("Failed to get database connection")
        return []

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                WITH updated AS (
                    UPDATE public.pdf_links
                    SET status = 'in_process'
                    WHERE id IN (
                        SELECT id FROM public.pdf_links
                        WHERE status <> 'in_process'
                        AND classify = 1
                        AND title IS NULL
                        ORDER BY RANDOM()
                        LIMIT %s
                    )
                    RETURNING id, pdf_link
                )
                SELECT * FROM updated;
                """,
                (batch_size,),
            )
            documents = cur.fetchall()
            conn.commit()
            return documents
    except psycopg2.Error as e:
        print(f"Error fetching PDF links for tagging: {e}")
        conn.rollback()
        return []
    finally:
        conn.close()
