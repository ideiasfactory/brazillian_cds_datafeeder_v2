import os
import io
import time
import re
import sys
import logging
import asyncio
from datetime import datetime, date as date_type
from typing import Optional

import pandas as pd
import requests
from lxml import html as lxhtml
from requests.adapters import HTTPAdapter, Retry

from loguru import logger
from logtail import LogtailHandler  # logtail-python package

from dotenv import load_dotenv
load_dotenv()

# Import database and CSV sources
from src.config import settings
from src.database.connection import get_async_session
from src.database.repositories.cds_repository import CDSRepository
from src.database.csv_source import CSVDataSource

# BetterStack (Logtail) integration
# Initialization moved into setup_logging() to delay import until logging setup.
BETTERSTACK_TOKEN = os.getenv("BETTERSTACK_SOURCE_TOKEN")
BETTERSTACK_HOST = os.getenv("BETTERSTACK_INGESTING_HOST", "in.logtail.com")
HAS_BETTERSTACK = False  # setup_logging() will attempt import and update this flag

# Configuration from environment variables
INVESTING_URL = os.getenv("INVESTING_URL", "https://br.investing.com/rates-bonds/brazil-cds-5-years-usd-historical-data")
CSV_PATH = os.getenv("CSV_OUTPUT_PATH", "data/brasil_CDS_historical.csv")
TABLE_XPATH = os.getenv("TABLE_XPATH", "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/div[3]/table")

# HTTP Request Configuration
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))
REQUEST_RETRIES = int(os.getenv("REQUEST_RETRIES", "3"))
REQUEST_BACKOFF_FACTOR = float(os.getenv("REQUEST_BACKOFF_FACTOR", "0.8"))

HEADERS = {
    "User-Agent": os.getenv("USER_AGENT", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                          "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": os.getenv("ACCEPT_LANGUAGE", "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"),
    "Referer": "https://br.investing.com/",
}

def _requests_session_with_retries(total=None, backoff_factor=None) -> requests.Session:
    if total is None:
        total = REQUEST_RETRIES
    if backoff_factor is None:
        backoff_factor = REQUEST_BACKOFF_FACTOR
    
    s = requests.Session()
    retries = Retry(
        total=total,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"]
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s

def _clean_number(s: str) -> Optional[float]:
    if s is None:
        return None
    s = str(s).strip()
    if s == "" or s.lower() in {"nan", "none", "null", "-"}:
        return None
    # troca vírgula por ponto (pt-BR)
    s = s.replace(".", "").replace(",", ".")  # "1.234,56" -> "1234.56"
    # remove % se houver
    s = s.replace("%", "")
    try:
        return float(s)/100
    except ValueError:
        return None

def _parse_change_pct(s: str) -> Optional[float]:
    # Mantém o sinal corretamente e remove o '%'
    if s is None:
        return None
    s = s.strip().replace(" ", "")
    s = s.replace("%", "")
    # vírgula decimal -> ponto
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        # tenta capturar algo como "+1.56%" já sem %, mas com unicode
        m = re.search(r"([+-]?\d+(?:\.\d+)?)", s)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                return None
        return None

def fetch_html(url: str) -> str:
    session = _requests_session_with_retries()
    r = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.text

def parse_table_with_read_html(page_html: str) -> Optional[pd.DataFrame]:
    # tenta puxar a primeira tabela que tenha cabeçalhos de interesse
    try:
        tables = pd.read_html(io.StringIO(page_html))
    except ValueError:
        return None

    candidates = []
    for t in tables:
        cols = [str(c).lower() for c in t.columns]
        if any("data" in c for c in cols) and (
            any("último" in c for c in cols) or any("ultimo" in c for c in cols) or any("close" in c for c in cols)
        ):
            candidates.append(t)

    if not candidates:
        return None

    # Pega a primeira candidata
    df = candidates[0].copy()
    return _normalize_investing_table(df)

def parse_table_with_xpath(page_html: str) -> Optional[pd.DataFrame]:
    try:
        root = lxhtml.fromstring(page_html)
        tables = root.xpath(TABLE_XPATH)
        if not tables:
            return None
        table_el = tables[0]

        # Extrai cabeçalhos
        headers = [("".join(th.itertext())).strip() for th in table_el.xpath(".//thead//th")]
        rows = []
        for tr in table_el.xpath(".//tbody//tr"):
            cells = [("".join(td.itertext())).strip() for td in tr.xpath("./td")]
            if cells:
                rows.append(cells)
        if not headers or not rows:
            return None

        df = pd.DataFrame(rows, columns=headers)
        return _normalize_investing_table(df)
    except Exception as e:
        logger.error(f"Falha no parsing por XPath: {e}")
        return None

def _normalize_investing_table(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    # normaliza nomes de coluna
    lower_cols = {c: str(c).strip().lower() for c in df.columns}
    df.rename(columns=lower_cols, inplace=True)

    # mapeia colunas esperadas
    # em pt: data, último, abertura, máxima, mínima, var%
    # em en pode vir: date, price/last, open, high, low, change %
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if "data" in cl or "date" in cl:
            col_map[c] = "date"
        elif "abert" in cl or "open" in cl:
            col_map[c] = "open"
        elif "máxima" in cl or "maxima" in cl or "high" in cl:
            col_map[c] = "high"
        elif "mínima" in cl or "minima" in cl or "low" in cl:
            col_map[c] = "low"
        elif "último" in cl or "ultimo" in cl or "close" in cl or "price" in cl or "fech" in cl:
            col_map[c] = "close"
    
        elif "var" in cl and "%" in cl:
            col_map[c] = "change_pct"

    df.rename(columns=col_map, inplace=True)

    expected = ["date", "open", "high", "low", "close","change_pct"]
    # mantém apenas as que temos
    keep = [c for c in expected if c in df.columns]
    df = df[keep].copy()

    # converte tipos
    # datas vêm em "dd.mm.yyyy" no HTML que você colou (e podem vir "dd/mm/yyyy" em outras versões)
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True, format=None)
    if "close" in df.columns:
        df["close"] = df["close"].apply(_clean_number)
    if "open" in df.columns:
        df["open"] = df["open"].apply(_clean_number)
    if "high" in df.columns:
        df["high"] = df["high"].apply(_clean_number)
    if "low" in df.columns:
        df["low"] = df["low"].apply(_clean_number)
    if "change_pct" in df.columns:
        df["change_pct"] = df["change_pct"].apply(_parse_change_pct)

    # ordena colunas para formato OHLC
    col_order = ['date', 'open', 'high', 'low', 'close', 'change_pct']
    df = df[[c for c in col_order if c in df.columns]]
    
    # remove linhas sem data ou sem preço
    df = df.dropna(subset=["date"])
    if "close" in df.columns:
        df = df.dropna(subset=["close"])

    # ordena do mais antigo para o mais recente (facilita merges)
    df = df.sort_values("date").reset_index(drop=True)
    return df

def fetch_investing_cds() -> pd.DataFrame:
    logger.info("Baixando página do Investing…")
    html = fetch_html(INVESTING_URL)

    # 1) tenta read_html
    df = parse_table_with_read_html(html)
    if df is not None and not df.empty:
        logger.success(f"Tabela capturada com read_html: {len(df)} linhas.")
        return df

    # 2) fallback: XPath
    logger.warning("read_html não encontrou a tabela; tentando XPath…")
    df = parse_table_with_xpath(html)
    if df is not None and not df.empty:
        logger.success(f"Tabela capturada com XPath: {len(df)} linhas.")
        logger.info(df.head(3).to_string())
        return df

    raise RuntimeError("Não foi possível capturar a tabela do Investing.")

def load_existing_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        logger.warning(f"CSV inexistente em {path}; iniciando base vazia.")
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "change_pct"])
    df = pd.read_csv(path)
    # normaliza
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

def merge_and_dedup(old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    if old is None or old.empty:
        merged = new.copy()
    else:
        merged = pd.concat([old, new], ignore_index=True)
    # remove duplicatas por data (mantém a última ocorrência)
    merged = merged.drop_duplicates(subset=["date"], keep="last")
    merged = merged.sort_values("date").reset_index(drop=True)
    return merged

def backup_file(path: str):
    if os.path.exists(path):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bkp = f"{os.path.splitext(path)[0]}__bkp_{ts}.csv"
        try:
            import shutil
            shutil.copy2(path, bkp)
            logger.info(f"Backup criado: {bkp}")
        except Exception as e:
            logger.warning(f"Falha ao criar backup: {e}")

def _build_ingest_url(host: str) -> str:
    """Return a proper HTTPS URL for Logtail ingestion based on provided host.

    Accepts either full URL (https://example) or bare host (example). Ensures
    we return an https URL without trailing slash.
    """
    if not host:
        return "https://in.logtail.com"
    h = host.strip()
    if not h.startswith("http://") and not h.startswith("https://"):
        h = f"https://{h}"
    return h.rstrip("/")
def setup_logging():
    """Configure loguru to log to console and forward to BetterStack when configured."""
    # Reset sinks and add console sink
    logger.remove()
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.add(
        sys.stdout,
        level=log_level,
        enqueue=True,
        backtrace=False,
        diagnose=False,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )

    # Try lazy import of BetterStack (logtail) and set flag so subsequent code knows availability.
    global HAS_BETTERSTACK
    try:
        
        HAS_BETTERSTACK = True
    except Exception:
        logtail_handler = None
        HAS_BETTERSTACK = False

    # BetterStack forwarding
    if HAS_BETTERSTACK and BETTERSTACK_TOKEN:
        try:
            ingest_url = _build_ingest_url(BETTERSTACK_HOST)
            logtail_handler = LogtailHandler(
                source_token=BETTERSTACK_TOKEN,
                host=ingest_url,
            )

            level_map = {
                "TRACE": logging.DEBUG,
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "SUCCESS": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "CRITICAL": logging.CRITICAL,
            }

            def betterstack_sink(message):
                rec = message.record
                lvl = level_map.get(rec["level"].name, logging.INFO)
                try:
                    log_record = logging.LogRecord(
                        name="loguru",
                        level=lvl,
                        pathname=rec["file"].path,
                        lineno=rec["line"],
                        msg=rec["message"],
                        args=(),
                        exc_info=None,
                    )
                    # Set created timestamp
                    log_record.created = rec["time"].timestamp()
                    log_record.funcName = rec["function"]
                    logtail_handler.emit(log_record)
                except Exception:
                    # Never break the app due to logging failure
                    pass

            logger.add(betterstack_sink, level="INFO")
            logger.info(f"BetterStack forwarding enabled -> {ingest_url}")
        except Exception as e:
            logger.warning(f"BetterStack setup failed: {e}")
    else:
        if not HAS_BETTERSTACK:
            logger.debug("BetterStack library not installed (pip install logtail-python)")
        elif not BETTERSTACK_TOKEN:
            logger.debug("BetterStack not configured (BETTERSTACK_SOURCE_TOKEN not set)")
            logger.debug("BetterStack not configured (BETTERSTACK_SOURCE_TOKEN not set)")

def main():
    """Main function - entry point for sync execution."""
    asyncio.run(async_main())

async def async_main():
    """Async main function - handles data fetch and storage."""
    # Configure logging (console + BetterStack)
    setup_logging()

    # Determine if using database or CSV
    use_database = bool(settings.database_url and settings.environment == "production")
    
    if use_database:
        logger.info("Using database storage (production mode)")
    else:
        logger.info("Using CSV storage (development mode)")

    try:
        df_new = fetch_investing_cds()
        logger.info(f"Fetched {len(df_new)} records from Investing.com")
    except Exception as e:
        logger.error(f"Falha ao capturar a tabela do Investing: {e}")
        return

    if use_database:
        # Database mode
        await save_to_database(df_new)
    else:
        # CSV mode
        save_to_csv(df_new)

async def save_to_database(df_new: pd.DataFrame) -> None:
    """Save data to database using repository."""
    try:
        async with get_async_session() as session:
            repo = CDSRepository(session)
            
            # Convert DataFrame to list of dicts
            records = []
            for _, row in df_new.iterrows():
                record = {
                    "date": row["date"].date() if isinstance(row["date"], pd.Timestamp) else row["date"],
                    "open": float(row["open"]) if pd.notna(row["open"]) else None,
                    "high": float(row["high"]) if pd.notna(row["high"]) else None,
                    "low": float(row["low"]) if pd.notna(row["low"]) else None,
                    "close": float(row["close"]) if pd.notna(row["close"]) else None,
                    "change_pct": float(row["change_pct"]) if pd.notna(row["change_pct"]) else None,
                }
                records.append(record)
            
            # Bulk insert with upsert
            result = await repo.bulk_insert(records, source="investing.com", skip_duplicates=False)
            
            # Log the update
            await repo.log_update(
                status="success",
                records_fetched=len(df_new),
                records_inserted=result["inserted"],
                records_updated=result["updated"],
                source="investing.com"
            )
            
            logger.success(
                f"Database updated: {result['inserted']} inserted, "
                f"{result['updated']} updated, {result['skipped']} skipped"
            )
            
            # Show statistics
            stats = await repo.get_statistics()
            logger.info(
                f"Database statistics: {stats['total_records']} total records, "
                f"date range: {stats['earliest_date']} to {stats['latest_date']}"
            )
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        # Try to log the error
        try:
            async with get_async_session() as session:
                repo = CDSRepository(session)
                await repo.log_update(
                    status="error",
                    records_fetched=len(df_new),
                    source="investing.com",
                    error_message=str(e)
                )
        except Exception:
            pass
        raise

def save_to_csv(df_new: pd.DataFrame) -> None:
    """Save data to CSV using CSVDataSource."""
    try:
        csv_source = CSVDataSource(CSV_PATH)
        
        # Convert DataFrame to list of dicts
        records = []
        for _, row in df_new.iterrows():
            record = {
                "date": row["date"].date() if isinstance(row["date"], pd.Timestamp) else row["date"],
                "open": float(row["open"]) if pd.notna(row["open"]) else None,
                "high": float(row["high"]) if pd.notna(row["high"]) else None,
                "low": float(row["low"]) if pd.notna(row["low"]) else None,
                "close": float(row["close"]) if pd.notna(row["close"]) else None,
                "change_pct": float(row["change_pct"]) if pd.notna(row["change_pct"]) else None,
            }
            records.append(record)
        
        # Bulk insert
        backup_file(CSV_PATH)
        result = csv_source.bulk_insert(records, source="investing.com", skip_duplicates=False)
        
        logger.success(
            f"CSV updated: {result['inserted']} inserted, "
            f"{result['updated']} updated, {result['skipped']} skipped"
        )
        
        # Show statistics
        stats = csv_source.get_statistics()
        logger.info(
            f"CSV statistics: {stats['total_records']} total records, "
            f"date range: {stats['earliest_date']} to {stats['latest_date']}"
        )
    except Exception as e:
        logger.error(f"Error saving to CSV: {e}")
        raise

if __name__ == "__main__":
    main()
