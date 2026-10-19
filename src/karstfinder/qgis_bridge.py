"""Length-prefixed localhost client for the installed QGIS MCP plugin.

Uses the plugin's documented-in-source wire format; no MCP server is exposed
as a callable tool in this session, so we verify the same plugin transport.
"""
import json
import socket
import struct


def request(command, params=None, host="127.0.0.1", port=9876, timeout=30):
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        payload = json.dumps({"type": command, "params": params or {}}).encode()
        sock.sendall(struct.pack(">I", len(payload)) + payload)

        def receive(n):
            data = b""
            while len(data) < n:
                block = sock.recv(n - len(data))
                if not block:
                    raise EOFError("QGIS MCP closed the connection")
                data += block
            return data

        size = struct.unpack(">I", receive(4))[0]
        if size > 64 * 1024 * 1024:
            raise ValueError("Unexpectedly large QGIS response")
        response = json.loads(receive(size))
        if response.get("status") != "success":
            raise RuntimeError(response)
        return response["result"]
