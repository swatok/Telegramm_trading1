from setuptools import setup, find_packages

setup(
    name="trading_bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot',
        'solana',
        'asyncio',
        'aiohttp',
        'python-dotenv',
        'websockets',
        'requests',
        'sqlalchemy',
        'pytest',
    ],
    python_requires='>=3.8',
    author="Your Name",
    author_email="your.email@example.com",
    description="Telegram trading bot for Solana",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
) 