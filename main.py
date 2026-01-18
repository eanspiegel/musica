from ui import MainWindow

# --- INFORMACIÓN DEL PROYECTO ---
__version__ = '1.3.1'
# -------------------------------

if __name__ == "__main__":
    app = MainWindow(__version__)
    app.mainloop()
