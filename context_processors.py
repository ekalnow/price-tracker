from datetime import datetime

def inject_now():
    """
    Inject the current datetime into all templates
    """
    return {'now': datetime.utcnow()}

def inject_app_name():
    """
    Inject the application name and version
    """
    return {
        'app_name': 'E-commerce Price Monitor',
        'app_version': '1.0.0'
    }

def register_context_processors(app):
    """
    Register all context processors with the Flask app
    """
    @app.context_processor
    def utility_processor():
        context = {}
        context.update(inject_now())
        context.update(inject_app_name())
        return context
