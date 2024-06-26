import logging
import os
import psycopg2
import psycopg2.extras
import pandas as pd
import sqlite3
# from psycopg2 import OperationalError

logger = logging.getLogger(__name__)


def sqlite_connect(working_env=None):
    if not working_env:
        working_env = os.getenv("WORKING_ENV")
    try:
        if working_env == "production":
            localdb = os.getenv("LOCAL_DB")
            assert localdb is not None, "Failed to connect to SQLite database"
            conn = sqlite3.connect(localdb)
            return conn
        elif working_env == "development":
            localdb = os.getenv("LOCAL_TEST_DB")
            assert localdb is not None, "Failed to connect to SQLite database"
            conn = sqlite3.connect(localdb)
            return conn
        else:
            print("Invalid working environment")
            logger.warning(f"Invalid working environment: {working_env}")
            return None
    except sqlite3.OperationalError as e:
        print(f"Error connecting to the SQLite database: {e}")
        return None


def pg_connect(working_env=None):
    if not working_env:
        working_env = os.getenv("WORKING_ENV")
    try:
        if working_env == "production":
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
            )
            return conn
        elif working_env == "development":
            conn = psycopg2.connect(
                dbname=os.getenv("DB_DEV_NAME"),
                user=os.getenv("DB_DEV_USER"),
                password=os.getenv("DB_DEV_PASSWORD"),
                host=os.getenv("DB_DEV_HOST"),
            )
            return conn
        else:
            print("Invalid working environment")
            logger.warning(f"Invalid working environment: {working_env}")
            return None

    except psycopg2.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        return None


def update_local_db(
    pgid, pdf_link, classify, title, status, sector, author, date, filename_location
):
    # Connect to the SQLite database
    conn = sqlite_connect()
    cursor = conn.cursor()

    # SQL statement for inserting data, using placeholders for values
    sql = """
    INSERT INTO documents (pg_id, pdf_link, classify, title, status, sector, author, date, last_updated, filename_location)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?);
    """

    # Data tuple contains all values to insert
    data = (
        pgid,
        pdf_link,
        classify,
        title,
        status,
        sector,
        author,
        date,
        filename_location,
    )

    # Execute the SQL statement with the data
    cursor.execute(sql, data)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("Record updated successfully.")


# Call the function with the prepared data
# insert_record(data_to_insert)


def update_tags(
    url, new_status=None, title=None, author=None, sector=None, date=None
) -> bool:
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


def fetchLinksForTestingNoExt(batch_size):
    """Fetching links to download, Classify Tag and Archive."""
    conn = pg_connect()
    if conn is None:
        print("Failed to get database connection")
        return []

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"""
                WITH updated AS (
                    UPDATE public.pdf_links
                    SET status = 'in_process'
                    WHERE id IN (
                        SELECT id FROM public.pdf_links
                        WHERE status <> 'in_process'
                        AND filename_location IS NULL
                        AND (pdf_link NOT  ILIKE '%.htm' AND pdf_link NOT ILIKE '%.html')
                        AND pdf_link NOT ILIKE '%.pdf'
                        ORDER BY RANDOM()
                        LIMIT {batch_size}
                    )
                    RETURNING id, pdf_link, classify, title, sector, author, date, classify_op, filename_location
                )
                SELECT * FROM updated;
                """
            )

            documents = cur.fetchall()
            conn.commit()
            # Turninto pandas dataframe
            df = pd.DataFrame(documents)
            return df
    except psycopg2.Error as e:
        print(f"Error fetching PDF links for testing htm: {e}")
        conn.rollback()
        return []
    except Exception as e:
        print(f"Error fetching PDF links for testing htm: {e}")
        conn.rollback()
        return []
    finally:
        conn.close()


def fetchLinksForTestingHtm(batch_size):
    """Fetching links to download, Classify Tag and Archive."""
    conn = pg_connect()
    if conn is None:
        print("Failed to get database connection")
        return []

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"""
                WITH updated AS (
                    UPDATE public.pdf_links
                    SET status = 'in_process'
                    WHERE id IN (
                        SELECT id FROM public.pdf_links
                        WHERE status <> 'in_process'
                        AND filename_location IS NULL
                        AND (pdf_link ILIKE '%.htm' OR pdf_link ILIKE '%.html')
                        ORDER BY RANDOM()
                        LIMIT {batch_size}
                    )
                    RETURNING id, pdf_link, classify, title, sector, author, date, classify_op, filename_location
                )
                SELECT * FROM updated;
                """
            )

            documents = cur.fetchall()
            conn.commit()
            # Turninto pandas dataframe
            df = pd.DataFrame(documents)
            return df
    except psycopg2.Error as e:
        print(f"Error fetching PDF links for testing htm: {e}")
        conn.rollback()
        return []
    except Exception as e:
        print(f"Error fetching PDF links for testing htm: {e}")
        conn.rollback()
        return []
    finally:
        conn.close()


def fetchLinksForDCAT(batch_size):
    """Fetching links to download, Classify Tag and Archive. The central database filename_location
    will not be updated until the file is archived by the bucket launcher"""
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
                        AND filename_location IS NULL
                        ORDER BY RANDOM()
                        LIMIT %s
                    )
                    RETURNING id, pdf_link, classify, title, sector, author, date, classify_op, filename_location
                )
                SELECT * FROM updated;
                """,
                (batch_size,),
            )

            documents = cur.fetchall()
            conn.commit()
            # Turninto pandas dataframe
            df = pd.DataFrame(documents)
            return df
    except psycopg2.Error as e:
        print(f"Error fetching PDF links for tagging: {e}")
        conn.rollback()
        return []
    finally:
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


def batch_update_db(dataframe) -> int:
    """
    Does a BATCH UPDATE of ["classify", "title", "date", "author", "sector", "status"] columns in pdf_links based on matches to 'pdf_link' in a dataframe.

    Parameters:
    - dataframe (pandas.DataFrame): DataFrame containing the data to update.
    """
    logging.info("Starting batch update in the database.")

    # Connect to the database
    try:
        conn = pg_connect()
        cur = conn.cursor()
        logging.info("Database connection established.")
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")
        return 0

    # Prepare data for update; ensure 'pdf_link' is at the end for WHERE clause matching
    update_cols = [
        "classify",
        "title",
        "date",
        "author",
        "sector",
        "filename_location",
        "pdf_link",
    ]
    if not all(col in dataframe.columns for col in update_cols):
        error_message = "Dataframe must contain the columns: " + ", ".join(update_cols)
        logging.error(error_message)
        raise ValueError(error_message)

    # Create a list of tuples in the correct order for the SQL statement
    try:
        values = dataframe[update_cols].to_records(index=False).tolist()
        logging.info("Data prepared for database update.")
    except Exception as e:
        logging.error(f"Error preparing data: {e}")
        return 0

    # Prepare the SQL statement
    sql = """
    UPDATE public.pdf_links
    SET classify = %s, title = %s, date = %s, author = %s, sector = %s, filename_location = %s, status = 'ready'
    WHERE pdf_link = %s;
    """

    # Execute the update
    try:
        cur.executemany(sql, values)
        count = cur.rowcount
        conn.commit()
        logging.info(f"Database update successful. Updated {count} rows.")
        return count
    except Exception as e:
        conn.rollback()
        logging.error(f"Failed to execute database update: {e}")
    finally:
        cur.close()
        conn.close()
        logging.info("Database connection closed.")


def is_link_classified_and_tagged(pdf_link) -> dict:
    conn = pg_connect()
    if conn is None:
        print("Failed to get database connection")
        return False

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT classify, title FROM public.pdf_links
                WHERE pdf_link = %s

                """,
                (pdf_link,),
            )
            document = cur.fetchone()
            if document:
                return document

            else:
                return {}
    except psycopg2.Error as e:
        print(f"Error checking if link is classified and tagged: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def reset_null_tags():
    """Find rows that have status 'in_process', classify = 1, title = NULL and set status = ready"""
    conn = pg_connect()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE public.pdf_links
        SET status = 'ready'
        WHERE status = 'in_process'
        AND classify = 1
        AND title IS NULL
        """
    )
    conn.commit()
    cur.close()
    conn.close()


def reset_unprocessed_links(ids):
    """Set status to read for the given ids"""
    conn = pg_connect()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE public.pdf_links
        SET status = 'ready'
        WHERE id = ANY(%s)
        """,
        (ids,),
    )
    conn.commit()
    cur.close()
    conn.close()


def analyze_csv(csv_path):
    """Open as datframe., Use 1st row as columns."""
    df = pd.read_csv(csv_path, header=0, index_col=0)
    print(df.columns)

    # Create new column from Presentations?  where 1 = Yes, 2 = No, 3 = 50/50
    df["classify_op"] = df["Presentation?"].apply(
        lambda x: 1 if x == "Yes" else 2 if x == "No" else 3 if x == "50/50" else 0
    )
    print(df["classify_op"].value_counts())
    print(df["Presentation?"].value_counts())
    # rename LINK column to 'pdf_link
    df.rename(columns={"LINK": "pdf_link"}, inplace=True)


def remove_document_contents():
    conn = sqlite_connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM documents")
    conn.commit()
    cur.close()
    conn.close()

def get_pdf_links_as_CSV():
    import csv
    conn = pg_connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM public.pdf_links")
    rows = cur.fetchall()
    # Write csv file
    with open("pdf_links.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["id", "pdf_link", "classify", "title", "sector", "author", "date",])
        writer.writerows(rows)
        
    



if __name__ == "__main__":
    get_pdf_links_as_CSV()
    # remove_document_contents()
    # docs = fetchLinksForTestingHtm(10)
    # print(docs)
    # csv_path = "docs/ClassifyOpinion.csv"
    # print(os.path.exists(csv_path))
    # print(analyze_csv(csv_path))
    # print()
    # reset_null_tags()
    # link = "https://www.sec.gov/files/sec-office-investor-advocate-report-objectives-fy2021.pdf"
    # od = is_link_classified_and_tagged(link)
    # print(od['classify'] == 1, od['title'] is None)

    # ##################### TODO
    # This doc causes chrom to ask to keep or not (security reasons)
    #   http://ir.bauschhealth.com/~/media/Files/V/Valeant-IR/reports-and-presentations/q3-2016-earnings-presentation.pdf
    #   Test it and fixit later
    #
    # THis doc is a page not found-- but it triggers a download process????
    # 'https://investors.personalis.com/static-files/3c11319a-f39a-4a31-bcd3-1702b82adf4d'
