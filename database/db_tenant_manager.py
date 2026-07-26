# database/db_tenant_manager.py

class TenantManager:
    """
    Resolve o tenant a partir do subdomínio. Não herda TenantScopedManager —
    é quem descobre o tenant, não pode depender de um tenant_id que ainda não existe.
    """
    def __init__(self, db):
        self.db = db

    def find_by_subdomain(self, subdomain):
        query = "SELECT id, subdomain, nome_fantasia, ativo FROM tenants WHERE subdomain = %s"
        result = self.db.execute_query(query, (subdomain,), fetch_results=True)
        return result[0] if result else None
