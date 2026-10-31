CREATE DATABASE IF NOT EXISTS Inventory_Management_System;
USE Inventory_Management_System;

CREATE TABLE IF NOT EXISTS products (
    ProductID INT AUTO_INCREMENT PRIMARY KEY,
    ProductName VARCHAR(100) NOT NULL,
    SKU VARCHAR(30) UNIQUE,
    Category VARCHAR(50),
    Brand VARCHAR(50),
    SupplierName VARCHAR(100),
    Warehouse VARCHAR(50) DEFAULT 'Jaipur Warehouse',
    Stock INT NOT NULL DEFAULT 0,
    Price DECIMAL(10,2) NOT NULL,
    CostPrice DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    ReorderLevel INT NOT NULL DEFAULT 10,
    TargetStock INT NOT NULL DEFAULT 50,
    LastUpdated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory_transactions (
    TransactionID INT AUTO_INCREMENT PRIMARY KEY,
    ProductID INT NOT NULL,
    TransactionType ENUM('IN', 'OUT', 'ADJUSTMENT') NOT NULL,
    Quantity INT NOT NULL,
    UnitCost DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    ReferenceNo VARCHAR(50),
    Department VARCHAR(50),
    TransactionDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Remarks VARCHAR(255),
    FOREIGN KEY (ProductID) REFERENCES products(ProductID)
);

-- Demo data is inserted only when the products table is empty.
INSERT INTO products
(ProductName, SKU, Category, Brand, SupplierName, Warehouse, Stock, Price, CostPrice, ReorderLevel, TargetStock)
SELECT d.* FROM (
    SELECT 'Laptop' ProductName,'ELEC-001' SKU,'Electronics' Category,'Dell' Brand,'Tech Suppliers' SupplierName,'Jaipur Warehouse' Warehouse,25 Stock,60000.00 Price,48000.00 CostPrice,10 ReorderLevel,50 TargetStock
    UNION ALL SELECT 'Mouse','ACC-001','Accessories','Logitech','Digital Traders','Jaipur Warehouse',8,800.00,500.00,15,60
    UNION ALL SELECT 'Keyboard','ACC-002','Accessories','HP','Digital Traders','Jaipur Warehouse',30,1500.00,1000.00,10,50
    UNION ALL SELECT 'Monitor','ELEC-002','Electronics','Samsung','Tech Suppliers','Delhi Warehouse',12,12000.00,9000.00,10,30
    UNION ALL SELECT 'Printer','ELEC-003','Electronics','Canon','Office Solutions','Jaipur Warehouse',0,18000.00,14000.00,5,20
    UNION ALL SELECT 'USB Cable','ACC-003','Accessories','Portronics','Digital Traders','Delhi Warehouse',100,250.00,120.00,20,100
    UNION ALL SELECT 'Webcam','ELEC-004','Electronics','Logitech','Tech Suppliers','Jaipur Warehouse',6,3500.00,2500.00,10,30
    UNION ALL SELECT 'Office Chair','FURN-001','Furniture','Godrej','Office Solutions','Delhi Warehouse',18,8500.00,6500.00,5,25
    UNION ALL SELECT 'Desk','FURN-002','Furniture','IKEA','Office Solutions','Jaipur Warehouse',4,7000.00,5200.00,5,20
    UNION ALL SELECT 'Headphones','ACC-004','Accessories','Sony','Digital Traders','Jaipur Warehouse',40,2200.00,1500.00,10,50
) d
WHERE NOT EXISTS (SELECT 1 FROM products);

INSERT INTO inventory_transactions
(ProductID, TransactionType, Quantity, UnitCost, ReferenceNo, Department, Remarks)
SELECT p.ProductID, d.TransactionType, d.Quantity, d.UnitCost, d.ReferenceNo, d.Department, d.Remarks
FROM (
    SELECT 'ELEC-001' SKU,'IN' TransactionType,25 Quantity,48000.00 UnitCost,'PO-1001' ReferenceNo,'Purchase' Department,'Opening stock demo' Remarks
    UNION ALL SELECT 'ACC-001','IN',20,500.00,'PO-1002','Purchase','Mouse stock received'
    UNION ALL SELECT 'ACC-001','OUT',12,500.00,'SO-2001','Sales','Mouse sold'
    UNION ALL SELECT 'ACC-002','IN',30,1000.00,'PO-1003','Purchase','Keyboard stock received'
    UNION ALL SELECT 'ELEC-002','IN',12,9000.00,'PO-1004','Purchase','Monitor stock received'
    UNION ALL SELECT 'ACC-003','IN',100,120.00,'PO-1005','Purchase','USB cable stock received'
    UNION ALL SELECT 'ELEC-004','IN',10,2500.00,'PO-1006','Purchase','Webcam stock received'
    UNION ALL SELECT 'FURN-001','IN',18,6500.00,'PO-1007','Purchase','Office chairs received'
    UNION ALL SELECT 'FURN-002','IN',4,5200.00,'PO-1008','Purchase','Desk stock received'
    UNION ALL SELECT 'ACC-004','IN',40,1500.00,'PO-1009','Purchase','Headphones received'
) d
JOIN products p ON p.SKU = d.SKU
WHERE NOT EXISTS (SELECT 1 FROM inventory_transactions);

SELECT * FROM products;
SELECT * FROM inventory_transactions;
