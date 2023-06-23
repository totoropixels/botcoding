import sqlite3

class database:
    def __init__(self, databasename):
        self.dbname = databasename

        return

    def connect(self):
        # Connects to Database
        global sqliteconnection
        try:
            sqliteconnection = sqlite3.connect(self.dbname)
            c = sqliteconnection.cursor()
            
            print("Database created and Successfully connected")
            query = "select sqlite_version();"
            print("Search Query:", query)
            
            c.execute(query)
            record = c.fetchall()
            print("SQLite Database Version is: ", record)
            return
        except:
            print("Failed to delete record from sqlite table")
            return
    
    def table(self, query):
        # Creates the table from given query
        global sqliteconnection
        try:      
            c = sqliteconnection.cursor()
            c.execute(query)
            print("Table Query:", query)
            sqliteconnection.commit()
            print("Table Created Successfully")
            return
        except sqlite3.Error as error:
            print(error)
            return

    def queryBuilder(self, df, databaseName):
        # Creates queries to build a table and insert data from given dataframe    
        lst = list(df.columns.values)
        tablestring = ""
        insertstring1 = ""
        insertstring2 = ""

        for name in lst:
            tablestring += f'"{name}"' + ', '

        tablestring = tablestring[:-2]
        tableQuery = f"Create table if not Exists {databaseName} ({tablestring})"
            
        for name in lst:
            insertstring1 += f'"{name}"' + ', '
        
        insertstring1 = insertstring1[:-2]   
        for x in range(len(lst)):
            insertstring2 += '?, '

        insertstring2 = insertstring2[:-2]
        insertQuery = f"INSERT INTO {databaseName} ({insertstring1}) VALUES ({insertstring2})"  
        
        self.table(tableQuery)
        for index, row in df.iterrows():
            self.insert(insertQuery, tuple(row))

        return

    def insert(self, query, tup):
        global sqliteconnection
        # Inserts data into the specified table
        try:
            c = sqliteconnection.cursor()
            c.execute(query, tup)
            print("Insert Query:", query)
            sqliteconnection.commit()
            print("Inserted Successfully")
            return
        except sqlite3.Error as error:
            print("Failed to Insert: ", error)
            return

    def readTable(self, tableName):
        global sqliteconnection
        records = None
        
        # Prints the specified table contents
        try:
            c = sqliteconnection.cursor()
            query = f"SELECT * from {tableName}"
            print('Query:', query)
            
            c.execute(query)
            records = c.fetchall()
            print("Total Rows:", len(records))
            return records
        except sqlite3.Error as error:
            print("Error:", error)
            return
        

    def search(self, value, tableName, columnName):
        global sqliteconnection
        c = sqliteconnection.cursor()
        
        # Searches for the value in the specific column in the specified table
        query = f"SELECT * FROM {tableName} WHERE {columnName} == {value}"
        print("Search Query:", query)
        c.execute(query)
        result = c.fetchall()
        return result

    def deleteRecord(self, ID, databaseName, columnName):
        global sqliteconnection
        try:
            c = sqliteconnection.cursor()
            # Deletes record from specific table if it exists
            query = f"DELETE from {databaseName} where {columnName} = ?"
            print(f"Deleting Query: DELETE from {databaseName} WHERE {columnName} = {ID}")
            c.execute(query, (str(ID),))
            sqliteconnection.commit()
            print("Record deleted successfully")
            return
        except sqlite3.Error as error:
            print("Failed to delete:", error)
            return

    def clearTable(self, tableName):
        global sqliteconnection
        try:
            c = sqliteconnection.cursor()
            # Deletes all data from specified table
            c.execute(f"DELETE FROM {tableName}")
            sqliteconnection.commit()
            print("Cleared all data from {tableName}")
            return
        except sqlite3.Error as error:
            print("Failed to clear all data", error)
            return
        
    def updateDB(self, query):
        global sqliteconnection
        try:
            c = sqliteconnection.cursor()
            # Update the specified row
            c.execute(query)
            sqliteconnection.commit()
            print("Successfully updated the row\n" + query)
        except sqlite3.Error as error:
            print(error)
            return