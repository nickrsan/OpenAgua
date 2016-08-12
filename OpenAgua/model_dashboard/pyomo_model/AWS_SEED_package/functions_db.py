import os

def db_mysql_connect(host='localhost', user='root'):
    import MySQLdb as db
    conn = db.connect(host=host, user=user)
    return conn

def db_connect(db_path, flavor='sqlite', new_db=True):
    
    if flavor=='mysql':
        conn = db_connection()
        curs = db_cursor(conn, p.db_name, new_db)
        #db_create_table(conn, curs, results_tbl, p.dbtype, p.datetypes, p.dtypes, p.results_list, p.aggregate)
        
    elif flavor=='sqlite':
        
        import sqlite3
        
        if new_db and os.path.exists(db_path):
            os.remove(db_path)
        conn = sqlite3.connect(db_path)
    
    return conn

# create the output database
def db_create(conn, db_name, new_db):
    import MySQLdb as db
    curs = conn.cursor()
    
    def db_create():
        curs.execute('CREATE DATABASE %s;' % db_name)
        
    def db_destroy():
        curs.execute('DROP DATABASE %s;' % db_name)
    
    sql = "SHOW DATABASES LIKE '%s'" % db_name
    if curs.execute(sql):
        if new_db:
            db_destroy()
            db_create()
    else:
        db_create()
            
    curs.execute("USE %s" % db_name)
    
    curs.close()

def db_create_table(conn, tbl, cols, dtypes, flavor, if_exists='append'):

    if flavor=='mysql':
        int_str = 'INT'
        inc_str = 'AUTO_INCREMENT'
    elif flavor=='sqlite':
        int_str = 'INTEGER'
        inc_str = 'AUTOINCREMENT'
    
    # create table
    cols_sql = ''
    lines = 'ID {} PRIMARY KEY {}'.format(int_str, inc_str)
    for c in cols:
        if c in dtypes.keys():
            lines += ', {} {}'.format(c, dtypes[c])
        else:
            lines += ', {} FLOAT'.format(c)
    lines += ' '
    
    if if_exists=='append':
        sql = """CREATE TABLE IF NOT EXISTS %s (%s)""" % (tbl, lines)
    else:
        try:
            conn.execute("DROP TABLE %s" % tbl)
        except:
            pass
        sql = """CREATE TABLE %s (%s)""" % (tbl, lines)
        
    conn.execute(sql)   
    conn.commit()

def db_insert_many(conn, tbl, cols, rows, dtypes, flavor='sqlite', if_exists='append'):
    
    if flavor=='mysql':
        symbol = '%s'            
    elif flavor=='sqlite':
        symbol = '?'
      
    db_create_table(conn, tbl, cols, dtypes, flavor, if_exists)
      
    vals = ((symbol+',')*len(rows[0]))[:-1]
    sql = """INSERT INTO {} {} VALUES ({})""".format(tbl, tuple(cols), vals)
    conn.executemany(sql, rows)
    conn.commit()
    
def df_to_sql(conn, df, tbl, dtypes, flavor='sqlite', if_exists='append', index=True):
    
    if index:
        cols = list(df.index.names) + list(df.columns)
        rows = []
        for idx_vals, row in df.iterrows():
            idx = []
            for idx_val in idx_vals:
                try:
                    i = idx_val.strftime('%Y-%m-%d')
                except:
                    i = idx_val
                idx.append(i)
            rows.append(idx + list(row.values))
    else:
        cols = list(df.columns)
        rows = [list(row.values) for i, row in df.iterrows]
    
    db_insert_many(conn, tbl, cols, rows, dtypes, flavor, if_exists='append')
    