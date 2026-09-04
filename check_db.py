import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password=''
    )
    print("✅ Connected to MySQL!")
    
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES")
    databases = cursor.fetchall()
    
    print("\n📊 Available databases:")
    for db in databases:
        print(f"   - {db[0]}")
    
    # Check if YOUR database exists
    cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'whatsap_online bot'")
    result = cursor.fetchone()
    
    if result:
        print("\n✅ Database 'whatsap_online bot' exists!")
        conn.database = 'whatsap_online bot'
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("\n📋 Tables in whatsap_online bot:")
        for table in tables:
            print(f"   - {table[0]}")
    else:
        print("\n❌ Database 'whatsap_online bot' NOT found!")
        print("🔧 Please create it in phpMyAdmin")
    
    conn.close()
    
except mysql.connector.Error as e:
    print(f"❌ Error: {e}")
    print("\n🔧 Possible fixes:")
    print("1. Is XAMPP running? (MySQL should be green)")
    print("2. Is the password correct? (Default is empty)")