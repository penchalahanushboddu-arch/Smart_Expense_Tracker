"""
NOVA — Smart Expense & Bill Manager
Modern desktop edition built with CustomTkinter + Matplotlib.

Install:
    py -m pip install customtkinter matplotlib

Run:
    py nova_expense_tracker.py
"""
import json
import os
import csv
import webbrowser
from datetime import date, datetime
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

APP_NAME = "NOVA"
DATA_FILE = Path(__file__).with_name("nova_data.json")

# ---------------------------- THEME -----------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG = "#0B1220"
SIDEBAR = "#101A2C"
CARD = "#142239"
CARD_ALT = "#1C2D46"
BORDER = "#2B405D"
TEXT = "#F5F7FC"
MUTED = "#AAB8CA"
BLUE = "#7896FF"
GREEN = "#45D2A5"
AMBER = "#FFC36B"
PURPLE = "#B29AFF"
RED = "#FF7888"
CYAN = "#58CBE8"
PINK = "#F08FBC"

CATEGORIES = ["Food", "Travel", "Bills", "Groceries", "Entertainment", "Other"]
CATEGORY_COLORS = {
    "Food": BLUE, "Travel": GREEN, "Bills": AMBER,
    "Groceries": PURPLE, "Entertainment": RED, "Other": CYAN
}
PAGE_INFO = {
    "Dashboard": ("Dashboard", "Your financial overview at a glance"),
    "Add Expense": ("Add Expense", "Record and organise every purchase"),
    "Transactions": ("Transactions", "Search, filter and manage expense records"),
    "Analytics": ("Analytics", "Understand your spending patterns"),
    "Generate Bill": ("Generate Bill", "Create, preview and print itemised bills"),
    "Settings & Data": ("Settings & Data", "Manage and export your application data"),
}


def money(value):
    return "₹{:,.2f}".format(float(value or 0))


def load_data():
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            return data.get("expenses", []), data.get("bills", [])
        except (json.JSONDecodeError, OSError, AttributeError):
            pass
    # First-run sample records make the dashboard look populated for a demo.
    today = date.today()
    sample = [
        {"id": "demo1", "date": today.replace(day=3).isoformat(),
         "category": "Groceries", "amount": 2450.50, "description": "Monthly groceries"},
        {"id": "demo2", "date": today.replace(day=7).isoformat(),
         "category": "Bills", "amount": 1250.00, "description": "Electricity bill"},
        {"id": "demo3", "date": today.replace(day=12).isoformat(),
         "category": "Travel", "amount": 620.00, "description": "Cab fare"},
        {"id": "demo4", "date": today.replace(day=18).isoformat(),
         "category": "Food", "amount": 480.00, "description": "Lunch"},
        {"id": "demo5", "date": today.replace(day=21).isoformat(),
         "category": "Entertainment", "amount": 850.00, "description": "Movie tickets"},
    ]
    return sample, []


class NovaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NOVA — Smart Expense & Bill Manager")
        self.geometry("1440x900")
        self.minsize(1100, 720)
        self.configure(fg_color=BG)

        self.expenses, self.bills = load_data()
        self.current_page = "Dashboard"
        self.current_bill = None
        self.bill_item_rows = []
        self.transaction_row_map = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew", padx=(0, 22), pady=18)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self._build_header()
        self.pages_host = ctk.CTkFrame(self.main, fg_color=BG, corner_radius=0)
        self.pages_host.grid(row=1, column=0, sticky="nsew")
        self.pages_host.grid_columnconfigure(0, weight=1)
        self.pages_host.grid_rowconfigure(0, weight=1)

        self._build_pages()
        self._save_data()
        self.show_page("Dashboard")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------------------------- DATA --------------------------------------
    def _save_data(self):
        payload = {"expenses": self.expenses, "bills": self.bills}
        DATA_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _total(self):
        return sum(float(x["amount"]) for x in self.expenses)

    def _category_totals(self):
        result = {}
        for item in self.expenses:
            result[item["category"]] = result.get(item["category"], 0) + float(item["amount"])
        return result

    def _toast(self, message):
        self.status_label.configure(text=message)
        self.after(3200, lambda: self.status_label.configure(text="NOVA • PERSONAL FINANCE"))

    # ---------------------------- COMMON UI ---------------------------------
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=245, fg_color=SIDEBAR, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(20, weight=1)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(25, 34))
        mark = ctk.CTkLabel(brand, text="N", width=46, height=46, corner_radius=14,
                            fg_color=BLUE, text_color="white",
                            font=ctk.CTkFont(size=25, weight="bold"))
        mark.pack(side="left")
        titlebox = ctk.CTkFrame(brand, fg_color="transparent")
        titlebox.pack(side="left", padx=12)
        ctk.CTkLabel(titlebox, text="NOVA", font=ctk.CTkFont(size=21, weight="bold"),
                     text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(titlebox, text="SMART FINANCE SUITE",
                     font=ctk.CTkFont(size=9, weight="bold"), text_color=MUTED).pack(anchor="w")

        ctk.CTkLabel(self.sidebar, text="WORKSPACE", text_color="#8294AD",
                     font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=25, pady=(0, 9))
        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", "▦"), ("Add Expense", "＋"), ("Transactions", "☷"),
            ("Analytics", "◉"), ("Generate Bill", "▤"), ("Settings & Data", "⚙")
        ]
        for name, symbol in nav_items:
            button = ctk.CTkButton(
                self.sidebar, text=f"  {symbol}     {name}", anchor="w",
                height=43, corner_radius=10, fg_color="transparent",
                hover_color=CARD_ALT, text_color=MUTED,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda n=name: self.show_page(n)
            )
            button.pack(fill="x", padx=12, pady=3)
            self.nav_buttons[name] = button

        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(expand=True, fill="both")
        tip = ctk.CTkFrame(self.sidebar, fg_color=CARD, corner_radius=13,
                           border_width=1, border_color=BORDER)
        tip.pack(fill="x", padx=14, pady=(10, 12))
        ctk.CTkLabel(tip, text="✦  MONEY CLARITY", text_color=TEXT,
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=13, pady=(13, 4))
        ctk.CTkLabel(tip, text="Track every rupee. Understand every habit.\nMake smarter financial decisions.",
                     text_color=MUTED, justify="left", wraplength=190,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", padx=13, pady=(0, 13))
        ctk.CTkLabel(self.sidebar, text="NOVA  •  PERSONAL EDITION",
                     text_color="#8294AD", font=ctk.CTkFont(size=9, weight="bold")).pack(pady=(0, 14))

    def _build_header(self):
        header = ctk.CTkFrame(self.main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(2, 20))
        header.grid_columnconfigure(0, weight=1)
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")
        self.page_title = ctk.CTkLabel(left, text="Dashboard",
                                       font=ctk.CTkFont(size=29, weight="bold"), text_color=TEXT)
        self.page_title.pack(anchor="w")
        self.page_subtitle = ctk.CTkLabel(left, text=PAGE_INFO["Dashboard"][1],
                                          font=ctk.CTkFont(size=13), text_color=MUTED)
        self.page_subtitle.pack(anchor="w", pady=(3, 0))
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(right, text=date.today().strftime("%A, %d %B %Y"),
                     text_color=MUTED, font=ctk.CTkFont(size=12)).pack(side="left", padx=12)
        ctk.CTkLabel(right, text="HU", width=40, height=40, corner_radius=20,
                     fg_color=CARD_ALT, text_color=TEXT,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

    def _card(self, parent, **kwargs):
        return ctk.CTkFrame(parent, fg_color=CARD, corner_radius=16,
                            border_width=1, border_color=BORDER, **kwargs)

    def _section_heading(self, parent, title, subtitle=None):
        ctk.CTkLabel(parent, text=title, text_color=TEXT,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(parent, text=subtitle, text_color=MUTED,
                         font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(3, 12))

    def _build_pages(self):
        self.pages = {}
        for name in PAGE_INFO:
            frame = ctk.CTkFrame(self.pages_host, fg_color=BG, corner_radius=0)
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
            self.pages[name] = frame
        self._build_dashboard()
        self._build_add_expense()
        self._build_transactions()
        self._build_analytics()
        self._build_bill_page()
        self._build_settings()

    def show_page(self, name):
        self.current_page = name
        for page in self.pages.values():
            page.grid_remove()
        self.pages[name].grid()
        self.page_title.configure(text=PAGE_INFO[name][0])
        self.page_subtitle.configure(text=PAGE_INFO[name][1])
        for key, button in self.nav_buttons.items():
            if key == name:
                button.configure(fg_color="#263B66", text_color=TEXT)
            else:
                button.configure(fg_color="transparent", text_color=MUTED)
        self.refresh_page(name)

    def refresh_page(self, name):
        if name == "Dashboard":
            self.refresh_dashboard()
        elif name == "Transactions":
            self.refresh_transactions()
        elif name == "Analytics":
            self.refresh_analytics()
        elif name == "Generate Bill":
            self.refresh_bill_history()
        elif name == "Settings & Data":
            self.refresh_storage_info()

    # ---------------------------- DASHBOARD ---------------------------------
    def _build_dashboard(self):
        page = self.pages["Dashboard"]
        page.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(page, text="Welcome back 👋", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=TEXT).grid(row=0, column=0, sticky="w", pady=(0, 2))
        ctk.CTkLabel(page, text="Your financial picture, organised in one place.",
                     font=ctk.CTkFont(size=12), text_color=MUTED).grid(row=1, column=0, sticky="w", pady=(0, 15))

        metrics = ctk.CTkFrame(page, fg_color="transparent")
        metrics.grid(row=2, column=0, sticky="ew")
        for col in range(4):
            metrics.grid_columnconfigure(col, weight=1, uniform="metric")
        self.metric_values = {}
        metric_defs = [
            ("TOTAL EXPENSES", "total", BLUE, "Across all saved records"),
            ("MONTHLY AVERAGE", "average", GREEN, "Average per active month"),
            ("TRANSACTIONS", "count", PURPLE, "Recorded expense entries"),
            ("TOP SPENDING", "top", AMBER, "Highest expense category"),
        ]
        for col, (label, key, tone, note) in enumerate(metric_defs):
            card = self._card(metrics)
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 7, 0 if col == 3 else 7))
            ctk.CTkFrame(card, fg_color=tone, height=4, corner_radius=3).pack(anchor="w", padx=17, pady=(0, 10), fill="x")
            ctk.CTkLabel(card, text=label, text_color=MUTED,
                         font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=16)
            value = ctk.CTkLabel(card, text="—", text_color=TEXT,
                                 font=ctk.CTkFont(size=23, weight="bold"))
            value.pack(anchor="w", padx=16, pady=(8, 2))
            ctk.CTkLabel(card, text=note, text_color=MUTED,
                         font=ctk.CTkFont(size=10)).pack(anchor="w", padx=16, pady=(0, 14))
            self.metric_values[key] = value

        lower = ctk.CTkFrame(page, fg_color="transparent")
        lower.grid(row=3, column=0, sticky="nsew", pady=(15, 0))
        lower.grid_columnconfigure(0, weight=12)
        lower.grid_columnconfigure(1, weight=9)
        lower.grid_rowconfigure(0, weight=1)
        chart_card = self._card(lower)
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._section_heading(chart_card, "Expense distribution",
                              "Every category's share of your total spending")
        self.dash_chart_host = ctk.CTkFrame(chart_card, fg_color=CARD)
        self.dash_chart_host.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        right = ctk.CTkFrame(lower, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        cats_card = self._card(right)
        cats_card.grid(row=0, column=0, sticky="nsew", pady=(0, 7))
        self._section_heading(cats_card, "Category percentage breakdown",
                              "Exact percentage and amount for every category")
        self.category_host = ctk.CTkFrame(cats_card, fg_color="transparent")
        self.category_host.pack(fill="both", expand=True, padx=15, pady=(0, 13))
        recent_card = self._card(right)
        recent_card.grid(row=1, column=0, sticky="nsew", pady=(7, 0))
        self._section_heading(recent_card, "Recent transactions", "Your latest recorded expenses")
        self.recent_host = ctk.CTkFrame(recent_card, fg_color="transparent")
        self.recent_host.pack(fill="both", expand=True, padx=15, pady=(0, 12))

    def _draw_donut(self, host):
        for child in host.winfo_children():
            child.destroy()
        totals = self._category_totals()
        if not totals:
            ctk.CTkLabel(host, text="Add expenses to display your chart.",
                         text_color=MUTED).pack(expand=True)
            return
        fig = Figure(figsize=(6.1, 3.3), dpi=100, facecolor=CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(CARD)
        labels = list(totals.keys())
        values = list(totals.values())
        colors = [CATEGORY_COLORS.get(x, CYAN) for x in labels]
        wedges, _ = ax.pie(values, colors=colors, startangle=90,
                           wedgeprops={"width": 0.34, "edgecolor": CARD, "linewidth": 2})
        ax.text(0, 0.08, money(sum(values)), ha="center", va="center",
                color=TEXT, fontsize=13, fontweight="bold")
        ax.text(0, -0.15, "TOTAL EXPENSES", ha="center", va="center",
                color=MUTED, fontsize=7, fontweight="bold")
        legend_labels = [f"{k}   {money(v)}  •  {v/sum(values)*100:.2f}%"
                         for k, v in zip(labels, values)]
        leg = ax.legend(wedges, legend_labels, loc="center left",
                        bbox_to_anchor=(0.91, 0.5), frameon=False,
                        labelcolor=TEXT, fontsize=8, handlelength=1)
        for text in leg.get_texts():
            text.set_color(TEXT)
        ax.set(aspect="equal")
        fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
        canvas = FigureCanvasTkAgg(fig, master=host)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def refresh_dashboard(self):
        total = self._total()
        months = {x["date"][:7] for x in self.expenses}
        top = max(self._category_totals().items(), key=lambda x: x[1], default=(None, 0))[0]
        self.metric_values["total"].configure(text=money(total))
        self.metric_values["average"].configure(text=money(total / len(months) if months else 0))
        self.metric_values["count"].configure(text=str(len(self.expenses)))
        self.metric_values["top"].configure(text=top or "—")
        self._draw_donut(self.dash_chart_host)

        for child in self.category_host.winfo_children():
            child.destroy()
        totals = self._category_totals()
        if not totals:
            ctk.CTkLabel(self.category_host, text="No expenses recorded yet.",
                         text_color=MUTED).pack(anchor="w")
        else:
            for category, amount in sorted(totals.items(), key=lambda x: x[1], reverse=True):
                percent = amount / total * 100 if total else 0
                row = ctk.CTkFrame(self.category_host, fg_color="transparent")
                row.pack(fill="x", pady=5)
                left = ctk.CTkFrame(row, fg_color="transparent")
                left.pack(side="left", fill="x", expand=True)
                ctk.CTkLabel(left, text=f"●  {category}", text_color=CATEGORY_COLORS[category],
                             font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
                bar = ctk.CTkProgressBar(left, height=7, progress_color=CATEGORY_COLORS[category],
                                         fg_color=CARD_ALT)
                bar.pack(fill="x", pady=(5, 0))
                bar.set(percent / 100)
                right = ctk.CTkFrame(row, fg_color="transparent")
                right.pack(side="right", padx=(10, 0))
                ctk.CTkLabel(right, text=f"{percent:.2f}%", text_color=TEXT,
                             font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="e")
                ctk.CTkLabel(right, text=money(amount), text_color=MUTED,
                             font=ctk.CTkFont(size=10)).pack(anchor="e")

        for child in self.recent_host.winfo_children():
            child.destroy()
        recent = sorted(self.expenses, key=lambda x: x["date"], reverse=True)[:4]
        if not recent:
            ctk.CTkLabel(self.recent_host, text="No recent transactions.",
                         text_color=MUTED).pack(anchor="w")
        for item in recent:
            row = ctk.CTkFrame(self.recent_host, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=f"{item['category']}  •  {item['date']}",
                         text_color=TEXT, font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(row, text=item.get("description", "") or "No description",
                         text_color=MUTED, font=ctk.CTkFont(size=10)).pack(side="left")
            ctk.CTkLabel(row, text=money(item["amount"]), text_color=TEXT,
                         font=ctk.CTkFont(size=11, weight="bold")).pack(side="right")

    # ---------------------------- ADD EXPENSE -------------------------------
    def _build_add_expense(self):
        page = self.pages["Add Expense"]
        ctk.CTkLabel(page, text="Add a new expense", text_color=TEXT,
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", pady=(2, 4))
        ctk.CTkLabel(page, text="Record a purchase and keep your expense report up to date.",
                     text_color=MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 18))
        card = self._card(page)
        card.pack(fill="x", padx=(0, 100), pady=2)
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=24)
        form.grid_columnconfigure((0, 1), weight=1)
        self.exp_date = self._form_field(form, "DATE", 0, 0, default=date.today().isoformat())
        self.exp_category = self._form_field(form, "CATEGORY", 0, 1, values=CATEGORIES)
        self.exp_amount = self._form_field(form, "AMOUNT (₹)", 1, 0, placeholder="e.g. 450.00")
        self.exp_description = self._form_field(form, "DESCRIPTION", 1, 1, placeholder="What was this expense for?")
        ctk.CTkLabel(form, text="Smart suggestions: Uber / Ola → Travel  •  Lunch / Zomato → Food  •  Rent / Electricity → Bills",
                     text_color=MUTED, font=ctk.CTkFont(size=11)).grid(row=2, column=0, columnspan=2, sticky="w", pady=(13, 0))
        buttons = ctk.CTkFrame(form, fg_color="transparent")
        buttons.grid(row=3, column=0, columnspan=2, sticky="w", pady=(19, 0))
        ctk.CTkButton(buttons, text="Save expense  →", fg_color=BLUE, hover_color="#5578EC",
                      height=40, command=self.add_expense).pack(side="left", padx=(0, 9))
        ctk.CTkButton(buttons, text="Clear form", fg_color=CARD_ALT, hover_color=BORDER,
                      height=40, command=self.clear_expense_form).pack(side="left")

    def _form_field(self, parent, label, row, col, default="", placeholder="", values=None, width=300):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="ew", padx=(0, 12), pady=9)
        ctk.CTkLabel(frame, text=label, text_color=MUTED,
                     font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(0, 6))
        if values is not None:
            widget = ctk.CTkComboBox(frame, values=values, width=width, height=40,
                                     fg_color="#0E192B", border_color=BORDER,
                                     button_color=CARD_ALT, text_color=TEXT)
            if values:
                widget.set(values[0])
        else:
            widget = ctk.CTkEntry(frame, width=width, height=40, fg_color="#0E192B",
                                  border_color=BORDER, text_color=TEXT,
                                  placeholder_text=placeholder)
        if default:
            widget.insert(0, default) if isinstance(widget, ctk.CTkEntry) else widget.set(default)
        widget.pack(fill="x")
        return widget

    def add_expense(self):
        try:
            amount = float(self.exp_amount.get().strip())
            if amount <= 0:
                raise ValueError
            datetime.strptime(self.exp_date.get().strip(), "%Y-%m-%d")
            category = self.exp_category.get().strip()
            if category not in CATEGORIES:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid expense", "Enter a valid date, category and positive amount.")
            return
        self.expenses.append({
            "id": str(datetime.now().timestamp()),
            "date": self.exp_date.get().strip(),
            "category": category,
            "amount": round(amount, 2),
            "description": self.exp_description.get().strip()
        })
        self._save_data()
        self.clear_expense_form()
        self._toast("Expense saved successfully.")
        self.refresh_dashboard()

    def clear_expense_form(self):
        self.exp_date.delete(0, "end")
        self.exp_date.insert(0, date.today().isoformat())
        self.exp_amount.delete(0, "end")
        self.exp_description.delete(0, "end")
        self.exp_category.set(CATEGORIES[0])

    # ---------------------------- TRANSACTIONS ------------------------------
    def _build_transactions(self):
        page = self.pages["Transactions"]
        ctk.CTkLabel(page, text="Transaction history", text_color=TEXT,
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(page, text="Search, filter, sort and remove individual expense records.",
                     text_color=MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(3, 15))
        toolbar = self._card(page)
        toolbar.pack(fill="x", pady=(0, 12))
        tools = ctk.CTkFrame(toolbar, fg_color="transparent")
        tools.pack(fill="x", padx=12, pady=12)
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_transactions())
        self.search_entry = ctk.CTkEntry(tools, textvariable=self.search_var, height=39,
                                          placeholder_text="Search description, category or date...",
                                          fg_color="#0E192B", border_color=BORDER)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.filter_menu = ctk.CTkOptionMenu(tools, values=["All categories"] + CATEGORIES,
                                             height=39, fg_color=CARD_ALT, button_color=BLUE,
                                             command=lambda _: self.refresh_transactions())
        self.filter_menu.pack(side="left", padx=5)
        self.sort_menu = ctk.CTkOptionMenu(tools, values=["Newest first", "Oldest first", "Highest amount", "Lowest amount"],
                                           height=39, fg_color=CARD_ALT, button_color=BLUE,
                                           command=lambda _: self.refresh_transactions())
        self.sort_menu.pack(side="left", padx=(5, 0))
        table_card = self._card(page)
        table_card.pack(fill="both", expand=True)
        self.table_frame = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, padx=8, pady=8)
        header = ctk.CTkFrame(self.table_frame, fg_color=CARD_ALT, corner_radius=8)
        header.pack(fill="x", pady=(0, 6))
        for text, width in [("SELECT", 55), ("DATE", 130), ("CATEGORY", 145), ("AMOUNT", 145), ("DESCRIPTION", 300)]:
            ctk.CTkLabel(header, text=text, width=width, anchor="w", text_color=MUTED,
                         font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=8, pady=11)
        self.transaction_rows = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        self.transaction_rows.pack(fill="both", expand=True)
        footer = ctk.CTkFrame(table_card, fg_color="transparent")
        footer.pack(fill="x", padx=14, pady=(0, 12))
        self.transaction_count_label = ctk.CTkLabel(footer, text="0 transactions", text_color=MUTED)
        self.transaction_count_label.pack(side="left")
        ctk.CTkButton(footer, text="Delete selected", fg_color="#713442", hover_color="#A43D53",
                      height=34, command=self.delete_selected).pack(side="right")

    def refresh_transactions(self):
        if not hasattr(self, "transaction_rows"):
            return
        for child in self.transaction_rows.winfo_children():
            child.destroy()
        query = self.search_var.get().lower().strip()
        category = self.filter_menu.get()
        sort = self.sort_menu.get()
        items = [x for x in self.expenses
                 if query in (x["date"] + " " + x["category"] + " " + x.get("description", "")).lower()
                 and (category == "All categories" or x["category"] == category)]
        if sort == "Oldest first":
            items.sort(key=lambda x: x["date"])
        elif sort == "Highest amount":
            items.sort(key=lambda x: x["amount"], reverse=True)
        elif sort == "Lowest amount":
            items.sort(key=lambda x: x["amount"])
        else:
            items.sort(key=lambda x: x["date"], reverse=True)

        self.transaction_checks = []
        for item in items:
            row = ctk.CTkFrame(self.transaction_rows, fg_color=CARD, corner_radius=8)
            row.pack(fill="x", pady=3)
            var = ctk.BooleanVar(value=False)
            self.transaction_checks.append((var, item["id"]))
            ctk.CTkCheckBox(row, text="", variable=var, width=40, checkbox_width=17,
                            checkbox_height=17, fg_color=BLUE).pack(side="left", padx=(12, 8), pady=12)
            ctk.CTkLabel(row, text=item["date"], width=130, anchor="w",
                         text_color=TEXT, font=ctk.CTkFont(size=11)).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=item["category"], width=145, anchor="w",
                         text_color=CATEGORY_COLORS.get(item["category"], TEXT),
                         font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=money(item["amount"]), width=145, anchor="w",
                         text_color=TEXT, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=item.get("description", "") or "—", anchor="w",
                         text_color=MUTED, font=ctk.CTkFont(size=11)).pack(side="left", padx=8, fill="x", expand=True)
        if not items:
            ctk.CTkLabel(self.transaction_rows, text="No matching transactions.",
                         text_color=MUTED).pack(pady=30)
        self.transaction_count_label.configure(text=f"Showing {len(items)} of {len(self.expenses)} transaction(s)")

    def delete_selected(self):
        selected = [item_id for var, item_id in getattr(self, "transaction_checks", []) if var.get()]
        if not selected:
            messagebox.showinfo("Nothing selected", "Select one or more transactions first.")
            return
        if not messagebox.askyesno("Confirm deletion", f"Delete {len(selected)} selected transaction(s)?"):
            return
        selected = set(selected)
        self.expenses = [x for x in self.expenses if x["id"] not in selected]
        self._save_data()
        self.refresh_transactions()
        self.refresh_dashboard()
        self._toast("Selected transactions deleted.")

    # ---------------------------- ANALYTICS ---------------------------------
    def _build_analytics(self):
        page = self.pages["Analytics"]
        ctk.CTkLabel(page, text="Spending analytics", text_color=TEXT,
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(page, text="Clear visual insights into where your money goes.",
                     text_color=MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(3, 15))
        total_card = self._card(page)
        total_card.pack(fill="x", pady=(0, 13))
        self.analytics_total = ctk.CTkLabel(total_card, text="Total recorded spending: ₹0.00",
                                            text_color=TEXT, font=ctk.CTkFont(size=17, weight="bold"))
        self.analytics_total.pack(anchor="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(total_card, text="Percentage = category amount ÷ total expenses × 100.",
                     text_color=MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w", padx=18, pady=(0, 14))
        content = ctk.CTkFrame(page, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure((0, 1), weight=1)
        content.grid_rowconfigure(0, weight=1)
        chart_card = self._card(content)
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self._section_heading(chart_card, "Spending by category", "Donut chart with percentages and total")
        self.analytics_chart_host = ctk.CTkFrame(chart_card, fg_color=CARD)
        self.analytics_chart_host.pack(fill="both", expand=True, padx=7, pady=(0, 7))
        report_card = self._card(content)
        report_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        self._section_heading(report_card, "Detailed category report", "Ranked by amount spent, highest first")
        self.analytics_report_host = ctk.CTkScrollableFrame(report_card, fg_color="transparent")
        self.analytics_report_host.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def refresh_analytics(self):
        total = self._total()
        self.analytics_total.configure(text=f"Total recorded spending: {money(total)}")
        self._draw_donut(self.analytics_chart_host)
        for child in self.analytics_report_host.winfo_children():
            child.destroy()
        totals = self._category_totals()
        if not totals:
            ctk.CTkLabel(self.analytics_report_host, text="Add expenses to see the report.",
                         text_color=MUTED).pack(pady=25)
            return
        for index, (category, amount) in enumerate(sorted(totals.items(), key=lambda x: x[1], reverse=True), 1):
            percent = amount / total * 100 if total else 0
            card = ctk.CTkFrame(self.analytics_report_host, fg_color=CARD_ALT, corner_radius=10)
            card.pack(fill="x", pady=5)
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(10, 2))
            ctk.CTkLabel(top, text=f"{index:02d}   ●  {category}",
                         text_color=CATEGORY_COLORS[category],
                         font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            ctk.CTkLabel(top, text=f"{percent:.2f}%", text_color=BLUE,
                         font=ctk.CTkFont(size=14, weight="bold")).pack(side="right")
            ctk.CTkLabel(card, text=money(amount), text_color=TEXT,
                         font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=12)
            ctk.CTkLabel(card, text=f"{percent:.2f}% of all recorded expenses",
                         text_color=MUTED, font=ctk.CTkFont(size=10)).pack(anchor="w", padx=12)
            bar = ctk.CTkProgressBar(card, height=7, progress_color=CATEGORY_COLORS[category],
                                     fg_color=CARD)
            bar.pack(fill="x", padx=12, pady=(7, 12))
            bar.set(percent / 100)

    # ---------------------------- BILL GENERATOR ---------------------------
    def _build_bill_page(self):
        page = self.pages["Generate Bill"]
        ctk.CTkLabel(page, text="Bill & receipt generator", text_color=TEXT,
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(page, text="Create a clean, itemised bill and print it or save it as a PDF.",
                     text_color=MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(3, 14))
        body = ctk.CTkFrame(page, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=11)
        body.grid_columnconfigure(1, weight=9)
        body.grid_rowconfigure(0, weight=1)
        form_card = self._card(body)
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        preview_card = self._card(body)
        preview_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        ctk.CTkLabel(form_card, text="Bill details", text_color=TEXT,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=17, pady=(16, 8))
        fields = ctk.CTkFrame(form_card, fg_color="transparent")
        fields.pack(fill="x", padx=16)
        fields.grid_columnconfigure((0, 1), weight=1)
        self.bill_business = self._form_field(fields, "BUSINESS / STORE NAME", 0, 0, placeholder="e.g. NOVA Stores", width=220)
        self.bill_number = self._form_field(fields, "BILL / INVOICE NUMBER", 0, 1, default=f"INV-{datetime.now():%H%M%S}", width=220)
        self.bill_customer = self._form_field(fields, "CUSTOMER NAME", 1, 0, placeholder="Customer name", width=220)
        self.bill_date = self._form_field(fields, "BILL DATE", 1, 1, default=date.today().isoformat(), width=220)
        self.bill_payment = self._form_field(fields, "PAYMENT METHOD", 2, 0,
                                             values=["Cash", "UPI", "Debit / Credit Card", "Net Banking"], width=220)
        self.bill_tax = self._form_field(fields, "TAX / GST (%)", 2, 1, default="0", width=220)

        item_header = ctk.CTkFrame(form_card, fg_color="transparent")
        item_header.pack(fill="x", padx=17, pady=(17, 6))
        ctk.CTkLabel(item_header, text="Items / services", text_color=TEXT,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkButton(item_header, text="＋ Add item", width=100, height=30,
                      fg_color=CARD_ALT, hover_color=BORDER, command=self.add_bill_line).pack(side="right")
        self.bill_lines_host = ctk.CTkScrollableFrame(form_card, height=150, fg_color="transparent")
        self.bill_lines_host.pack(fill="both", expand=True, padx=12)
        actions = ctk.CTkFrame(form_card, fg_color="transparent")
        actions.pack(fill="x", padx=16, pady=13)
        ctk.CTkButton(actions, text="Generate bill preview", fg_color=BLUE, hover_color="#5578EC",
                      command=self.generate_bill).pack(side="left", padx=(0, 7))
        ctk.CTkButton(actions, text="Reset", fg_color=CARD_ALT, hover_color=BORDER,
                      command=self.reset_bill).pack(side="left")
        ctk.CTkLabel(form_card, text="Creates a sample invoice. Verify seller, customer, item and tax details before real use.",
                     text_color=MUTED, wraplength=480, justify="left",
                     font=ctk.CTkFont(size=10)).pack(anchor="w", padx=17, pady=(0, 12))

        ctk.CTkLabel(preview_card, text="Bill preview", text_color=TEXT,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=17, pady=(16, 2))
        ctk.CTkLabel(preview_card, text="Your itemised bill appears here.",
                     text_color=MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w", padx=17, pady=(0, 10))
        self.bill_preview_host = ctk.CTkScrollableFrame(preview_card, fg_color="#F8FAFC",
                                                       corner_radius=10)
        self.bill_preview_host.pack(fill="both", expand=True, padx=13, pady=(0, 10))
        self._preview_placeholder()
        preview_actions = ctk.CTkFrame(preview_card, fg_color="transparent")
        preview_actions.pack(fill="x", padx=13, pady=(0, 13))
        self.print_bill_btn = ctk.CTkButton(preview_actions, text="Print / Save as PDF",
                                            fg_color=BLUE, hover_color="#5578EC",
                                            command=self.print_bill, state="disabled")
        self.print_bill_btn.pack(side="left", padx=(0, 7))
        self.save_bill_btn = ctk.CTkButton(preview_actions, text="Save to history",
                                           fg_color=CARD_ALT, hover_color=BORDER,
                                           command=self.save_bill, state="disabled")
        self.save_bill_btn.pack(side="left")

        history_card = self._card(page)
        history_card.pack(fill="x", pady=(13, 0))
        ctk.CTkLabel(history_card, text="Saved bill history", text_color=TEXT,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(12, 2))
        self.bill_history_host = ctk.CTkFrame(history_card, fg_color="transparent")
        self.bill_history_host.pack(fill="x", padx=15, pady=(3, 12))
        self.add_bill_line()

    def add_bill_line(self):
        row = ctk.CTkFrame(self.bill_lines_host, fg_color=CARD_ALT, corner_radius=8)
        row.pack(fill="x", pady=3)
        desc = ctk.CTkEntry(row, placeholder_text="Item / service", height=34,
                            fg_color="#0E192B", border_color=BORDER)
        desc.pack(side="left", fill="x", expand=True, padx=(6, 4), pady=6)
        qty = ctk.CTkEntry(row, width=55, height=34, fg_color="#0E192B",
                           border_color=BORDER, placeholder_text="Qty")
        qty.insert(0, "1")
        qty.pack(side="left", padx=4, pady=6)
        price = ctk.CTkEntry(row, width=88, height=34, fg_color="#0E192B",
                             border_color=BORDER, placeholder_text="Unit ₹")
        price.pack(side="left", padx=4, pady=6)
        remove = ctk.CTkButton(row, text="×", width=30, height=32, fg_color="#713442",
                               hover_color="#A43D53", command=lambda r=row: self.remove_bill_line(r))
        remove.pack(side="left", padx=(3, 6), pady=6)
        self.bill_item_rows.append((row, desc, qty, price))

    def remove_bill_line(self, row):
        if len(self.bill_item_rows) <= 1:
            messagebox.showinfo("Bill items", "At least one item row is required.")
            return
        for entry in list(self.bill_item_rows):
            if entry[0] is row:
                self.bill_item_rows.remove(entry)
                break
        row.destroy()

    def _bill_calculation(self):
        items = []
        for _, desc, qty, price in self.bill_item_rows:
            description = desc.get().strip()
            if not description:
                continue
            try:
                q, p = int(qty.get()), float(price.get())
                if q <= 0 or p < 0:
                    raise ValueError
            except ValueError:
                raise ValueError("Enter a valid positive quantity and non-negative unit price for each item.")
            items.append({"description": description, "quantity": q, "price": p,
                          "amount": q * p})
        if not items:
            raise ValueError("Add at least one item with a description and price.")
        try:
            tax_rate = float(self.bill_tax.get() or 0)
            if not 0 <= tax_rate <= 100:
                raise ValueError
        except ValueError:
            raise ValueError("Tax / GST must be between 0 and 100.")
        subtotal = sum(x["amount"] for x in items)
        tax = subtotal * tax_rate / 100
        return items, subtotal, tax_rate, tax, subtotal + tax

    def generate_bill(self):
        business = self.bill_business.get().strip()
        number = self.bill_number.get().strip()
        customer = self.bill_customer.get().strip()
        bill_date = self.bill_date.get().strip()
        if not all([business, number, customer, bill_date]):
            messagebox.showerror("Missing details", "Complete business name, bill number, customer and date.")
            return
        try:
            datetime.strptime(bill_date, "%Y-%m-%d")
            items, subtotal, rate, tax, total = self._bill_calculation()
        except ValueError as error:
            messagebox.showerror("Invalid bill", str(error))
            return
        self.current_bill = {
            "id": str(datetime.now().timestamp()), "business": business, "number": number,
            "customer": customer, "date": bill_date, "payment": self.bill_payment.get(),
            "items": items, "subtotal": subtotal, "tax_rate": rate, "tax": tax, "total": total
        }
        self._render_bill_preview(self.current_bill)
        self.print_bill_btn.configure(state="normal")
        self.save_bill_btn.configure(state="normal")
        self._toast("Bill preview generated successfully.")

    def _preview_placeholder(self):
        for child in self.bill_preview_host.winfo_children():
            child.destroy()
        ctk.CTkLabel(self.bill_preview_host, text="YOUR BILL WILL APPEAR HERE",
                     text_color="#526078", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(45, 5))
        ctk.CTkLabel(self.bill_preview_host, text="Complete the details and generate a preview.",
                     text_color="#526078", font=ctk.CTkFont(size=10)).pack(pady=(0, 40))

    def _render_bill_preview(self, bill):
        for child in self.bill_preview_host.winfo_children():
            child.destroy()
        host = self.bill_preview_host
        ctk.CTkLabel(host, text=bill["business"], text_color="#172033",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=13, pady=(13, 0))
        ctk.CTkLabel(host, text=f"INVOICE  •  {bill['number']}",
                     text_color="#526078", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=13)
        ctk.CTkFrame(host, height=1, fg_color="#DCE3ED").pack(fill="x", padx=12, pady=9)
        ctk.CTkLabel(host, text=f"Bill to: {bill['customer']}     |     Date: {bill['date']}",
                     text_color="#172033", font=ctk.CTkFont(size=10)).pack(anchor="w", padx=13, pady=4)
        header = ctk.CTkFrame(host, fg_color="#E8EDF5", corner_radius=5)
        header.pack(fill="x", padx=9, pady=(8, 3))
        for label, width in [("ITEM", 145), ("QTY", 38), ("UNIT", 75), ("AMOUNT", 90)]:
            ctk.CTkLabel(header, text=label, width=width, text_color="#536078",
                         font=ctk.CTkFont(size=9, weight="bold")).pack(side="left", padx=3, pady=7)
        for item in bill["items"]:
            line = ctk.CTkFrame(host, fg_color="transparent")
            line.pack(fill="x", padx=10)
            vals = [item["description"], str(item["quantity"]), money(item["price"]), money(item["amount"])]
            widths = [145, 38, 75, 90]
            for val, width in zip(vals, widths):
                ctk.CTkLabel(line, text=val, width=width, anchor="w", text_color="#172033",
                             font=ctk.CTkFont(size=9)).pack(side="left", padx=3, pady=5)
        ctk.CTkFrame(host, height=1, fg_color="#DCE3ED").pack(fill="x", padx=12, pady=8)
        for label, value, bold in [
            ("Subtotal", money(bill["subtotal"]), False),
            (f"Tax / GST ({bill['tax_rate']:.2f}%)", money(bill["tax"]), False),
            ("GRAND TOTAL", money(bill["total"]), True)
        ]:
            row = ctk.CTkFrame(host, fg_color="transparent")
            row.pack(fill="x", padx=13, pady=3)
            font = ctk.CTkFont(size=12 if bold else 10, weight="bold" if bold else "normal")
            ctk.CTkLabel(row, text=label, text_color="#172033", font=font).pack(side="left")
            ctk.CTkLabel(row, text=value, text_color="#172033", font=font).pack(side="right")
        ctk.CTkLabel(host, text=f"Payment method: {bill['payment']}",
                     text_color="#526078", font=ctk.CTkFont(size=10)).pack(anchor="w", padx=13, pady=(9, 4))
        ctk.CTkLabel(host, text="Thank you for your business.",
                     text_color="#526078", font=ctk.CTkFont(size=10)).pack(pady=(12, 15))

    def save_bill(self):
        if not self.current_bill:
            return
        if any(x["number"] == self.current_bill["number"] for x in self.bills):
            messagebox.showwarning("Duplicate bill number", "That bill number is already saved. Use a unique number.")
            return
        self.bills.insert(0, self.current_bill.copy())
        self._save_data()
        self.refresh_bill_history()
        self.save_bill_btn.configure(state="disabled")
        self._toast("Bill saved to history.")

    def refresh_bill_history(self):
        if not hasattr(self, "bill_history_host"):
            return
        for child in self.bill_history_host.winfo_children():
            child.destroy()
        if not self.bills:
            ctk.CTkLabel(self.bill_history_host, text="No saved bills yet.",
                         text_color=MUTED).pack(anchor="w")
            return
        for bill in self.bills[:5]:
            row = ctk.CTkFrame(self.bill_history_host, fg_color=CARD_ALT, corner_radius=8)
            row.pack(fill="x", pady=3)
            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(left, text=f"{bill['number']}  •  {bill['business']}",
                         text_color=TEXT, font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(left, text=f"{bill['date']}  •  Customer: {bill['customer']}",
                         text_color=MUTED, font=ctk.CTkFont(size=10)).pack(anchor="w")
            ctk.CTkLabel(row, text=money(bill["total"]), text_color=GREEN,
                         font=ctk.CTkFont(size=12, weight="bold")).pack(side="right", padx=12)

    def _bill_html(self, bill):
        # Escape all user-entered values before placing them into the printable document.
        import html
        esc = html.escape
        rows = "".join(
            f"<tr><td>{esc(x['description'])}</td><td>{x['quantity']}</td>"
            f"<td>{money(x['price'])}</td><td>{money(x['amount'])}</td></tr>"
            for x in bill["items"]
        )
        return f"""<!doctype html><html><head><meta charset='utf-8'><title>{esc(bill['number'])}</title>
<style>body{{font:14px Arial;color:#172033;padding:42px;max-width:850px;margin:auto}}
header{{display:flex;justify-content:space-between}}h1{{font-size:26px}}small{{color:#64748b}}
table{{width:100%;border-collapse:collapse;margin-top:28px}}th,td{{text-align:left;padding:12px;border-bottom:1px solid #ddd}}
th{{background:#edf1f7}}.totals{{margin:25px 0 0 auto;width:290px}}.totals div{{display:flex;justify-content:space-between;padding:7px 0}}
.grand{{font-size:20px;font-weight:bold;border-top:2px solid #222;margin-top:8px}}.thanks{{text-align:center;margin-top:60px;color:#64748b}}
@media print{{body{{padding:15px}}}}</style></head><body>
<header><div><h1>{esc(bill['business'])}</h1><small>Payment receipt / invoice</small></div>
<div><b>INVOICE</b><p>{esc(bill['number'])}</p></div></header><hr>
<p><b>Bill to:</b> {esc(bill['customer'])}</p><p><b>Date:</b> {esc(bill['date'])}</p>
<table><thead><tr><th>Item / service</th><th>Qty</th><th>Unit price</th><th>Amount</th></tr></thead><tbody>{rows}</tbody></table>
<div class='totals'><div><span>Subtotal</span><b>{money(bill['subtotal'])}</b></div>
<div><span>Tax / GST ({bill['tax_rate']:.2f}%)</span><b>{money(bill['tax'])}</b></div>
<div class='grand'><span>Grand total</span><span>{money(bill['total'])}</span></div></div>
<p><b>Payment method:</b> {esc(bill['payment'])}</p><p class='thanks'>Thank you for your business.</p>
<script>window.onload=()=>window.print();</script></body></html>"""

    def print_bill(self):
        if not self.current_bill:
            messagebox.showinfo("Generate bill", "Generate a bill preview first.")
            return
        path = Path(__file__).with_name(f"{self.current_bill['number'].replace('/', '-')}.html")
        path.write_text(self._bill_html(self.current_bill), encoding="utf-8")
        webbrowser.open(path.resolve().as_uri())
        self._toast("Printable bill opened in your browser. Choose Save as PDF in Print.")

    def reset_bill(self):
        self.current_bill = None
        self.bill_business.delete(0, "end")
        self.bill_number.delete(0, "end")
        self.bill_number.insert(0, f"INV-{datetime.now():%H%M%S}")
        self.bill_customer.delete(0, "end")
        self.bill_date.delete(0, "end")
        self.bill_date.insert(0, date.today().isoformat())
        self.bill_payment.set("Cash")
        self.bill_tax.delete(0, "end")
        self.bill_tax.insert(0, "0")
        for row, *_ in self.bill_item_rows:
            row.destroy()
        self.bill_item_rows.clear()
        self.add_bill_line()
        self._preview_placeholder()
        self.print_bill_btn.configure(state="disabled")
        self.save_bill_btn.configure(state="disabled")

    # ---------------------------- SETTINGS ----------------------------------
    def _build_settings(self):
        page = self.pages["Settings & Data"]
        ctk.CTkLabel(page, text="Settings & data management", text_color=TEXT,
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(page, text="Export your records, check storage, or clear application data.",
                     text_color=MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(3, 15))
        self.storage_label = ctk.CTkLabel(self._card(page), text="", text_color=MUTED,
                                          font=ctk.CTkFont(size=12))
        self.storage_label.master.pack(fill="x", pady=(0, 10))
        self.storage_label.pack(anchor="w", padx=18, pady=18)
        self._settings_action(page, "Export expense report",
                              "Download your transaction history as a CSV spreadsheet.",
                              "Export expenses to CSV", self.export_expenses)
        self._settings_action(page, "Export saved bills",
                              "Download your saved bill history as a CSV spreadsheet.",
                              "Export bill history", self.export_bills, secondary=True)
        self._settings_action(page, "Danger zone",
                              "Permanently remove all expense records and saved bills. This cannot be undone.",
                              "Delete all application data", self.clear_all, danger=True)

    def _settings_action(self, parent, title, description, button_text, command,
                         secondary=False, danger=False):
        card = self._card(parent)
        card.pack(fill="x", pady=6)
        ctk.CTkLabel(card, text=title, text_color=RED if danger else TEXT,
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=17, pady=(13, 2))
        ctk.CTkLabel(card, text=description, text_color=MUTED,
                     font=ctk.CTkFont(size=11), wraplength=800).pack(anchor="w", padx=17)
        color = "#713442" if danger else (CARD_ALT if secondary else BLUE)
        hover = "#A43D53" if danger else ("#2B405D" if secondary else "#5578EC")
        ctk.CTkButton(card, text=button_text, fg_color=color, hover_color=hover,
                      command=command, height=36).pack(anchor="w", padx=17, pady=12)

    def refresh_storage_info(self):
        self.storage_label.configure(
            text=f"LOCAL BROWSER-STYLE STORAGE  •  {len(self.expenses)} expense record(s)  •  {len(self.bills)} saved bill(s)\n"
                 f"Data file: {DATA_FILE}"
        )

    def export_expenses(self):
        if not self.expenses:
            messagebox.showinfo("Export", "There are no expenses to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            initialfile="nova_expenses.csv",
                                            filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Category", "Amount INR", "Description"])
            for x in sorted(self.expenses, key=lambda z: z["date"], reverse=True):
                writer.writerow([x["date"], x["category"], x["amount"], x.get("description", "")])
        self._toast("Expense CSV exported.")

    def export_bills(self):
        if not self.bills:
            messagebox.showinfo("Export", "There are no saved bills to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            initialfile="nova_bill_history.csv",
                                            filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["Bill Number", "Date", "Business", "Customer",
                             "Subtotal", "Tax", "Total", "Payment"])
            for x in self.bills:
                writer.writerow([x["number"], x["date"], x["business"], x["customer"],
                                 x["subtotal"], x["tax"], x["total"], x["payment"]])
        self._toast("Bill history CSV exported.")

    def clear_all(self):
        if not messagebox.askyesno("Delete all data",
                                   "Permanently delete all expenses and saved bills? This cannot be undone."):
            return
        self.expenses = []
        self.bills = []
        self.current_bill = None
        self._save_data()
        self.refresh_dashboard()
        self.refresh_transactions()
        self.refresh_analytics()
        self.refresh_bill_history()
        self.refresh_storage_info()
        self._toast("All application data deleted.")

    def _on_close(self):
        self._save_data()
        self.destroy()


if __name__ == "__main__":
    app = NovaApp()
    app.mainloop()
