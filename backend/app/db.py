from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()


def build_database_connect_args(
    database_url: str,
    *,
    require_tls: bool = False,
    tls_mode: str = "require",
    tls_root_cert: str | None = None,
):
    """预留 database_url 形参与 create_app 对齐；当前连接参数仅由 TLS 开关决定。"""
    connect_args: dict = {}
    if require_tls:
        connect_args["sslmode"] = tls_mode
        if tls_root_cert:
            connect_args["sslrootcert"] = tls_root_cert
    return connect_args


def build_engine(database_url: str, connect_args: dict | None = None):
    return create_engine(database_url, future=True, connect_args=connect_args or {})


def build_session_factory(database_url: str, connect_args: dict | None = None):
    engine = build_engine(database_url, connect_args=connect_args)
    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
