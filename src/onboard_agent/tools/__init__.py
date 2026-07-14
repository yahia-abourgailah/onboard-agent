from onboard_agent.tools.sql_tool import query_sql_db
from onboard_agent.tools.vector_tool import query_vector_db

tools = [query_vector_db, query_sql_db]
