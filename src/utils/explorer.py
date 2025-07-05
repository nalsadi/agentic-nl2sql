import json
from ..tools.database import db_manager
import os

class DatabaseExplorer:    
    def __init__(self):
        self.db_manager = db_manager
    
    def explore_database(self, db_name: str) -> dict:
        print(f"\n Exploring database: {db_name}")
        
        # Set db
        set_result = self.db_manager.set_database(db_name)
        print(f"{set_result}")
        
        exploration_results = {
            "database": db_name,
            "tables": [],
            "total_tables": 0,
            "sample_data": {}
        }
        
        try:
            tables_result = self.db_manager.get_tables()
            print(f"\n Tables in {db_name}:")
            print(tables_result)
            
            tables = json.loads(tables_result)
            exploration_results["total_tables"] = len(tables)
            
            for table_info in tables:
                table_name = table_info['name']
                exploration_results["tables"].append(table_name)
                
                print(f"\n Structure of table '{table_name}':")
                structure = self.db_manager.get_table_info(table_name)
                print(structure)
                
                print(f"\n Sample data from '{table_name}' (first 3 rows):")
                sample = self.db_manager.get_sample_data(table_name, 3)
                print(sample)
                
                exploration_results["sample_data"][table_name] = {
                    "structure": json.loads(structure) if structure.startswith('[') else structure,
                    "sample": json.loads(sample) if sample.startswith('[') else sample
                }
        
        except Exception as e:
            print(f" Error exploring database: {e}")
            exploration_results["error"] = str(e)
        
        return exploration_results
    
    def quick_explore(self, db_name: str, max_tables: int = 3) -> dict:
        print(f"\n Quick exploration of database: {db_name}")
        
        set_result = self.db_manager.set_database(db_name)
        print(f" {set_result}")
        
        results = {"database": db_name, "tables": []}
        
        try:
            tables_result = self.db_manager.get_tables()
            tables = json.loads(tables_result)
            
            print(f"\n Found {len(tables)} tables. Showing first {max_tables}:")
            
            for table_info in tables[:max_tables]:
                table_name = table_info['name']
                print(f"\n Table: {table_name}")
                
                structure = self.db_manager.get_table_info(table_name)
                sample = self.db_manager.get_sample_data(table_name, 2)
                
                results["tables"].append({
                    "name": table_name,
                    "structure": json.loads(structure) if structure.startswith('[') else structure,
                    "sample": json.loads(sample) if sample.startswith('[') else sample
                })
                
                print(f"  Columns: {len(json.loads(structure))}")
                print(f"  Sample: {sample[:100]}..." if len(sample) > 100 else f"  Sample: {sample}")
        
        except Exception as e:
            print(f" Error in quick exploration: {e}")
            results["error"] = str(e)
        
        return results
    
    def list_available_databases(self, spider_db_path: str = "spider_data/database") -> list:        
        if not os.path.exists(spider_db_path):
            print(f" Spider database path not found: {spider_db_path}")
            return []
        
        databases = []
        for item in os.listdir(spider_db_path):
            item_path = os.path.join(spider_db_path, item)
            if os.path.isdir(item_path):
                # Check if SQLite file exists
                sqlite_file = os.path.join(item_path, f"{item}.sqlite")
                if os.path.exists(sqlite_file):
                    databases.append(item)
        
        databases.sort()
        print(f" Found {len(databases)} Spider databases:")
        
        for i, db in enumerate(databases[:20]):
            print(f"  {db}")
        
        if len(databases) > 20:
            print(f"  ... and {len(databases) - 20} more")
        
        return databases

explorer = DatabaseExplorer()
