# Py2N

Asynchronous library to control [2N Telekomunikace® devices](https://www.2n.com)

**This library is under development**

## Requirements

- Python >= 3.9
- aiohttp

## Install
```bash
pip install py2n
```

## Example

```python
from py2n import Py2NDevice, Py2NConnectionData

import asyncio
import aiohttp

async def main():
    """Run with aiohttp ClientSession."""
    async with aiohttp.ClientSession() as session:
        await run(session)


async def run(websession):
    """Use library."""
    device = await Py2NDevice.create(
        websession,
        Py2NConnectionData(
            ip_address="192.168.1.69",
            username="username",
            password="password",
        ),
    )

    await device.restart()

asyncio.run(main())
```
