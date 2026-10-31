import os, time
from datetime import datetime
import pandas as pd
from database import get_connection

OUTPUT_FILE=os.getenv("IMS_EXCEL_FILE","Inventory_Report.xlsx")
REFRESH_SECONDS=int(os.getenv("IMS_REFRESH_SECONDS","30"))

def refresh_excel():
    conn=get_connection()
    try:
        products=pd.read_sql("""SELECT ProductID,ProductName,SKU,Category,Brand,SupplierName,Warehouse,Stock,Price,CostPrice,
            ReorderLevel,TargetStock,LastUpdated,
            CASE WHEN Stock=0 THEN 'OUT OF STOCK' WHEN Stock<=ReorderLevel THEN 'LOW STOCK' ELSE 'OK' END StockStatus,
            Stock*CostPrice InventoryCostValue, Stock*Price PotentialSalesValue
            FROM products ORDER BY ProductID""",conn)
        transactions=pd.read_sql("""SELECT t.TransactionID,t.ProductID,p.ProductName,p.SKU,t.TransactionType,t.Quantity,t.UnitCost,
            t.ReferenceNo,t.Department,t.TransactionDate,t.Remarks FROM inventory_transactions t
            JOIN products p ON p.ProductID=t.ProductID ORDER BY t.TransactionDate DESC,t.TransactionID DESC""",conn)
    finally: conn.close()
    with pd.ExcelWriter(OUTPUT_FILE,engine="openpyxl") as writer:
        products.to_excel(writer,sheet_name="Products",index=False)
        transactions.to_excel(writer,sheet_name="Transactions",index=False)
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Excel refreshed: {os.path.abspath(OUTPUT_FILE)}")

if __name__=="__main__":
    print(f"Excel refresh service running every {REFRESH_SECONDS} seconds. Press Ctrl+C to stop.")
    while True:
        try: refresh_excel()
        except Exception as e: print("Refresh failed:",e)
        time.sleep(REFRESH_SECONDS)
