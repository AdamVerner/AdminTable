from ._base import BaseWrapper


class FlaskWrapper(BaseWrapper):
    """
    Creates an extension which can be used with flask

    ```python
    from flask import Flask
    from admin_table import table_api, FlaskWrapper

    at = admin_table()
    app = Flask(__name__)

    at_app = FlaskWrapper(ta)
    at_app.init_app(app)

    app.run()

    ```
    """

    def __init__(self, admin_table):
        super().__init__(admin_table)
        raise NotImplementedError()
