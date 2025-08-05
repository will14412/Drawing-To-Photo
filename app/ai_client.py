"""
Replace the body of `turn_sketch_into_photo` with a real call to
OpenAI Images, Stability, Replicate, etc. (e.g. using httpx).
"""

import asyncio

async def turn_sketch_into_photo(bytes_in: bytes) -> bytes:
    await asyncio.sleep(0.05)   # simulate latency
    return bytes_in             # echo back until you implement real AI
