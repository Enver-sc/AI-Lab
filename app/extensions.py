from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Neue nullable EcoLogits-Spalten auf provider_configuration. db.create_all() legt nur
# fehlende Tabellen an, keine fehlenden Spalten auf bestehenden Tabellen -- ohne
# Migrationswerkzeug (z. B. Flask-Migrate) uebernimmt diese Funktion das minimal noetige
# ALTER TABLE, damit eine schon existierende instance/gateway.db weiterhin startet.
_PROVIDER_CONFIGURATION_NEW_COLUMNS = {
    "ecologits_provider": "VARCHAR(40)",
    "eco_active_params_b": "FLOAT",
    "eco_total_params_b": "FLOAT",
    "eco_datacenter_pue": "FLOAT",
    "eco_datacenter_wue": "FLOAT",
    "eco_electricity_mix_zone": "VARCHAR(3)",
}


def ensure_schema_upgrades(app):
    with app.app_context():
        engine = db.engine
        if engine.dialect.name != "sqlite":
            return
        with engine.connect() as conn:
            existing = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(provider_configuration)")}
            for name, column_type in _PROVIDER_CONFIGURATION_NEW_COLUMNS.items():
                if name not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE provider_configuration ADD COLUMN {name} {column_type}")
            conn.commit()

