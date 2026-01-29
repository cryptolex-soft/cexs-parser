import requests
import asyncio
import aiohttp
import sys 
import cex_parsers.gate as gate_parser

if __name__ == "__main__":
    mode = sys.argv[1].lower()
    if mode == "gate":
        asyncio.run(gate_parser.main())
        