from tkinter import END, Button, Entry, Label, Menu, OptionMenu, StringVar, Text, Tk

from client import fetch_all_data
from configuration.logger_setup import logger
from tkcalendar import Calendar

FIELDS = [
    "call_recording",
    "utm_campaign",
    "utm_source",
    "utm_term",
    "utm_content",
    "call_duration",
    "call_date",
    "employee",
    "employee_ext_number",
    "caller_number",
    "unique_call",
    "unique_target_call",
    "number_pool_name",
    "utm_medium",
    "substitution_type",
    "call_id",
]
CONDITIONS = [
    "равно",
    "не равно",
    "содержит",
    "не содержит",
    "начинается с",
    "заканчивается на",
    "больше чем",
    "меньше чем",
    "больше или равно",
    "меньше или равно",
]
LOGICAL_OPERATORS = ["И", "ИЛИ"]


def show_calendar(entry):
    calendar_window = Tk()
    calendar_window.title("Выберите дату")
    cal = Calendar(calendar_window, selectmode="day", date_pattern="yyyy-mm-dd")
    cal.pack(pady=20)

    def set_date():
        selected_date = cal.get_date() + " 00:00:00"
        entry.delete(0, END)
        entry.insert(0, selected_date)
        calendar_window.destroy()

    Button(calendar_window, text="Выбрать", command=set_date).pack()
    calendar_window.mainloop()


def add_context_menu(entry_widget, root):
    context_menu = Menu(entry_widget, tearoff=0)
    context_menu.add_command(
        label="Копировать", command=lambda: root.clipboard_append(entry_widget.get())
    )
    context_menu.add_command(
        label="Вставить", command=lambda: entry_widget.insert(END, root.clipboard_get())
    )

    entry_widget.bind(
        "<Button-3>", lambda event: context_menu.post(event.x_root, event.y_root)
    )


def build_gui():
    root = Tk()
    root.title("Data Fetcher with Filters")

    field_vars, condition_vars, value_entries, operator_vars = [], [], [], []
    for i in range(5):
        Label(root, text=f"Фильтр {i + 1}").pack()
        field_var = StringVar(root)
        field_var.set(FIELDS[0])
        field_vars.append(field_var)
        OptionMenu(root, field_var, *FIELDS).pack()

        condition_var = StringVar(root)
        condition_var.set(CONDITIONS[0])
        condition_vars.append(condition_var)
        OptionMenu(root, condition_var, *CONDITIONS).pack()

        value_entry = Entry(root)
        value_entries.append(value_entry)
        value_entry.pack()
        add_context_menu(value_entry, root)

        field_var.trace(
            "w",
            lambda *args, entry=value_entry, field=field_var: (
                show_calendar(entry) if field.get() == "call_date" else None
            ),
        )

        if i < 4:
            operator_var = StringVar(root)
            operator_var.set(LOGICAL_OPERATORS[0])
            operator_vars.append(operator_var)
            OptionMenu(root, operator_var, *LOGICAL_OPERATORS).pack()

    result_text = Text(root, wrap="word", width=80, height=20)
    result_text.pack(pady=10)
    Button(
        root,
        text="Получить данные",
        command=lambda: fetch_all_data(
            result_text, field_vars, condition_vars, value_entries, operator_vars
        ),
    ).pack(pady=10)

    root.mainloop()
