from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from datacore.config import STAGING_DB_DSN
from datacore.storage.staging.models import metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# DSN unique : lu depuis .env via datacore.config (python-dotenv),
# plutôt que codé en dur dans alembic.ini -- une seule source de vérité
# pour la chaîne de connexion à la base de staging.
config.set_main_option("sqlalchemy.url", STAGING_DB_DSN)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Métadonnées des tables gérées par Alembic (C11) : voir
# src/datacore/storage/staging/models.py. Les tables FluxPro
# (schema.sql, issue #7) et historique_expeditions (C9) restent en
# dehors du périmètre Alembic -- elles sont importées telles quelles
# depuis des schémas déjà fournis/créés, pas modélisées par nous.
target_metadata = metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
