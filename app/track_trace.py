"""Standalone, local Track & Trace components. No production/GMP qualification implied."""
from __future__ import annotations
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

GS = '\x1d'

def parse_gs1(data: str) -> dict:
    """Parse a supported GS1 subset: (01) GTIN14, (17) YYMMDD, (10) lot, (21) serial.

    Parenthesized human-readable notation and scanner FNC1/GS-delimited data are supported.
    Other Application Identifiers require additional specification-aware handling.
    """
    import re
    result = {}
    keys = {'01': 'gtin', '17': 'expiry_yymmdd', '10': 'lot', '21': 'serial'}
    if '(' in data:
        parts = re.findall(r'\((01|17|10|21)\)([^()]*)', data)
        for ai, val in parts:
            value = val.strip()
            if ai in ('01', '17'):
                limit = 14 if ai == '01' else 6
                if not value.isdigit() or len(value) != limit:
                    raise ValueError(f'Invalid AI {ai} length or format')
            elif not 1 <= len(value) <= 20:
                raise ValueError(f'Invalid variable-length AI {ai}')
            result[keys[ai]] = value
    else:
        i = 0
        if data.startswith(']d2'):
            i = 3
        while i < len(data):
            if data[i] == GS:
                i += 1
                continue
            ai = data[i:i+2]
            if ai not in keys:
                raise ValueError(f'Unsupported GS1 AI at offset {i}: {ai!r}')
            i += 2
            if ai in ('01','17'):
                length = 14 if ai == '01' else 6
                value = data[i:i+length]
                if len(value) != length or not value.isdigit():
                    raise ValueError(f'Invalid fixed-length AI {ai}')
                i += length
            else:
                end = data.find(GS, i)
                if end == -1:
                    end = len(data)
                value = data[i:end]
                if not 1 <= len(value) <= 20:
                    raise ValueError(f'Invalid variable-length AI {ai}')
                i = end
            result[keys[ai]] = value
    if not result:
        raise ValueError('No supported GS1 application identifiers')
    return result


def check_gs1_against_print(gs1: dict, printed: dict) -> dict:
    """Compare only semantically equivalent fields; absent fields remain unverified."""
    comparisons = {}
    pairs = [('gtin', 'gtin'), ('lot', 'batch'), ('serial', 'serial')]
    for encoded_key, printed_key in pairs:
        encoded = gs1.get(encoded_key)
        observed = printed.get(printed_key)
        comparisons[encoded_key] = ('MATCH' if encoded and observed and str(encoded).upper() == str(observed).upper()
                                    else 'MISMATCH' if encoded and observed else 'NOT_VERIFIED')
    if gs1.get('expiry_yymmdd'):
        datecode = gs1['expiry_yymmdd']
        yearmonth = f'20{datecode[:2]}-{datecode[2:4]}'
        printed_exp = printed.get('expiry')
        comparisons['expiry'] = ('MATCH' if printed_exp and (printed_exp == yearmonth or printed_exp == f'{yearmonth}-{datecode[4:]}')
                                 else 'MISMATCH' if printed_exp else 'NOT_VERIFIED')
    return comparisons


def init_database(db_path: str | Path) -> None:
    with sqlite3.connect(db_path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS inspections (id INTEGER PRIMARY KEY, ts_utc TEXT NOT NULL, filename TEXT, status TEXT, elapsed_ms REAL, evidence_json TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS serial_units (serial TEXT PRIMARY KEY, gtin TEXT NOT NULL, lot TEXT, parent TEXT, registered_utc TEXT NOT NULL)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_units_parent ON serial_units(parent)')


def save_inspection(db_path: str | Path, record: dict) -> int:
    init_database(db_path)
    with sqlite3.connect(db_path) as db:
        cursor = db.execute('INSERT INTO inspections (ts_utc, filename, status, elapsed_ms, evidence_json) VALUES (?,?,?,?,?)',
            (datetime.now(timezone.utc).isoformat(), record.get('filename'), 'PASS' if record.get('passed') else 'REVIEW',
             record.get('processing_ms'), json.dumps(record, default=str)))
        return int(cursor.lastrowid)


def register_unit(db_path: str | Path, serial: str, gtin: str, lot: str = '') -> None:
    if not serial or not gtin:
        raise ValueError('serial and GTIN required')
    init_database(db_path)
    with sqlite3.connect(db_path) as db:
        db.execute('INSERT INTO serial_units(serial, gtin, lot, parent, registered_utc) VALUES (?,?,?,?,?)',
                   (serial, gtin, lot, None, datetime.now(timezone.utc).isoformat()))


def aggregate_units(db_path: str | Path, parent: str, child_serials: list[str]) -> None:
    """Attach registered children under a registered parent; reject reparenting/cycles."""
    if not child_serials or len(child_serials) != len(set(child_serials)) or parent in child_serials:
        raise ValueError('Invalid children or self-aggregation')
    init_database(db_path)
    with sqlite3.connect(db_path) as db:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute('SELECT 1 FROM serial_units WHERE serial=?', (parent,)).fetchone():
            raise ValueError('Parent serial is not registered')
        for child in child_serials:
            row = db.execute('SELECT parent FROM serial_units WHERE serial=?', (child,)).fetchone()
            if row is None or row[0] is not None:
                raise ValueError(f'Child {child} not registered or already aggregated')
            # Walk ancestors of parent: prevents cycles even with previously nested levels.
            ancestor = parent
            while ancestor is not None:
                if ancestor == child:
                    raise ValueError('Aggregation cycle detected')
                current = db.execute('SELECT parent FROM serial_units WHERE serial=?', (ancestor,)).fetchone()
                ancestor = current[0] if current else None
        for child in child_serials:
            db.execute('UPDATE serial_units SET parent=? WHERE serial=?', (parent, child))


def children_of(db_path: str | Path, serial: str) -> list[str]:
    init_database(db_path)
    with sqlite3.connect(db_path) as db:
        return [row[0] for row in db.execute('SELECT serial FROM serial_units WHERE parent=? ORDER BY serial', (serial,))]
