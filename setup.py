from setuptools import setup

setup(
    name="ollama-experiments",
    version="0.1.0",
    py_modules=["main", "streamlit_app"],  # <-- list your modules
    install_requires=[
        "fastapi",
        "uvicorn",
        "streamlit",
        "ollama",
        "python-docx",
        "pypdf2",
        "setuptools"
    ],
)
