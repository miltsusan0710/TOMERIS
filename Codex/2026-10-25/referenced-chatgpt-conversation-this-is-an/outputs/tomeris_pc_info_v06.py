"""Fixed read-only PC metrics. No network, file contents, or persistence."""
import ctypes
from ctypes import wintypes
import os
import platform
import shutil
import sys

VERSION = "0.6.0-standalone"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"


def memory_info():
    if sys.platform != "win32":
        return {"status": "Windows以外では取得しません"}

    class MemoryStatus(ctypes.Structure):
        _fields_ = [("length", wintypes.DWORD), ("load", wintypes.DWORD)] + [
            (name, ctypes.c_ulonglong) for name in (
                "total", "available", "page_total", "page_available",
                "virtual_total", "virtual_available", "extended_available")]

    status = MemoryStatus()
    status.length = ctypes.sizeof(status)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MemoryStatus)]
    kernel.GlobalMemoryStatusEx.restype = wintypes.BOOL
    if not kernel.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError("メモリー情報を取得できません")
    return {"total_bytes": status.total, "available_bytes": status.available,
            "used_percent": status.load}


def pc_info():
    """Read a fixed set of aggregate values; no identifiers or file contents."""
    result = {
        "os": {"name": platform.system(), "release": platform.release(),
               "version": platform.version(), "architecture": platform.machine()},
        "cpu": {"logical_processors": os.cpu_count()},
        "python": platform.python_version(),
    }
    for name, collect in (("memory", memory_info), ("system_disk", disk_info)):
        try:
            result[name] = collect()
        except OSError:
            result[name] = {"status": "取得できません"}
    return result


def disk_info():
    root = os.path.abspath(os.sep)
    if sys.platform == "win32":
        root = os.path.splitdrive(sys.executable)[0] + "\\"
    usage = shutil.disk_usage(root)
    return {"scope": "Python実行ドライブ", "total_bytes": usage.total,
            "free_bytes": usage.free, "used_bytes": usage.used}

