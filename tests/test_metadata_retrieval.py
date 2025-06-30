import unittest
from unittest.mock import patch
from src.db2_mcp_server.tools.metadata_retrieval import MetadataRetrievalTool


class TestMetadataRetrievalTool(unittest.TestCase):
  def setUp(self):
    # Mock connection string for testing
    self.connection_string = "DATABASE=sample;HOSTNAME=localhost;PORT=50000;PROTOCOL=TCPIP;UID=user;PWD=password;"
    self.tool = MetadataRetrievalTool(self.connection_string)

  @patch("src.db2_mcp_server.tools.metadata_retrieval.ibm_db")
  def test_get_table_metadata(self, mock_ibm_db):
    # Mock table name
    table_name = "SAMPLE_TABLE"
    # Mock expected result
    expected_result = [
      {"COLNAME": "ID", "TYPENAME": "INTEGER"},
      {"COLNAME": "NAME", "TYPENAME": "VARCHAR"},
    ]
    # Mock the ibm_db functions to return expected results
    mock_ibm_db.execute.return_value = True
    mock_ibm_db.fetch_assoc.side_effect = expected_result + [None]

    result = self.tool.get_table_metadata(table_name)
    self.assertEqual(result, expected_result)


if __name__ == "__main__":
  unittest.main()
