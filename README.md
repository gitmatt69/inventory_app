# Group 12 Semester Project - Web-Based Supply Chain Application
This is a repository for a web-based application for the module BFB 321. This is the submission regarding the semester project for Group 12.

## Group members
Matthew Taylor, u23739772  
Daniël Johannes Voges, u23539519  
Etienne Kros, u23628911  
Chris-Dian Haasbroek, u05017158

## Project Purpose
The objective and purpose of this project is to improve VanH's operational efficiency by means of improving data commmunication and system visibility. This is achieved by constructing and implementing a web-based Sales and Operations Planning (S&OP) platform for the business to replace their current manual, paper-based data communication system. This platform will effectively execute various supply chain management functions such as centralised data communication, optimising order cycle times, comprehensive inventory tracking and improving overall prodcuction quality. 

Centralised data communication will improve day-to-day logistics and manufacturing operations by promoting process transparency to all parties that it may concern and effective communication between employees and managers. Inventory tracking enables inventory visbility which allows VanH to minimise its material handling expenses while sustaining maximum client service levels and avoiding stock-outs. The system highlights supply chain bottlenecks and underutilised proceses that may serve as potential alleviators which reduces the aggregate cycle time of orders. This accumulates into greater customer service. Production quality is improved by granting VanH strict supervision on product standards and enabling the business to study defective products to determine their root causes and take action. 

Once the web-based S&OP platform has been constructed it is integrated into VanH's operations to replace the current manual paper-based data communication system and thereby improve overall operational efficiency.

## File Structure 
![file_structure](https://github.com/user-attachments/assets/ff9550c1-b3b1-4505-9a64-c07e60c0b79b)


## Database Schema
The project has tables for customers, sales orders and sales order details to ensure that the end user can track all sales related information in real time. Similarly, there are tables for suppliers, purchase orders and purchase order details. The project also has tables for stock and warehouses to ensure that inventory is tracked accurately. The warehouses table is included to allow for scalability if the company ever opens multiple warehouses or production facilities. The categories table allows the end user to track stock per category, and to easily change categories in the future without needing a lot of extra work in the database. The transactions and users tables are included to allow for tracking who has made what changes to the website, and for user verification (which will only be implemented later in the project, as it was not included in this submission).
## Entity Realtionship Diagram (ERD)
![bfb_erd](https://github.com/user-attachments/assets/3f3426a5-f8c3-4f88-9ad1-bf38cb00faff)
## Sample Data
- __7 Inventory Categories__: Raw Materials, Bibs, Jerseys, Shorts, Gloves, Helmets, Accessories.  
- __2 Suppliers__: TechSupplies Inc. and FurniCo.  
- __2 Customers__: Acme Corp. and Beta LLC.  
- __2 Warehouses__: Main Warehouse and Secondary Warehouse.  
- __8 Items__: Linen Cloth, Cotton Fabric, Zips, Womens Navy Hyper Jersey, Womens Purple Hyper Jersey, Womens Coupure Shorts, Pink Nova Gloves, Kolisi Songo Jersey.  
  
We also created two purchase orders linked to their details, and did the same for ten sales orders. Additionally, we inserted two users and three stock movement transactions.

## Running the App
The following steps are required to ensure that the constructed inventory management app runs effectively and without any errors.
Please ensure to use Google Chrome to run the app, as we have had issues with Microsoft Edge and our CSS/styling. 
### Step 1: Clone the repository
Open VS Code and do either of the following: 
Press Ctrl Shift P and then use the following (Ensure you select Group 12 after typing this)
```
Git: Clone
```
OR type in a terminal the following: 
```
git clone https://github.com/gitmatt69/Group12
cd Group12
```

### Step 2: Create a virtual environment
Ensure that the latest version of Python is installed. (This is version 3.14.0 at the time of writing)
Type in a terminal:
```
python -m venv venv
```
Then use one of the folliwng depending on your machine:
Windows (Command Prompt):
``` 
venv\Scripts\activate
```
Windows (PowerShell):
```
.\venv\Scripts\Activate.ps1
```
Mac/Linux:
```
source venv/bin/activate
```
To download Flask, type in the terminal:
```
pip install Flask
```
### Step 3: Initialise the database
Open the inventory.sql file in VS Code. Then do the following: 
Press Ctrl Shift P and select the following (Ensure no code is highlighted so all the tables are created and all data is inserted)
```
SQLite: Run Query
```
OR open a terminal/command prompt and run the following:
```
sqlite3 inventory.db < inventory.sql
```
You should now have a working database!   
If you do not have a working database, please follow these steps. We discovered during testing that uploading the empty inventory.db file sometimes makes the .sql file run with errors. If this happens, ensure that the web app is closed and delete the inventory.db file. Then, make a new inventory.db file, and run the inventory.sql file again as per the previous steps. You may also need to close and reopen VS Code. 
### Step 4: Running the app
If you created a virtual environment, use the following in a terminal:
```
flask run
```
Then the app will open at the following __(Use Google Chrome)__ 
```
http://127.0.0.1:5000
```
If you did not create a virtual environment, use the following in a terminal:
```
python app.py
```
It will open at the following __(Use Google Chrome)__
```
http://127.0.0.1:5000  
```

## Technology Stack
Front-end: HTML5, CSS and Bootstrap   
Back-end: Python (Flask framework) for logic and SQLite for the database. 
