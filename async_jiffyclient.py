#!/usr/bin/python3
"""Asynchronous variant of JiffyClient using aiohttp."""

import sys
import uuid
import xml.etree.ElementTree as ET

from JiffyClient import JiffyClient

try:
    import aiohttp
except Exception as e:  # pragma: no cover - used only when aiohttp installed
    aiohttp = None


class AsyncJiffyClient(JiffyClient):
    """Jiffy client using asyncio/aiohttp for network operations."""

    def __init__(self):
        super().__init__()
        if aiohttp is None:  # pragma: no cover - for safety
            raise RuntimeError("aiohttp is required for AsyncJiffyClient")
        self.AIOSESSION = aiohttp.ClientSession()

    async def close(self):
        await self.AIOSESSION.close()

    async def getServerVersion_async(self):
        try:
            async with self.AIOSESSION.get(
                self.SERVER_URL + "/JiffyVersion",
                headers=self.defaultRequestHeaders,
            ) as resp:
                text = await resp.text()
        except Exception:
            print("JiffyClient: [ERROR] - Cannot connect to server", self.SERVER_URL)
            sys.exit(4)
        self.SERVER_VERSION = self.gpgVerifyAndExtractText(data=text)
        print(
            "JiffyClient: Server",
            self.SERVER_URL,
            "-",
            self.SERVER_VERSION,
            "(Signature Timestamp:",
            self.lastInSigTimestamp_text,
            ")",
        )

    async def startSession_async(self):
        initialRSTR = str(uuid.uuid4())
        payload = {
            "data": self.gpgSignAndEncrypt(
                recipient=self.SERVER_KEY, data=initialRSTR
            )
        }
        async with self.AIOSESSION.post(
            self.SERVER_URL + "/JiffySession",
            data=payload,
            headers=self.defaultRequestHeaders,
            timeout=5,
        ) as resp:
            text = await resp.text()
        self.sessionUUIDS = self.gpgDecryptAndVerify(text)
        if self.sessionUUIDS is None:
            print(
                "JiffyClient: [ERROR]. Is the GPG Agent running? \"eval $(gpg-agent --daemon)\". Alternatively, verify entire trust chain."
            )
            sys.exit(5)
        await self.startSession2_async()

    async def startSession2_async(self):
        payload = {
            "data": self.gpgSignAndEncrypt(
                recipient=self.SERVER_KEY, data=str(self.sessionUUIDS)
            )
        }
        async with self.AIOSESSION.post(
            self.SERVER_URL + "/JiffySession2",
            data=payload,
            headers=self.defaultRequestHeaders,
            timeout=5,
        ) as resp:
            await resp.text()

    async def endSession_async(self):
        payload = {
            "session": self.gpgSignAndEncrypt(
                recipient=self.SERVER_KEY, data=str(self.sessionUUIDS)
            )
        }
        async with self.AIOSESSION.post(
            self.SERVER_URL + "/JiffyBye",
            data=payload,
            headers=self.defaultRequestHeaders,
            timeout=5,
        ) as resp:
            await resp.text()
        self.sessionUUIDS = None

    async def sendJiffies_async(self, jiffies):
        jTop = ET.Element("Jiffies")
        for jiffie in jiffies:
            nodo = ET.SubElement(jTop, "jiffy")
            nodo.text = self.gpgSignAndEncrypt(recipient=jiffie[0], data=jiffie[1])
            nodo.set("rcpt", jiffie[0])
        el_xml = ET.tostring(jTop, encoding="utf-8", method="xml")
        payload = {
            "session": self.gpgSignAndEncrypt(
                recipient=self.SERVER_KEY, data=str(self.sessionUUIDS)
            ),
            "data": self.gpgSignAndEncrypt(
                recipient=self.SERVER_KEY, data=el_xml
            ),
        }
        async with self.AIOSESSION.post(
            self.SERVER_URL + "/JiffySend",
            data=payload,
            headers=self.defaultRequestHeaders,
            timeout=30,
        ) as resp:
            await resp.text()

    async def receiveJiffies_async(self):
        jiffies = []
        payload = {
            "session": self.gpgSignAndEncrypt(
                recipient=self.SERVER_KEY, data=str(self.sessionUUIDS)
            )
        }
        async with self.AIOSESSION.post(
            self.SERVER_URL + "/JiffyRecv",
            data=payload,
            headers=self.defaultRequestHeaders,
            timeout=30,
        ) as resp:
            text = await resp.text()
        decrypted = self.gpgDecryptAndVerify(text)
        if decrypted is None:
            await self.startSession_async()
            async with self.AIOSESSION.post(
                self.SERVER_URL + "/JiffyRecv",
                data=payload,
                headers=self.defaultRequestHeaders,
                timeout=30,
            ) as resp:
                text = await resp.text()
            decrypted = self.gpgDecryptAndVerify(text)
            if decrypted is None:
                return None
        if (
            decrypted.trust_level is not None
            and decrypted.trust_level >= decrypted.TRUST_FULLY
        ):
            jTop = ET.fromstring(str(decrypted))
            if jTop.tag == "Jiffies":
                for jiffy in jTop.findall("jiffy"):
                    jiffies.append(self.returnJiffy(jiffy))
                return jiffies

