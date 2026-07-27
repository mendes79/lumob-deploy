# database/cache_ext.py
# Instância compartilhada do Flask-Caching. Fica separada de app.py pra evitar
# import circular (managers precisam de `cache`, app.py importa os managers).

from flask_caching import Cache

cache = Cache()
