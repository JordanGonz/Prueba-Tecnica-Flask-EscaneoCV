import os
import json
import logging
from flask import Flask
from urllib.parse import urlparse
from werkzeug.middleware.proxy_fix import ProxyFix

# Importa la instancia única de SQLAlchemy
from extensions import db
from routes import routes_bp

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

# Crear la aplicación Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configurar base de datos
database_url = os.environ.get("DATABASE_URL", "sqlite:///recruitment.db")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {} if database_url.startswith("sqlite") else {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_timeout": 20,
    "max_overflow": 0,
    "connect_args": {
        "sslmode": "prefer",
        "connect_timeout": 10,
    }
}

# Configurar carpeta de carga de archivos
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB
app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Inicializar extensiones
db.init_app(app)

# Crear tablas dentro del contexto de la app
with app.app_context():
    import models  # Asegúrate que models.py use: from extensions import db
    db.create_all()

# Registrar rutas
app.register_blueprint(routes_bp)

# Filtro Jinja personalizado
@app.template_filter('from_json')
def from_json_filter(value):
    try:
        if isinstance(value, str) and value.strip().startswith('['):
            return json.loads(value)
        return []
    except (json.JSONDecodeError, TypeError, ValueError):
        return []

# Ejecutar la aplicación
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
