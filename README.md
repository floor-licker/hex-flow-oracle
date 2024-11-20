![Alt text](images/cover-art.png)

To begin using this tool, create a QuickNode account, create a QuickNode endpoint, and copy your QuickNode WSS Provider link into the config.py file.

Note that Github is currently experiencing bugs with users trying to access .pdf files embedded in repositories on Safari. If you wish to view the technical paper, please use an alternative browser such as Chrome.

[View Hex-Flow Oracle Technical Paper](docs/hex-flow-oracle-technical-paper.pdf)

Output of the program is sent to std::out in JSON format. For integration with trading applications, set CLEAN_MODE = True in config.py, this will ensure that no empty messages or heartbeats are ever sent, and the only output will be the hash values of secure and approved tokens of newly created liquidity pools.
