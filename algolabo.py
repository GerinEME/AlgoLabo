# -*- coding: utf-8 -*-
"""AlgoLabo — point d'entree de l'application."""

import tkinter as tk
import ctypes
from app import AlgoLaboApp, resource_path

if __name__ == '__main__':
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('AlgoLabo')
    except Exception:
        pass
    root = tk.Tk()
    try:
        root.iconbitmap(resource_path('resources/favicon.ico'))
    except Exception:
        pass
    app = AlgoLaboApp(root)
    root.mainloop()
