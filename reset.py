import os
import sys

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

file_path = os.path.join(application_path, "inventory_data.json")

if os.path.exists(file_path):
    os.remove(file_path)
    print("Berhasil")
else:   
    print("Gagal")   