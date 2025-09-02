#!/usr/bin/env python3
"""
Migration script to add delivery_status and contract_status fields to the rooms table
and update existing room status from '闭户' to '验收完成' where applicable.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from database import SQLALCHEMY_DATABASE_URL, get_db
import models

def migrate_database():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # For SQLite, check if columns exist by trying to add them and catching the error
            try:
                print("Adding delivery_status column...")
                connection.execute(text("""
                    ALTER TABLE rooms 
                    ADD COLUMN delivery_status VARCHAR DEFAULT '待交付'
                """))
                connection.commit()
                print("* delivery_status column added")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("delivery_status column already exists")
                else:
                    raise e
            
            try:
                print("Adding contract_status column...")
                connection.execute(text("""
                    ALTER TABLE rooms 
                    ADD COLUMN contract_status VARCHAR DEFAULT '待签约'
                """))
                connection.commit()
                print("* contract_status column added")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("contract_status column already exists")
                else:
                    raise e
            
            # Update existing rooms with default values if they're null
            print("Setting default values for existing records...")
            connection.execute(text("""
                UPDATE rooms 
                SET delivery_status = '待交付' 
                WHERE delivery_status IS NULL
            """))
            connection.execute(text("""
                UPDATE rooms 
                SET contract_status = '待签约' 
                WHERE contract_status IS NULL
            """))
            connection.commit()
            print("* Default values set for existing records")
            
            # Update room status from '闭户' to '验收完成'
            print("Updating room status from '闭户' to '验收完成'...")
            result = connection.execute(text("""
                UPDATE rooms 
                SET status = '验收完成' 
                WHERE status = '闭户'
            """))
            connection.commit()
            updated_count = result.rowcount
            print(f"* Updated {updated_count} rooms from '闭户' to '验收完成'")
            
            print("\nMigration completed successfully!")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate_database()