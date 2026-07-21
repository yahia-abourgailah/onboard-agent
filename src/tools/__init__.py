from tools.navigation_tool import get_office_directions
from tools.sql_tool import query_sql_db
from tools.vector_tool import query_vector_db

tools = [query_vector_db, query_sql_db, get_office_directions]
