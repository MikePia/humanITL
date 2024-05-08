# Human in the Loop
## For Betterpitch
Is a mostly automated  tool to download Investor Presentations  that are identified in our central database and use Chrome to download them. It is remarkably effective compared to using any completely automated tool and much faster.

## The pipeline
* Download --  using a Chrome extension to download and a Flask app to connect url with filename.
* Classify downloaded pdf  using a trained model
* Tag investor presentations using 
  * Trained model to identify the title page for mix types.
  * openai API  to tag.
* Archive the files once processed to AWS buckets and update the file_location in the database

## Dependencies
Dedpends on three projects
* https://github.com/MikePia/bucketlaunch
* https://github.com/MikePia/doc_classify
* https://github.com/MikePia/train_mix_tagger


### Running the app
Set up the environment in .env
Chrome must be set to download pdfs and allow popups
* Start the archiver *bucket launch*
* Start flask
* navigate to localhost:5000
* Click on Load Documnents