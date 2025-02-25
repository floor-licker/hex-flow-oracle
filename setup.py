from setuptools import setup, find_packages

setup(
    name="hex-flow-oracle",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "web3[async]>=6.0.0",
        "websockets>=10.0",
        "goplus>=0.2.4",
        "aiohttp>=3.8.0",
        "tqdm>=4.65.0",
    ],
    entry_points={
        'console_scripts': [
            'hex-flow-oracle=hex_flow_oracle.main:main',
        ],
    },
    python_requires='>=3.8',
) 