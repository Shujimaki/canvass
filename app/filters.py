from datetime import datetime

def register_filters(app):
    @app.template_filter("format_date")
    def format_date(value, fmt="%B %d, %Y"):
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
            return dt.strftime(fmt)
        except Exception:
            return value