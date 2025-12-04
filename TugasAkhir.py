import customtkinter as ctk
from tkinter import messagebox
import json
import os
import sys
from datetime import datetime, date

COLOR_BG_MAIN = "#1a1f2c"
COLOR_BG_SIDEBAR = "#222b33"
COLOR_ACCENT = "#32a89b"
COLOR_TEXT_WHITE = "#ffffff"
COLOR_TEXT_GRAY = "#a0aec0"
COLOR_DANGER = "#e53e3e"
COLOR_WARNING = "#d69e2e"
COLOR_SUCCESS = "#38a169"

ctk.set_appearance_mode("Dark")

class Stack:
    def __init__(self): self.items = []
    def push(self, value): self.items.append(value)
    def pop(self): return self.items.pop() if self.items else None

class Queue:
    def __init__(self): self.items = []
    def enqueue(self, value): self.items.append(value)
    def dequeue(self): return self.items.pop(0) if self.items else None

class Item:
    category_counter = {}

    def __init__(self, name, category, price, stock, sku=None):
        self.name = name
        self.category = category
        self.price = price
        self.stock = stock

        if sku:
            self.sku = sku
            if category not in Item.category_counter:
                Item.category_counter[category] = 1
        else:
            if category not in Item.category_counter:
                Item.category_counter[category] = 1

            num = Item.category_counter[category]
            cat_prefix = category[:3].upper() if len(category) >= 3 else category.upper()
            self.sku = f"{cat_prefix}-{num:03d}"
            Item.category_counter[category] += 1

class InventorySystem:
    def __init__(self):
        self.items = []

        self.stock_in = Queue()
        self.stock_out = Stack()
        self.recent_activity = []
        
        self.daily_in = 0
        self.daily_out = 0
        self.current_date = date.today()

        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(__file__)
            
        self.data_file = os.path.join(application_path, "inventory_data.json")
        print(f"File database lokasi di: {self.data_file}")
        
        self.load_data()

    def load_data(self):
        if not os.path.exists(self.data_file):
            return

        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)

                last_date_str = data.get("date", str(date.today()))
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()

                if last_date == date.today():
                    self.daily_in = data.get("daily_in", 0)
                    self.daily_out = data.get("daily_out", 0)
                else:
                    self.daily_in = 0
                    self.daily_out = 0
                    print("System: Hari berganti, reset daily stats.")

                self.items = []
                Item.category_counter = {}
                for item_data in data.get("items", []):
                    new_item = Item(item_data['name'], item_data['category'], item_data['price'], item_data['stock'])
                    new_item.sku = item_data['sku'] 
                    self.items.append(new_item)

                self.recent_activity = data.get("recent_activity", [])

        except Exception as e:
            print(f"Gagal load data: {e}")

    def save_data(self):
        try:
            items_data = []
            for item in self.items:
                items_data.append({
                    "name": item.name,
                    "sku": item.sku,
                    "category": item.category,
                    "price": item.price,
                    "stock": item.stock
                })

            data = {
                "date": str(date.today()),
                "daily_in": self.daily_in,
                "daily_out": self.daily_out,
                "items": items_data,
                "recent_activity": self.recent_activity
            }

            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=4)
            print("Data berhasil disimpan.")
            
        except Exception as e:
            print(f"Error Saving Data: {e}")
            messagebox.showerror("Save Error", f"Gagal menyimpan data: {e}")

    
    def check_daily_reset(self):
        now = date.today()
        if now != self.current_date:
            self.daily_in = 0
            self.daily_out = 0
            self.current_date = now
            return True
        return False

    def add_item(self, name, category, price, stock):
        self.items.append(Item(name, category, price, stock))
        self.log_activity(f"New Item: {name}", "add")
        self.save_data()

    def search_item(self, name_or_sku):
        text = name_or_sku.strip().lower()
        for item in self.items:
            if text in item.name.lower() or text in item.sku.lower():
                return item
        return None

    def add_stock(self, name, amount):
        item = self.search_item(name)
        if item:
            self.stock_in.enqueue(f"{item.name} (+{amount})")
            item.stock += amount
            self.daily_in += amount
            self.log_activity(f"Stock In: {amount}x {item.name}", "in")
            self.save_data()
            return True
        return False

    def remove_stock(self, name, amount):
        item = self.search_item(name)
        if item and item.stock >= amount:
            self.stock_out.push(f"{item.name} (-{amount})")
            item.stock -= amount
            self.daily_out += amount
            self.log_activity(f"Stock Out: {amount}x {item.name}", "out")
            self.save_data()
            return True
        return False

    def delete_item(self, name):
        item = self.search_item(name)
        if item:
            self.items.remove(item)
            self.log_activity(f"Deleted: {item.name}", "del")
            self.save_data()
            return True
        return False

    def log_activity(self, text, type):
        self.recent_activity.insert(0, {"text": text, "type": type})
        if len(self.recent_activity) > 10:
            self.recent_activity.pop()

    def update_item(self, sku, new_name, new_category, new_price, new_stock):
        item = self.get_item_by_sku(sku)
        if item:
            old_name = item.name
            old_category = item.category

            activity_text = f"Updated Item: {item.sku}"
            
            if old_name != new_name:
                activity_text += f" (Name: {old_name} -> {new_name})"
            
            if old_category != new_category:
                activity_text += f" (Category: {old_category} -> {new_category})"
            
            item.name = new_name
            item.category = new_category
            
            self.log_activity(activity_text, "edit")
            self.save_data()
            return True
        return False

class InventoryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.system = InventorySystem()
        self.system.load_data()

        self.title("Faaza Gadget Store Inventory Manager")
        self.geometry("1200x700")
        self.configure(fg_color=COLOR_BG_MAIN)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_active_button = None
        self.create_sidebar()
        self.create_pages()
        self.show_frame("Dashboard")
        
        self.update_time_system()

    def update_time_system(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        current_date = now.strftime("%A, %d %b %Y")
        
        self.lbl_time.configure(text=current_time)
        self.lbl_date.configure(text=current_date)

        if self.system.check_daily_reset():
            self.refresh_data()
            print("System: Daily stats reset triggered.")

        self.after(1000, self.update_time_system)

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=COLOR_BG_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        profile_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        profile_frame.grid(row=0, column=0, padx=20, pady=30, sticky="ew")
        avatar = ctk.CTkLabel(profile_frame, text="f", width=50, height=50, corner_radius=0, fg_color=COLOR_ACCENT, text_color=COLOR_TEXT_WHITE, font=ctk.CTkFont(size=30, weight="bold"))
        avatar.pack(side="left")
        user_info = ctk.CTkFrame(profile_frame, fg_color="transparent")
        user_info.pack(side="left", padx=10)
        ctk.CTkLabel(user_info, text="Faaza Gadget Store", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLOR_TEXT_WHITE).pack(anchor="w")
        ctk.CTkLabel(user_info, text="Inventory Manager", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_GRAY).pack(anchor="w")

        self.btn_dash = self.create_sidebar_btn(1, "Dashboard", "Dashboard")
        self.btn_inv = self.create_sidebar_btn(2, "Inventory List", "Inventory")
        self.btn_in = self.create_sidebar_btn(3, "Stock In", "StockIn")
        self.btn_out = self.create_sidebar_btn(4, "Stock Out", "StockOut")

        self.time_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.time_frame.grid(row=7, column=0, sticky="ew", padx=20, pady=20)
        
        self.lbl_time = ctk.CTkLabel(self.time_frame, text="00:00:00", font=ctk.CTkFont(size=24, weight="bold"), text_color=COLOR_TEXT_WHITE)
        self.lbl_time.pack(anchor="w")
        
        self.lbl_date = ctk.CTkLabel(self.time_frame, text="Monday, 01 Jan 2024", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_GRAY)
        self.lbl_date.pack(anchor="w")

    def create_sidebar_btn(self, row, text, page_name):
        btn = ctk.CTkButton(self.sidebar, text=text,
                            fg_color="transparent",
                            text_color=COLOR_TEXT_GRAY,
                            hover_color=COLOR_BG_MAIN,
                            anchor="w",
                            height=45,
                            font=ctk.CTkFont(size=14),
                            command=lambda p=page_name: self.show_frame(p) if p else None)
        btn.grid(row=row, column=0, padx=15, pady=5, sticky="ew")
        return btn

    def create_pages(self):
        self.frames = {}
        content_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        content_container.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        content_container.grid_rowconfigure(0, weight=1)
        content_container.grid_columnconfigure(0, weight=1)

        frame_dash = ctk.CTkFrame(content_container, fg_color="transparent")
        self.frames["Dashboard"] = frame_dash

        ctk.CTkLabel(frame_dash, text="Dashboard Overview", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLOR_TEXT_WHITE).pack(anchor="w", pady=(0, 25))

        stats_grid = ctk.CTkFrame(frame_dash, fg_color="transparent")
        stats_grid.pack(fill="x")
        for i in range(4): stats_grid.grid_columnconfigure(i, weight=1)

        self.card_total = self.create_dash_card(stats_grid, 0, "", "Total Items", "0")
        self.card_low = self.create_dash_card(stats_grid, 1, "", "Low Stock Alerts", "0")
        self.card_in = self.create_dash_card(stats_grid, 2, "", "Today's Stock-In", "0")
        self.card_out = self.create_dash_card(stats_grid, 3, "", "Today's Stock-Out", "0")

        ctk.CTkLabel(frame_dash, text="Recent Activity", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLOR_TEXT_WHITE).pack(anchor="w", pady=(30, 15))
        self.activity_frame = ctk.CTkFrame(frame_dash, fg_color=COLOR_BG_SIDEBAR, corner_radius=15)
        self.activity_frame.pack(fill="both", expand=True)

        frame_inv = ctk.CTkFrame(content_container, fg_color="transparent")
        self.frames["Inventory"] = frame_inv

        header_inv = ctk.CTkFrame(frame_inv, fg_color="transparent")
        header_inv.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_inv, text="Inventory List", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLOR_TEXT_WHITE).pack(side="left")
        ctk.CTkButton(header_inv, text="+ Add New Item", fg_color=COLOR_ACCENT, font=ctk.CTkFont(weight="bold"), height=40, command=self.popup_add_item).pack(side="right")

        self.search_bar = ctk.CTkEntry(frame_inv, placeholder_text="Search by name or SKU...", height=45, border_width=0, fg_color=COLOR_BG_SIDEBAR, text_color=COLOR_TEXT_WHITE)
        self.search_bar.pack(fill="x", pady=(0, 20))
        self.search_bar.bind("<KeyRelease>", self.on_search_key)
        self.search_bar.bind("<Return>", self.on_search_key)

        table_header = ctk.CTkFrame(frame_inv, fg_color="transparent")
        table_header.pack(fill="x", padx=10, pady=(0,5))
        headers = ["ITEM NAME", "SKU", "CATEGORY", "STOCK", "PRICE", "STATUS", "ACTIONS"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(table_header, text=h, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_GRAY, anchor="w").grid(row=0, column=i, sticky="ew", padx=15)
            if i == 0: 
                table_header.grid_columnconfigure(i, weight=2, uniform="cols")
            else: 
                table_header.grid_columnconfigure(i, weight=1, uniform="cols")

        self.scroll_inv = ctk.CTkScrollableFrame(frame_inv, fg_color="transparent")
        self.scroll_inv.pack(fill="both", expand=True)

        self.create_transaction_page("StockIn", "Stock In (Masuk)", COLOR_ACCENT, self.action_stock_in, content_container)
        self.create_transaction_page("StockOut", "Stock Out (Keluar)", COLOR_DANGER, self.action_stock_out, content_container)

    def create_dash_card(self, parent, col_idx, icon_text, title, value, icon_color=COLOR_ACCENT):
        card = ctk.CTkFrame(parent, fg_color=COLOR_BG_SIDEBAR, corner_radius=15)
        card.grid(row=0, column=col_idx, sticky="ew", padx=10)

        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14), text_color=COLOR_TEXT_GRAY).pack(anchor="w", padx=20)
        val_lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=32, weight="bold"), text_color=COLOR_TEXT_WHITE)
        val_lbl.pack(anchor="w", padx=20, pady=(0, 20))

        card.value_label = val_lbl
        return card

    def create_transaction_page(self, page_name, title, theme_color, action_command, container):
        frame = ctk.CTkFrame(container, fg_color="transparent")
        self.frames[page_name] = frame

        ctk.CTkLabel(frame, text=f"{title}", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLOR_TEXT_WHITE).pack(anchor="w", pady=(0, 30))

        form_card = ctk.CTkFrame(frame, fg_color=COLOR_BG_SIDEBAR, corner_radius=15)
        form_card.pack(fill="x", pady=20)

        ctk.CTkLabel(form_card, text="Product Name / SKU", text_color=COLOR_TEXT_GRAY).pack(anchor="w", padx=30, pady=(30, 10))
        entry_name = ctk.CTkEntry(form_card, placeholder_text="Mouse, MO-001", height=45, border_width=0, fg_color=COLOR_BG_MAIN)
        entry_name.pack(fill="x", padx=30, pady=(0, 20))

        ctk.CTkLabel(form_card, text="Quantity", text_color=COLOR_TEXT_GRAY).pack(anchor="w", padx=30, pady=(0, 10))
        entry_qty = ctk.CTkEntry(form_card, placeholder_text="1", height=45, border_width=0, fg_color=COLOR_BG_MAIN)
        entry_qty.pack(fill="x", padx=30, pady=(0, 30))

        btn_text = "Confirm Stock In" if page_name == "StockIn" else "Confirm Stock Out"
        ctk.CTkButton(frame, text=btn_text, fg_color=theme_color, height=55, font=ctk.CTkFont(size=16, weight="bold"),
                      command=lambda: action_command(entry_name, entry_qty)).pack(fill="x", pady=20)

    def on_search_key(self, event=None):
        self.refresh_data()

    def show_frame(self, page_name):
        for frame in self.frames.values(): frame.grid_forget()
        self.frames[page_name].grid(row=0, column=0, sticky="nsew")
        self.update_sidebar_active_state(page_name)
        self.refresh_data()

    def update_sidebar_active_state(self, page_name):
        btns = [self.btn_dash, self.btn_inv, self.btn_in, self.btn_out]
        for btn in btns:
            btn.configure(fg_color="transparent", text_color=COLOR_TEXT_GRAY)

        if page_name == "Dashboard": self.btn_dash.configure(fg_color=COLOR_ACCENT, text_color=COLOR_TEXT_WHITE)
        elif page_name == "Inventory": self.btn_inv.configure(fg_color=COLOR_ACCENT, text_color=COLOR_TEXT_WHITE)
        elif page_name == "StockIn": self.btn_in.configure(fg_color=COLOR_ACCENT, text_color=COLOR_TEXT_WHITE)
        elif page_name == "StockOut": self.btn_out.configure(fg_color=COLOR_ACCENT, text_color=COLOR_TEXT_WHITE)

    def refresh_data(self):
        total = sum(item.stock for item in self.system.items)
        low = sum(1 for item in self.system.items if item.stock < 10)
        in_today = self.system.daily_in
        out_today = self.system.daily_out
        self.system.save_data()

        self.card_total.value_label.configure(text=f"{total:,}")
        self.card_low.value_label.configure(text=str(low))
        self.card_in.value_label.configure(text=f"+{in_today}")
        self.card_out.value_label.configure(text=f"-{out_today}")

        for widget in self.activity_frame.winfo_children(): widget.destroy()
        if not self.system.recent_activity:
            ctk.CTkLabel(self.activity_frame, text="No recent activity.", text_color=COLOR_TEXT_GRAY).pack(pady=20)
        else:
            for act in self.system.recent_activity:
                row = ctk.CTkFrame(self.activity_frame, fg_color="transparent")
                row.pack(fill="x", padx=20, pady=10)
                ctk.CTkLabel(row, text=act['text'], text_color=COLOR_TEXT_WHITE).pack(side="left")

        for widget in self.scroll_inv.winfo_children(): widget.destroy()

        query = ""
        if hasattr(self, "search_bar"):
            query = self.search_bar.get().strip().lower()

        if query:
            items_to_show = [item for item in self.system.items if query in item.name.lower() or query in item.sku.lower()]
        else:
            items_to_show = list(self.system.items)

        for item in items_to_show:
            row = ctk.CTkFrame(self.scroll_inv, fg_color=COLOR_BG_SIDEBAR, corner_radius=10)
            row.pack(fill="x", pady=5, padx=15)
            for i in range(7): 
                if i == 0:
                    row.grid_columnconfigure(i, weight=2, uniform="cols")
                else:
                    row.grid_columnconfigure(i, weight=1, uniform="cols")

            ctk.CTkLabel(row, text=item.name, font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=15, pady=15)
            ctk.CTkLabel(row, text=item.sku, text_color=COLOR_TEXT_GRAY, anchor="w").grid(row=0, column=1, sticky="ew", padx=5)
            ctk.CTkLabel(row, text=item.category, anchor="w").grid(row=0, column=2, sticky="ew", padx=35)
            ctk.CTkLabel(row, text=str(item.stock), anchor="w").grid(row=0, column=3, sticky="ew", padx=30)
            ctk.CTkLabel(row, text=f"Rp{item.price:,}", anchor="w").grid(row=0, column=4, sticky="ew", padx=20)

            status_color = COLOR_SUCCESS if item.stock > 20 else COLOR_WARNING if item.stock > 0 else COLOR_DANGER
            status_text = "In Stock" if item.stock > 20 else "Low Stock" if item.stock > 0 else "Out of Stock"
            badge = ctk.CTkFrame(row, fg_color=status_color, corner_radius=15, height=25)
            badge.grid(row=0, column=5, sticky="ew", padx=20)
            ctk.CTkLabel(badge, text=status_text, font=ctk.CTkFont(size=8), text_color=COLOR_BG_MAIN).pack(padx=10, pady=2)

            action_frame = ctk.CTkFrame(row, fg_color="transparent")
            action_frame.grid(row=0, column=6, sticky="ew", padx=30)
            ctk.CTkButton(action_frame, text="Hapus", font=ctk.CTkFont(size=10), width=40, fg_color=COLOR_BG_MAIN, hover_color=COLOR_DANGER, command=lambda n=item.name: self.action_delete(n)).pack()
            

    def action_stock_in(self, entry_name, entry_qty):
        name = entry_name.get(); qty = entry_qty.get()
        if name and qty.isdigit():
            if self.system.add_stock(name, int(qty)):
                messagebox.showinfo("Success", f"Stok {name} berhasil ditambah ke Queue!")
                entry_name.delete(0, 'end'); entry_qty.delete(0, 'end')
                self.refresh_data()
                self.system.save_data()
            else: messagebox.showerror("Error", "Barang tidak ditemukan!")
        else: messagebox.showwarning("Invalid", "Cek inputan nama dan jumlah.")

    def action_stock_out(self, entry_name, entry_qty):
        name = entry_name.get(); qty = entry_qty.get()
        if name and qty.isdigit():
            if self.system.remove_stock(name, int(qty)):
                messagebox.showinfo("Success", f"Stok {name} berhasil dikurangi (Stack Push)!")
                entry_name.delete(0, 'end'); entry_qty.delete(0, 'end')
                self.refresh_data()
                self.system.save_data()
            else: messagebox.showerror("Error", "Barang tidak ditemukan atau stok habis!")
        else: messagebox.showwarning("Invalid", "Cek inputan nama dan jumlah.")

    def action_delete(self, name):
        if messagebox.askyesno("Confirm Delete", f"Yakin menghapus '{name}'?"):
            self.system.delete_item(name)
            self.refresh_data()
            self.system.save_data()

    def popup_add_item(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Add New Item")
        popup.geometry("400x450")
        popup.grab_set()

        ctk.CTkLabel(popup, text="Add New Item", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        frame = ctk.CTkFrame(popup, fg_color="transparent")
        frame.pack(pady=10, fill="x", padx=20)

        ctk.CTkLabel(frame, text="Nama Barang").pack(anchor="w")
        entry_name = ctk.CTkEntry(frame, placeholder_text="Contoh: Headset RGB")
        entry_name.pack(fill="x", pady=(0,10))

        ctk.CTkLabel(frame, text="Kategori").pack(anchor="w")
        entry_cat = ctk.CTkEntry(frame, placeholder_text="Contoh: Audio")
        entry_cat.pack(fill="x", pady=(0,10))

        ctk.CTkLabel(frame, text="Harga").pack(anchor="w")
        entry_price = ctk.CTkEntry(frame, placeholder_text="350000")
        entry_price.pack(fill="x", pady=(0,10))

        ctk.CTkLabel(frame, text="Stok Awal").pack(anchor="w")
        entry_stock = ctk.CTkEntry(frame, placeholder_text="10")
        entry_stock.pack(fill="x", pady=(0,10))
        

        def submit():
            name = entry_name.get()
            cat = entry_cat.get()
            price = entry_price.get()
            stock = entry_stock.get()

            if not (name and cat and price.isdigit() and stock.isdigit()):
                messagebox.showerror("Error", "Isi semua data dengan benar.")
                return

            self.system.add_item(name, cat, int(price), int(stock))
            self.refresh_data()
            self.system.save_data()
            messagebox.showinfo("Success", "Barang ditambahkan!")
            popup.destroy()

        ctk.CTkButton(popup, text="Tambah Barang", fg_color=COLOR_ACCENT,
                      height=40, command=submit).pack(pady=15)


if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
