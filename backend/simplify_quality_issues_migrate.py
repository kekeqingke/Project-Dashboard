#!/usr/bin/env python3
"""
简化质量问题验收管理功能 - 数据库迁移脚本

功能：
1. 将"需复验"状态数据迁移为"待验收"
2. 移除复杂验收字段 (revoked_by, revoked_at, reverified_by, reverified_at)
3. 创建操作日志表 (quality_issue_logs)
4. 迁移现有验收记录到日志表

执行前请确保数据库已备份！
"""

import sqlite3
import json
from datetime import datetime
import os
import shutil

DATABASE_PATH = "zwy_project.db"
BACKUP_PATH = f"quality_management_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

def backup_database():
    """备份数据库"""
    if os.path.exists(DATABASE_PATH):
        shutil.copy2(DATABASE_PATH, BACKUP_PATH)
        print(f"✅ 数据库已备份到: {BACKUP_PATH}")
        return True
    else:
        print("❌ 数据库文件不存在")
        return False

def connect_db():
    """连接数据库"""
    return sqlite3.connect(DATABASE_PATH)

def create_quality_issue_logs_table(conn):
    """创建操作日志表"""
    cursor = conn.cursor()
    
    # 检查表是否已存在
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='quality_issue_logs'
    """)
    
    if cursor.fetchone():
        print("⚠️ quality_issue_logs 表已存在，跳过创建")
        return
    
    # 创建操作日志表
    cursor.execute("""
        CREATE TABLE quality_issue_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER NOT NULL,
            action VARCHAR(50) NOT NULL,
            operator_id INTEGER NOT NULL,
            operator_name VARCHAR(100),
            operator_role VARCHAR(50),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            before_data TEXT,
            after_data TEXT,
            remarks TEXT,
            FOREIGN KEY (issue_id) REFERENCES quality_issues (id),
            FOREIGN KEY (operator_id) REFERENCES users (id)
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX idx_issue_logs_issue_id ON quality_issue_logs(issue_id)")
    cursor.execute("CREATE INDEX idx_issue_logs_action ON quality_issue_logs(action)")
    cursor.execute("CREATE INDEX idx_issue_logs_timestamp ON quality_issue_logs(timestamp)")
    
    conn.commit()
    print("✅ 操作日志表创建成功")

def migrate_existing_logs(conn):
    """迁移现有验收记录到日志表"""
    cursor = conn.cursor()
    
    # 获取所有有验收记录的质量问题
    cursor.execute("""
        SELECT qi.id, qi.user_id, qi.accepted_by, qi.accepted_at,
               qi.revoked_by, qi.revoked_at, qi.reverified_by, qi.reverified_at,
               qi.status, qi.created_at,
               creator.name as creator_name, creator.role as creator_role,
               acceptor.name as acceptor_name, acceptor.role as acceptor_role,
               revoker.name as revoker_name, revoker.role as revoker_role,
               reverifier.name as reverifier_name, reverifier.role as reverifier_role
        FROM quality_issues qi
        LEFT JOIN users creator ON qi.user_id = creator.id
        LEFT JOIN users acceptor ON qi.accepted_by = acceptor.id
        LEFT JOIN users revoker ON qi.revoked_by = revoker.id
        LEFT JOIN users reverifier ON qi.reverified_by = reverifier.id
        WHERE qi.accepted_by IS NOT NULL 
           OR qi.revoked_by IS NOT NULL 
           OR qi.reverified_by IS NOT NULL
    """)
    
    records = cursor.fetchall()
    logs_created = 0
    
    for record in records:
        (issue_id, user_id, accepted_by, accepted_at, revoked_by, revoked_at, 
         reverified_by, reverified_at, status, created_at,
         creator_name, creator_role, acceptor_name, acceptor_role,
         revoker_name, revoker_role, reverifier_name, reverifier_role) = record
        
        # 创建问题录入日志
        cursor.execute("""
            INSERT INTO quality_issue_logs 
            (issue_id, action, operator_id, operator_name, operator_role, timestamp, after_data, remarks)
            VALUES (?, 'CREATE', ?, ?, ?, ?, ?, ?)
        """, (
            issue_id, user_id, creator_name, creator_role, created_at,
            json.dumps({"status": "待验收"}),
            "问题录入"
        ))
        logs_created += 1
        
        # 创建验收日志
        if accepted_by and accepted_at:
            cursor.execute("""
                INSERT INTO quality_issue_logs 
                (issue_id, action, operator_id, operator_name, operator_role, timestamp, 
                 before_data, after_data, remarks)
                VALUES (?, 'ACCEPT', ?, ?, ?, ?, ?, ?, ?)
            """, (
                issue_id, accepted_by, acceptor_name, acceptor_role, accepted_at,
                json.dumps({"status": "待验收"}),
                json.dumps({"status": "已验收", "accepted_by": accepted_by, "accepted_at": accepted_at}),
                "质量问题验收"
            ))
            logs_created += 1
        
        # 创建撤销验收日志
        if revoked_by and revoked_at:
            cursor.execute("""
                INSERT INTO quality_issue_logs 
                (issue_id, action, operator_id, operator_name, operator_role, timestamp,
                 before_data, after_data, remarks)
                VALUES (?, 'REVOKE_ACCEPT', ?, ?, ?, ?, ?, ?, ?)
            """, (
                issue_id, revoked_by, revoker_name, revoker_role, revoked_at,
                json.dumps({"status": "已验收"}),
                json.dumps({"status": "需复验"}),
                "撤销验收"
            ))
            logs_created += 1
        
        # 创建复验日志
        if reverified_by and reverified_at:
            cursor.execute("""
                INSERT INTO quality_issue_logs 
                (issue_id, action, operator_id, operator_name, operator_role, timestamp,
                 before_data, after_data, remarks)
                VALUES (?, 'REVERIFY', ?, ?, ?, ?, ?, ?, ?)
            """, (
                issue_id, reverified_by, reverifier_name, reverifier_role, reverified_at,
                json.dumps({"status": "需复验"}),
                json.dumps({"status": "已验收", "reverified_by": reverified_by, "reverified_at": reverified_at}),
                "复验通过"
            ))
            logs_created += 1
    
    conn.commit()
    print(f"✅ 迁移完成，创建了 {logs_created} 条操作日志")

def simplify_quality_issues_status(conn):
    """简化质量问题状态"""
    cursor = conn.cursor()
    
    # 统计当前状态分布
    cursor.execute("SELECT status, COUNT(*) FROM quality_issues GROUP BY status")
    status_stats = cursor.fetchall()
    print("📊 当前状态分布:")
    for status, count in status_stats:
        print(f"   {status}: {count}")
    
    # 将"需复验"状态改为"待验收"
    cursor.execute("""
        UPDATE quality_issues 
        SET status = '待验收' 
        WHERE status = '需复验'
    """)
    
    reverted_count = cursor.rowcount
    conn.commit()
    
    if reverted_count > 0:
        print(f"✅ 已将 {reverted_count} 个'需复验'状态改为'待验收'")
    else:
        print("ℹ️ 没有'需复验'状态需要处理")

def remove_complex_fields(conn):
    """移除复杂验收字段"""
    cursor = conn.cursor()
    
    # SQLite不支持直接删除列，需要重建表
    print("🔄 开始重建质量问题表，移除复杂字段...")
    
    # 创建新表结构
    cursor.execute("""
        CREATE TABLE quality_issues_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            issue_type VARCHAR(50) DEFAULT '质量瑕疵',
            images TEXT,
            status VARCHAR(20) DEFAULT '待验收',
            accepted_by INTEGER,
            accepted_at DATETIME,
            record_date DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (accepted_by) REFERENCES users (id)
        )
    """)
    
    # 迁移数据（只保留简化的字段）
    cursor.execute("""
        INSERT INTO quality_issues_new 
        (id, room_id, user_id, description, issue_type, images, status, 
         accepted_by, accepted_at, record_date, created_at)
        SELECT 
            id, room_id, user_id, description, issue_type, images, status,
            accepted_by, accepted_at, record_date, created_at
        FROM quality_issues
    """)
    
    # 删除旧表
    cursor.execute("DROP TABLE quality_issues")
    
    # 重命名新表
    cursor.execute("ALTER TABLE quality_issues_new RENAME TO quality_issues")
    
    # 重建索引
    cursor.execute("CREATE INDEX idx_quality_issues_room_id ON quality_issues(room_id)")
    cursor.execute("CREATE INDEX idx_quality_issues_user_id ON quality_issues(user_id)")
    cursor.execute("CREATE INDEX idx_quality_issues_status ON quality_issues(status)")
    cursor.execute("CREATE INDEX idx_quality_issues_created_at ON quality_issues(created_at)")
    
    conn.commit()
    print("✅ 质量问题表重建完成，复杂字段已移除")

def verify_migration(conn):
    """验证迁移结果"""
    cursor = conn.cursor()
    
    print("\n📋 迁移结果验证:")
    
    # 检查质量问题状态分布
    cursor.execute("SELECT status, COUNT(*) FROM quality_issues GROUP BY status")
    status_stats = cursor.fetchall()
    print("📊 简化后状态分布:")
    for status, count in status_stats:
        print(f"   {status}: {count}")
    
    # 检查日志表记录数
    cursor.execute("SELECT COUNT(*) FROM quality_issue_logs")
    log_count = cursor.fetchone()[0]
    print(f"📝 操作日志记录数: {log_count}")
    
    # 检查表结构
    cursor.execute("PRAGMA table_info(quality_issues)")
    columns = cursor.fetchall()
    print("🏗️ 质量问题表字段:")
    for col in columns:
        print(f"   {col[1]} ({col[2]})")
    
    # 验证不再有复杂字段
    complex_fields = ['revoked_by', 'revoked_at', 'reverified_by', 'reverified_at']
    column_names = [col[1] for col in columns]
    remaining_complex = [field for field in complex_fields if field in column_names]
    
    if remaining_complex:
        print(f"⚠️ 仍存在复杂字段: {remaining_complex}")
        return False
    else:
        print("✅ 所有复杂字段已成功移除")
        return True

def main():
    """主函数"""
    print("🚀 开始简化质量问题验收管理功能...")
    print("=" * 50)
    
    # 备份数据库
    if not backup_database():
        return
    
    try:
        conn = connect_db()
        
        # 1. 创建操作日志表
        create_quality_issue_logs_table(conn)
        
        # 2. 迁移现有验收记录到日志表
        migrate_existing_logs(conn)
        
        # 3. 简化质量问题状态
        simplify_quality_issues_status(conn)
        
        # 4. 移除复杂验收字段
        remove_complex_fields(conn)
        
        # 5. 验证迁移结果
        if verify_migration(conn):
            print("\n🎉 数据库迁移成功完成!")
            print(f"📁 备份文件: {BACKUP_PATH}")
            print("\n接下来请继续执行后端代码修改...")
        else:
            print("\n❌ 迁移验证失败，请检查数据库状态")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ 迁移过程出错: {str(e)}")
        print("请检查备份文件并恢复数据库")
        return False
    
    return True

if __name__ == "__main__":
    main()