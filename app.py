"""Inventory Management System GUI.

Requirements:
    - Python 3.10+
    - mysql-connector-python
    - A local database.py exposing get_connection() and test_connection()

The application uses the existing `products` and `inventory_transactions` tables.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from database import get_connection, test_connection


APP_TITLE = "Inventory Management System"
DEFAULT_WAREHOUSE = "Jaipur Warehouse"
DEFAULT_REORDER_LEVEL = 10
DEFAULT_TARGET_STOCK = 50


class InventoryApp:
    """Manage products and record stock movements in MySQL."""

    PRODUCT_FIELDS = [
        ("Product Name", "ProductName"),
        ("SKU", "SKU"),
        ("Category", "Category"),
        ("Brand", "Brand"),
        ("Supplier", "SupplierName"),
        ("Warehouse", "Warehouse"),
        ("Current Stock", "Stock"),
        ("Selling Price", "Price"),
        ("Cost Price", "CostPrice"),
        ("Reorder Level", "ReorderLevel"),
        ("Target Stock", "TargetStock"),
    ]

    TABLE_COLUMNS = (
        "ProductID",
        "ProductName",
        "SKU",
        "Category",
        "Warehouse",
        "Stock",
        "Price",
        "CostPrice",
        "ReorderLevel",
        "Status",
    )

    TABLE_WIDTHS = (70, 155, 100, 110, 145, 85, 100, 100, 100, 135)

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.selected_id = None
        self.variables = {}

        self.root.title(APP_TITLE)
        self.root.geometry("1240x760")
        self.root.minsize(1050, 650)

        self._configure_style()
        self._build_header()
        self._build_product_form()
        self._build_stock_movement_form()
        self._build_product_table()
        self.load_products(show_errors=False)

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------
    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("AppTitle.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=27, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 9, "bold"))

    def _build_header(self) -> None:
        header = ttk.Frame(self.root, padding=(14, 12))
        header.pack(fill="x")

        ttk.Label(header, text=APP_TITLE, style="AppTitle.TLabel").pack(side="left")

        ttk.Button(header, text="Test Database", command=self.check_db).pack(
            side="right", padx=(6, 0)
        )
        ttk.Button(header, text="Refresh Data", command=self.load_products).pack(
            side="right", padx=6
        )

    def _build_product_form(self) -> None:
        form = ttk.LabelFrame(
            self.root,
            text="Product Details",
            padding=10,
            style="Section.TLabelframe",
        )
        form.pack(fill="x", padx=14, pady=(0, 8))

        for index, (label, key) in enumerate(self.PRODUCT_FIELDS):
            row, column = divmod(index, 4)
            cell = ttk.Frame(form)
            cell.grid(row=row, column=column, sticky="ew", padx=6, pady=5)

            ttk.Label(cell, text=label).pack(anchor="w", pady=(0, 3))
            variable = tk.StringVar()
            self.variables[key] = variable
            ttk.Entry(cell, textvariable=variable, width=25).pack(fill="x")
            form.columnconfigure(column, weight=1)

        actions = ttk.Frame(form)
        actions.grid(row=3, column=0, columnspan=4, sticky="w", padx=5, pady=(8, 2))

        ttk.Button(
            actions, text="Add Product", style="Primary.TButton", command=self.add_product
        ).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Update Selected", command=self.update_product).pack(
            side="left", padx=6
        )
        ttk.Button(actions, text="Clear Form", command=self.clear_form).pack(
            side="left", padx=6
        )

    def _build_stock_movement_form(self) -> None:
        movement = ttk.LabelFrame(
            self.root,
            text="Stock Movement — select a product from the table first",
            padding=10,
            style="Section.TLabelframe",
        )
        movement.pack(fill="x", padx=14, pady=(0, 8))

        self.transaction_type = tk.StringVar(value="IN")
        self.transaction_quantity = tk.StringVar()
        self.reference_number = tk.StringVar()
        self.remarks = tk.StringVar()

        fields = [
            ("Movement Type", 0),
            ("Quantity (Adjustment = final stock)", 1),
            ("Reference Number", 2),
            ("Remarks", 3),
        ]
        for label, column in fields:
            ttk.Label(movement, text=label).grid(
                row=0, column=column, sticky="w", padx=5, pady=(0, 4)
            )

        ttk.Combobox(
            movement,
            textvariable=self.transaction_type,
            values=("IN", "OUT", "ADJUSTMENT"),
            state="readonly",
            width=18,
        ).grid(row=1, column=0, sticky="ew", padx=5)

        ttk.Entry(movement, textvariable=self.transaction_quantity, width=24).grid(
            row=1, column=1, sticky="ew", padx=5
        )
        ttk.Entry(movement, textvariable=self.reference_number, width=24).grid(
            row=1, column=2, sticky="ew", padx=5
        )
        ttk.Entry(movement, textvariable=self.remarks, width=36).grid(
            row=1, column=3, sticky="ew", padx=5
        )
        ttk.Button(
            movement, text="Save Movement", style="Primary.TButton", command=self.save_transaction
        ).grid(row=1, column=4, padx=(10, 4))

        for column in range(4):
            movement.columnconfigure(column, weight=1)

    def _build_product_table(self) -> None:
        table_frame = ttk.Frame(self.root, padding=(14, 4, 14, 14))
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            table_frame, columns=self.TABLE_COLUMNS, show="headings", selectmode="browse"
        )

        for column, width in zip(self.TABLE_COLUMNS, self.TABLE_WIDTHS):
            self.tree.heading(column, text=column)
            self.tree.column(column, width=width, minwidth=65, anchor="center")

        self.tree.tag_configure("out_of_stock", foreground="#b42318")
        self.tree.tag_configure("low_stock", foreground="#b54708")
        self.tree.tag_configure("out_of_target", foreground="#6941c6")
        self.tree.tag_configure("ok", foreground="#067647")

        vertical_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        horizontal_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _close_database(cursor=None, connection=None) -> None:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    def check_db(self) -> None:
        try:
            result = test_connection()
            messagebox.showinfo("Database Connection", f"Connection successful.\nDatabase: {result}")
        except Exception as error:
            messagebox.showerror(
                "Database Connection Failed",
                f"Could not connect to MySQL.\n\nDetails: {error}\n\nCheck database.py and MySQL Server.",
            )

    def load_products(self, show_errors: bool = True) -> None:
        """Load current products and derive status from stock, reorder and target levels."""
        connection = cursor = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT
                    ProductID,
                    ProductName,
                    SKU,
                    Category,
                    Warehouse,
                    Stock,
                    Price,
                    CostPrice,
                    ReorderLevel,
                    CASE
                        WHEN Stock = 0 THEN 'OUT OF STOCK'
                        WHEN Stock > TargetStock THEN 'OUT OF TARGET STOCK'
                        WHEN Stock <= ReorderLevel THEN 'LOW STOCK'
                        ELSE 'OK'
                    END AS Status
                FROM products
                ORDER BY ProductID
                """
            )

            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in cursor.fetchall():
                status = row[-1]
                tag = {
                    "OUT OF STOCK": "out_of_stock",
                    "LOW STOCK": "low_stock",
                    "OUT OF TARGET STOCK": "out_of_target",
                    "OK": "ok",
                }.get(status, "")
                self.tree.insert("", "end", values=row, tags=(tag,))

        except Exception as error:
            if show_errors:
                messagebox.showerror("Unable to Load Products", str(error))
        finally:
            self._close_database(cursor, connection)

    # ------------------------------------------------------------------
    # Product form validation and CRUD operations
    # ------------------------------------------------------------------
    def _read_product_form(self) -> dict:
        values = {key: variable.get().strip() for key, variable in self.variables.items()}

        if not values["ProductName"]:
            raise ValueError("Product Name is required.")
        if not values["Price"]:
            raise ValueError("Selling Price is required.")

        try:
            defaults = {
                "Stock": 0,
                "ReorderLevel": DEFAULT_REORDER_LEVEL,
                "TargetStock": DEFAULT_TARGET_STOCK,
            }
            for key, default in defaults.items():
                values[key] = int(values[key] or default)

            for key in ("Price", "CostPrice"):
                values[key] = float(values[key] or 0)
        except ValueError as error:
            raise ValueError(
                "Stock, Reorder Level and Target Stock must be whole numbers. "
                "Selling Price and Cost Price must be numeric."
            ) from error

        numeric_values = (
            values["Stock"],
            values["ReorderLevel"],
            values["TargetStock"],
            values["Price"],
            values["CostPrice"],
        )
        if any(value < 0 for value in numeric_values):
            raise ValueError("Negative stock levels and prices are not allowed.")

        if values["Stock"] > values["TargetStock"]:
            raise ValueError(
                "OUT OF TARGET STOCK: Current Stock cannot be greater than Target Stock. "
                f"Current Stock = {values['Stock']}, Target Stock = {values['TargetStock']}."
            )

        return values

    @staticmethod
    def _product_parameters(values: dict) -> tuple:
        return (
            values["ProductName"],
            values["SKU"] or None,
            values["Category"] or None,
            values["Brand"] or None,
            values["SupplierName"] or None,
            values["Warehouse"] or DEFAULT_WAREHOUSE,
            values["Stock"],
            values["Price"],
            values["CostPrice"],
            values["ReorderLevel"],
            values["TargetStock"],
        )

    def add_product(self) -> None:
        connection = cursor = None
        try:
            values = self._read_product_form()
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO products (
                    ProductName, SKU, Category, Brand, SupplierName, Warehouse,
                    Stock, Price, CostPrice, ReorderLevel, TargetStock
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                self._product_parameters(values),
            )
            product_id = cursor.lastrowid

            if values["Stock"] > 0:
                cursor.execute(
                    """
                    INSERT INTO inventory_transactions (
                        ProductID, TransactionType, Quantity, UnitCost,
                        ReferenceNo, Department, Remarks
                    ) VALUES (%s, 'IN', %s, %s, 'OPENING-STOCK', 'Inventory', %s)
                    """,
                    (product_id, values["Stock"], values["CostPrice"], "Opening stock from GUI"),
                )

            connection.commit()
            self.clear_form()
            self.load_products()
            messagebox.showinfo("Product Added", "Product added successfully.")
        except Exception as error:
            if connection is not None:
                connection.rollback()
            messagebox.showerror("Add Product Failed", str(error))
        finally:
            self._close_database(cursor, connection)

    def update_product(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("Select a Product", "Select a product from the table first.")
            return

        connection = cursor = None
        try:
            values = self._read_product_form()
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE products SET
                    ProductName = %s, SKU = %s, Category = %s, Brand = %s,
                    SupplierName = %s, Warehouse = %s, Stock = %s, Price = %s,
                    CostPrice = %s, ReorderLevel = %s, TargetStock = %s
                WHERE ProductID = %s
                """,
                self._product_parameters(values) + (self.selected_id,),
            )
            connection.commit()
            self.clear_form()
            self.load_products()
            messagebox.showinfo("Product Updated", "Product updated successfully.")
        except Exception as error:
            if connection is not None:
                connection.rollback()
            messagebox.showerror("Update Product Failed", str(error))
        finally:
            self._close_database(cursor, connection)

    # ------------------------------------------------------------------
    # Stock movement
    # ------------------------------------------------------------------
    def save_transaction(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Select a Product", "Select a product from the table first.")
            return

        try:
            quantity = int(self.transaction_quantity.get().strip())
            if quantity <= 0:
                raise ValueError("Quantity must be greater than zero.")
        except ValueError as error:
            messagebox.showerror("Invalid Quantity", str(error) or "Enter a whole-number quantity.")
            return

        product_id = int(self.tree.item(selection[0], "values")[0])
        movement_type = self.transaction_type.get()
        connection = cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(
                "SELECT Stock, CostPrice, TargetStock FROM products WHERE ProductID = %s FOR UPDATE",
                (product_id,),
            )
            product = cursor.fetchone()
            if product is None:
                raise ValueError("Selected product could not be found.")

            current_stock = int(product[0])
            unit_cost = float(product[1] or 0)
            target_stock = int(product[2])

            if movement_type == "IN":
                new_stock = current_stock + quantity
            elif movement_type == "OUT":
                if quantity > current_stock:
                    raise ValueError(f"Insufficient stock. Current stock: {current_stock}.")
                new_stock = current_stock - quantity
            elif movement_type == "ADJUSTMENT":
                # For ADJUSTMENT, Quantity is the desired final stock value.
                new_stock = quantity
            else:
                raise ValueError("Choose a valid stock movement type.")

            if new_stock > target_stock:
                raise ValueError(
                    "OUT OF TARGET STOCK: This movement would exceed the target. "
                    f"Target Stock = {target_stock}, requested new stock = {new_stock}."
                )

            cursor.execute(
                "UPDATE products SET Stock = %s WHERE ProductID = %s",
                (new_stock, product_id),
            )
            cursor.execute(
                """
                INSERT INTO inventory_transactions (
                    ProductID, TransactionType, Quantity, UnitCost,
                    ReferenceNo, Department, Remarks
                ) VALUES (%s, %s, %s, %s, %s, 'Inventory', %s)
                """,
                (
                    product_id,
                    movement_type,
                    quantity,
                    unit_cost,
                    self.reference_number.get().strip() or None,
                    self.remarks.get().strip() or None,
                ),
            )
            connection.commit()

            self.transaction_quantity.set("")
            self.reference_number.set("")
            self.remarks.set("")
            self.clear_form()
            self.load_products()
            messagebox.showinfo("Stock Movement Saved", f"Stock updated successfully. New stock: {new_stock}")
        except Exception as error:
            if connection is not None:
                connection.rollback()
            messagebox.showerror("Stock Movement Failed", str(error))
        finally:
            self._close_database(cursor, connection)

    # ------------------------------------------------------------------
    # Selection and reset
    # ------------------------------------------------------------------
    def on_select(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return

        self.selected_id = int(self.tree.item(selection[0], "values")[0])
        connection = cursor = None
        try:
            connection = get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM products WHERE ProductID = %s", (self.selected_id,))
            product = cursor.fetchone()
            if product:
                for key, variable in self.variables.items():
                    value = product.get(key)
                    variable.set("" if value is None else str(value))
        except Exception as error:
            messagebox.showerror("Unable to Select Product", str(error))
        finally:
            self._close_database(cursor, connection)

    def clear_form(self) -> None:
        self.selected_id = None
        for variable in self.variables.values():
            variable.set("")

        self.variables["Warehouse"].set(DEFAULT_WAREHOUSE)
        self.variables["ReorderLevel"].set(str(DEFAULT_REORDER_LEVEL))
        self.variables["TargetStock"].set(str(DEFAULT_TARGET_STOCK))

        for item in self.tree.selection():
            self.tree.selection_remove(item)


def main() -> None:
    root = tk.Tk()
    InventoryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
