"""Setup module for py2n."""
from pathlib import Path
from setuptools import setup

PROJECT_DIR = Path(__file__).parent.resolve()
README_FILE = PROJECT_DIR / "README.md"
VERSION = "0.0.9"

setup(
    name='py2n',
    version=VERSION,
    license="MIT",
    url="https://github.com/elektr0nisch/py2n",
    author="Linus Groschke",
    author_email="linus@elektronisch.dev",
    description="Python library for 2N® devices",
    long_description=README_FILE.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=['py2n'],
    python_requires=">=3.9",
    zip_safe=True,
    platforms="any",
    install_requires=["aiohttp"],
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
)