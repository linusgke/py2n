# Py2N

<img src="https://user-images.githubusercontent.com/38865194/210242643-8f2cef4d-e426-4280-9263-63bee2b66eef.png" width=20% height=20%>

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
            host="192.168.1.69",
            username="username",
            password="password",
            # auth_method="digest", # default: "basic"
            # protocol="https", # default: "http"
            # ssl_verify=True, # default: False
        ),
    )

    await device.restart()

asyncio.run(main())
```

`auth_method` controls HTTP auth scheme and supports `"basic"` (default) and `"digest"`. Digest auth relies on `aiohttp.DigestAuthMiddleware`. 2N recommends Digest Auth, especially if using plain HTTP instead of HTTPS.
`ssl_verify` controls TLS certificate verification for HTTPS connections. Requires the device to present a trusted server certificate (e.g. Let's Encrypt).
