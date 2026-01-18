from ui import MainWindow

# --- INFORMACIÓN DEL PROYECTO ---
__version__ = '3.0.0'
# -------------------------------

if __name__ == "__main__":
    app = MainWindow(__version__)
    app.mainloop()
