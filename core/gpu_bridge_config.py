"""Identify physical GPUs by UUID, including multiple cards of the same model."""

import csv
from dataclasses import dataclass
import io
import subprocess


@dataclass(frozen=True)
class GPU:
    index: int
    uuid: str
    name: str
    memory_mib: int

    @property
    def label(self) -> str:
        return f"GPU {self.index}  ·  {self.name}  ·  {self.memory_mib / 1024:.0f} GB"


def parse_gpus(output: str) -> list[GPU]:
    return [
        GPU(int(index.strip()), uuid.strip(), name.strip(), int(memory.strip()))
        for index, uuid, name, memory in csv.reader(io.StringIO(output))
        if index.strip()
    ]


def get_available_gpus() -> list[GPU]:
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,uuid,name,memory.total", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, check=True, timeout=10,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return parse_gpus(result.stdout)
