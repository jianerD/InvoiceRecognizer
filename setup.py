import os
from cx_Freeze import setup, Executable

setup(
    name="InvoiceTool",
    version="1.0",
    description="发票识别工具",
    options={"build_exe": {"packages": ["pdfplumber", "tkinter"]}},
    executables=[Executable("invoice_gui.py", base="Win32GUI")]
)
