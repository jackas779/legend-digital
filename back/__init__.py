"""Conector de MySQL: PyMySQL en lugar de mysqlclient.

mysqlclient necesita compilarse en Windows con Python 3.14 (requiere las
Build Tools de C++). PyMySQL es puro Python: se instala con pip en cualquier
versión y se registra como ``MySQLdb``, que es el módulo que busca Django.

Django exige mysqlclient >= 2.2.1 y PyMySQL se anuncia con otra
numeración, así que se declara una versión compatible. Con SQLite (sin
DB_PASSWORD en el .env) esto no se usa.
"""

try:
    import pymysql
except ImportError:  # Sin PyMySQL instalado se usa mysqlclient si existe.
    pass
else:
    pymysql.version_info = (2, 2, 7, 'final', 0)
    pymysql.install_as_MySQLdb()
