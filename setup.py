"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Setup Configuration
============================================================
"""
from setuptools import setup, find_packages

with open("docs/README.md", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="ai-enterprise-test-framework",
    version="1.0.0",
    author="Enterprise QA Team",
    author_email="qa-team@enterprise.com",
    description="AI-Enhanced Enterprise Test Automation Framework with Selenium, PyTest, and ML",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/enterprise/ai-test-framework",
    packages=find_packages(exclude=["tests*", "docs*"]),
    python_requires=">=3.9",
    install_requires=requirements,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "run-tests=scripts.run_tests:main",
            "gen-report=scripts.generate_report:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.ini", "*.json", "*.yaml", "*.yml", "*.html"],
    },
)
