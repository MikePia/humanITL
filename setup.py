import os
from setuptools import setup, find_packages

base_dir = os.path.dirname(os.path.abspath(__file__))
classify_path = os.path.join(base_dir, '../classify_presentations')
tagger_path = os.path.join(base_dir, '../train_mix_tagger')

setup(
    name="human_in_loop",  # Replace with your package name
    version="0.2.0",
    package_dir={"": "app"},  # Update to point to 'app' directory
    packages=find_packages(where="app"),  # Find all packages in app
    description="Human in the loop to download, classify, tag and archive specific pdfs",
    author="ZeroSubstance",
    author_email="lynnpeter@proton.me",
    license="Proprietary License",
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=[
        "Flask>=2.0.0",  # Flask web framework
        "Flask_Cors",
        "pandas",
        "openai",
        "python-dotenv",
        "tqdm",
        "PyMuPDF",
        "psycopg2-binary",
        "selenium",
        "webdriver-manager",
        "pdf2image",
        "pytesseract",
        "selenium-wire",
        "beautifulsoup4",
        "joblib",
        "celery",
        "redis",
        f"classify @ file://{classify_path}",
        f"tagtrain @ file://{tagger_path}"
    ],
    package_data={
        '':['LICENSE', 'README.md', 'requirements.txt']
    },
    entry_points={
        "console_scripts": [
            "start-web-batch=app.web_batch.app:main",  # Adjusted path assuming 'web_batch.app' is within the 'app' directory
            "start-file-mon=app.file_mon:main",  # Adjusted path assuming 'file_mon' is within the 'app' directory
        ],
    },
)
