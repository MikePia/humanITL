import pandas as pd


class PersistDF:
    def __init__(self):
        self.df = pd.DataFrame()

    def add_rows(self, new_df):
        """Add as new rows, set new rows status to unprocessed"""
        new_df["status"] = "unprocessed"
        self.df = pd.concat([self.df, new_df])

    def set_status(self, url, status):
        # Update the status of a row based on URL
        if self.df.empty or url not in self.df["pdf_link"].values:
            return
        self.df.loc[self.df["pdf_link"] == url, "status"] = status

    def update_tags_in_df(self, url, tags):
        self.df.loc[
            self.df["pdf_link"] == url, ["title", "date", "author", "sector"]
        ] = [tags["title"], tags["date"], tags["author"], tags["sector"]]

    def get_processed(self):
        # Return rows that have been processed
        if self.df.empty:
            return self.df
        return self.df[self.df["status"] == "processed"]

    def set_processed(self):
        # Set unprocessed row to processed so the database can change their status back to ready
        if self.df.empty:
            return
        self.df.loc[self.df["status"] == "unprocessed", "status"] = "processed"

    def remove_processed(self):
        # Remove processed rows from DataFrame
        if self.df.empty:
            return
        self.df = self.df[self.df["status"] != "processed"]

    def is_processed(self, url):
        row = self.df[self.df["pdf_link"] == url]
        if row.empty:
            return False
        first_row = row.iloc[0]

        classify_value = first_row["classify"]
        if classify_value == 2:
            return True
        elif classify_value in [1, 3]:
            title = first_row["title"]
            filename_location = first_row["filename_location"]
            if pd.notna(title) and pd.notna(filename_location):
                return True

        return False
    
    def is_tagged(self, url):
        row = self.df[self.df["pdf_link"] == url]
        if row.empty:
            return False
        first_row = row.iloc[0]

        if first_row["title"] is not None and first_row["date"] is not None:
            return True

        return False

    def update_classification(self, url, filename, prediction):
        if self.df.empty or url not in self.df["pdf_link"].values:
            return
        self.df.loc[self.df["pdf_link"] == url, "classify"] = int(prediction)

        # We only want to archive Investor Presentations
        if prediction in [1, 3]:
            self.df.loc[self.df["pdf_link"] == url, "filename_location"] = filename
            
    def set_uncertainty(self, url):
        if self.df.empty or url not in self.df["pdf_link"].values:
            return
        self.df.loc[self.df["pdf_link"] == url, "uncertainty"] = True
        
    def remove_uncertainty(self, url):
        if self.df.empty or url not in self.df["pdf_link"].values:
            return
        self.df.loc[self.df["pdf_link"] == url, "uncertainty"] = False
        self.df.loc[self.df["pdf_link"] == url, "classify"] = None

    def reset(self):
        # Reset the DataFrame after batch operations
        self.df = pd.DataFrame()


# Instantiate the PersistDF to be used across the application
persist = PersistDF()
