from setuptools import setup, find_packages

setup(
    name="human_in_loop",  # Replace with your package name
    version="0.1.1",
    package_dir={"": "src"},  # Tells setuptools that packages are under src directory
    packages=find_packages(where="src"),  # Find all packages in src
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=[
        "Flask>=2.0.0",  # Flask web framework
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
        "beautifulsoup4"
    ],
    entry_points={
        "console_scripts": [
            "start-web-batch=web_batch.app:main",  # Assuming 'main' is your Flask app's startup function
            "start-file-mon=file_mon:main",  # Replace 'main' with your actual function to start file_mon
        ],
    },
)
