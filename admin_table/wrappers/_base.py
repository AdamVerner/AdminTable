from admin_table import AdminTable


class BaseWrapper:
    admin_table: AdminTable

    def __init__(self, admin_table: AdminTable):
        self.admin_table = admin_table

    def on_startup(self, app_url):
        print(f"Table api ({self.admin_table.config.name} running on: ", app_url)

    def on_shutdown(self):
        print("Table api shutting down")
