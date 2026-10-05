"""A guard that keeps a Python process off the network (NFR-2, AC-9, D-77): every attempt to resolve
or connect to a host other than this machine's loopback is refused with OSError and recorded. Binding
and loopback (127.0.0.1, ::1, localhost) still work, so the app serves itself as usual.

test_offline.py installs it around the whole flow in-process; offline_guard/sitecustomize.py installs
it in a real server process for the rehearsal (frontend/scripts/rehearse.ts), which reads the log of
refused attempts at the end. Standard library only.
"""

from __future__ import annotations

import socket
from collections.abc import Callable
from typing import Any

LOOPBACK = {"127.0.0.1", "::1", "localhost", "", None}

attempts: list[str] = []
_saved: dict[str, Any] = {}


def _host(address: Any) -> Any:
    return address[0] if isinstance(address, tuple) and address else address


def _refuse(what: str, host: Any, log: str | None) -> None:
    entry = f"{what} {host}"
    attempts.append(entry)
    if log:
        with open(log, "a", encoding="utf-8") as out:
            out.write(entry + "\n")
    raise OSError(f"SeedFactory offline guard: {entry} refused, the app must not reach the network")


def install(log: str | None = None) -> Callable[[], None]:
    """Patch socket's lookups and connects; returns the function that undoes it."""
    if _saved:
        return uninstall
    _saved.update(
        getaddrinfo=socket.getaddrinfo,
        gethostbyname=socket.gethostbyname,
        connect=socket.socket.connect,
        connect_ex=socket.socket.connect_ex,
    )

    def getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> Any:
        if host not in LOOPBACK and not str(host).startswith("127."):
            _refuse("lookup", host, log)
        return _saved["getaddrinfo"](host, *args, **kwargs)

    def gethostbyname(host: str) -> str:
        if host not in LOOPBACK and not host.startswith("127."):
            _refuse("lookup", host, log)
        return _saved["gethostbyname"](host)

    def checked(name: str) -> Callable[..., Any]:
        def method(self: socket.socket, address: Any) -> Any:
            host = _host(address)
            if self.family in (socket.AF_INET, socket.AF_INET6) and host not in LOOPBACK and not str(host).startswith("127."):
                _refuse("connect", host, log)
            return _saved[name](self, address)

        return method

    socket.getaddrinfo = getaddrinfo
    socket.gethostbyname = gethostbyname
    socket.socket.connect = checked("connect")  # type: ignore[method-assign]
    socket.socket.connect_ex = checked("connect_ex")  # type: ignore[method-assign]
    return uninstall


def uninstall() -> None:
    if not _saved:
        return
    socket.getaddrinfo = _saved["getaddrinfo"]
    socket.gethostbyname = _saved["gethostbyname"]
    socket.socket.connect = _saved["connect"]  # type: ignore[method-assign]
    socket.socket.connect_ex = _saved["connect_ex"]  # type: ignore[method-assign]
    _saved.clear()
