# Human in the Loop
## For Betterpitch
Is a tool to download Investor Presentations  that are identified in our central database and use Chrome to download them. It is remarkably effective compared to using any automated tool and much faster.

## The pipeline
* Download  using a Chrome extension to call Flask app to connect url with filename.
* Classify downloaded pdf as  Investor Presentations, Not Investor Presentation or mix Investor Presentations using a trained model
* Tag investor presentations using 
  * Trained model to identify the title page for mix types.
  * openai API  to tag.
* Archive the files once processed to AWS buckets and update the file_location in the database