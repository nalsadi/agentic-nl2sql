import sqlite3
import json
import os
from typing import Optional
from ..config.settings import SPIDER_DB_PATH

class DatabaseManager:
 # Manager for handling SQLite dbs
    def __init__(self):
        self.current_db_path: Optional[str] = None
    
    def set_database(self, db_name: str) -> str:
        """Set the current database to work with"""
        db_path = os.path.join(SPIDER_DB_PATH, db_name, f"{db_name}.sqlite")
        if not os.path.exists(db_path):
            return f"Database {db_name} not found at {db_path}"
        self.current_db_path = db_path
        return f"Database set to {db_name} at {db_path}"
    
    def execute_query(self, query: str) -> str:
        """Execute SQL query against the current SQLite database"""
        if not self.current_db_path:
            return "No database selected. Please set a database first."
        
        try:
            # Connect to the SQLite database
            conn = sqlite3.connect(self.current_db_path)
            cursor = conn.cursor()
            
            # Execute the query
            cursor.execute(query)
            
            # Check if it's a SELECT or PRAGMA query (returns data)
            if query.strip().upper().startswith(('SELECT', 'PRAGMA')):
                # Fetch all results
                rows = cursor.fetchall()
                
                # Get column names
                columns = [description[0] for description in cursor.description]
                
                # Format results as JSON
                results = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        row_dict[columns[i]] = str(value) if value is not None else None
                    results.append(row_dict)
                
                # Close connection
                cursor.close()
                conn.close()
                
                if not results:
                    return "Query executed successfully but returned no results."
                
                return json.dumps(results, indent=2)
            
            else:
                # For non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
                conn.commit()
                affected_rows = cursor.rowcount
                
                # Close connection
                cursor.close()
                conn.close()
                
                return f"Query executed successfully. {affected_rows} row(s) affected."
        
        except sqlite3.Error as e:
            return f"Database error: {str(e)}"
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    def get_tables(self) -> str:
        """Get list of tables in the current database"""
        return self.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
    
    def get_table_info(self, table_name: str) -> str:
        """Get schema information for a specific table"""
        return self.execute_query(f"PRAGMA table_info({table_name})")
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> str:
        """Get sample data from a table"""
        return self.execute_query(f"SELECT * FROM {table_name} LIMIT {limit}")

# Global database manager instance
db_manager = DatabaseManager()

def sql_query(query: str) -> str:
    """Execute SQL query - wrapper function for backward compatibility"""
    return db_manager.execute_query(query)

def set_database(db_name: str) -> str:
    """Set database - wrapper function for backward compatibility"""
    return db_manager.set_database(db_name)
