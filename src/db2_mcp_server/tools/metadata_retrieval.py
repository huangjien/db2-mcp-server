import ibm_db


class MetadataRetrievalTool:
  def __init__(self, connection_string):
    self.connection_string = connection_string

  def get_table_metadata(self, table_name):
    conn = ibm_db.connect(self.connection_string, "", "")
    query = f"SELECT * FROM SYSCAT.COLUMNS WHERE TABNAME = '{table_name}'"
    stmt = ibm_db.exec_immediate(conn, query)
    result = []
    row = ibm_db.fetch_assoc(stmt)
    while row:
      result.append(row)
      row = ibm_db.fetch_assoc(stmt)
    ibm_db.close(conn)
    return result
