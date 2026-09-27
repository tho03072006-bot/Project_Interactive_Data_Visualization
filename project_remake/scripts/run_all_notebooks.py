from __future__ import annotations

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
NOTEBOOKS = [
    "00_kiem_ke_nguon_va_schema_raw.ipynb",
    "01_lam_sach_du_lieu_crypto.ipynb",
    "02_lam_sach_du_lieu_vi_mo.ipynb",
    "03_lam_sach_du_lieu_quoc_gia.ipynb",
    "04_tao_truong_va_ket_bang.ipynb",
    "05_kiem_tra_chat_luong_processed.ipynb",
    "06_eda_thi_truong_crypto.ipynb",
    "07_eda_boi_canh_vi_mo.ipynb",
    "08_eda_moi_tuong_quan.ipynb",
]


def main() -> int:
    for name in NOTEBOOKS:
        path = SCRIPTS / name
        print(f"\n[RUN] {name}", flush=True)
        notebook = nbformat.read(path, as_version=4)
        client = NotebookClient(
            notebook,
            timeout=900,
            kernel_name="python3",
            resources={"metadata": {"path": str(ROOT)}},
            allow_errors=False,
        )
        client.execute()
        nbformat.write(notebook, path)
        print(f"[OK ] {name}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

