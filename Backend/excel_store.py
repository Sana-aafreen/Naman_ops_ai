"""
excel_store.py — Excel-backed datastore for NamanDarshan.

Provides:
  - `store` singleton used by routes/tools
  - search helpers for Pandits / Hotels / Cabs / Temples sheets

The Excel file path is configured via `config.EXCEL_PATH`.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from config import EXCEL_PATH

log = logging.getLogger("nd.excel")


def _norm_key(name: str) -> str:
    return (name or "").strip().lower()


def _truthy_yes(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"yes", "y", "true", "1", "available", "open"}


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value)


def _df_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if df is None or df.empty:
        return []
    clean = df.where(pd.notnull(df), None)
    return clean.to_dict(orient="records")


class ExcelDataStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._frames: Dict[str, pd.DataFrame] = {}
        self._name_by_norm: Dict[str, str] = {}
        self.sheets: List[str] = []
        self.reload()

    # --------------------------------------------------

    def reload(self) -> Dict[str, int]:
        self._frames.clear()
        self._name_by_norm.clear()
        self.sheets = []

        if not self.path.exists():
            log.warning("Excel file not found: %s", self.path)
            return {}

        data = pd.read_excel(self.path, sheet_name=None, engine="openpyxl")

        counts: Dict[str, int] = {}
        for sheet_name, df in data.items():
            if df is None:
                continue
            self._frames[sheet_name] = df
            self._name_by_norm[_norm_key(sheet_name)] = sheet_name
            counts[sheet_name] = int(len(df.index))

        self.sheets = list(self._frames.keys())
        return counts

    # --------------------------------------------------

    def _get_df(self, sheet: str) -> Optional[pd.DataFrame]:
        if not sheet:
            return None
        key = _norm_key(sheet)
        actual = self._name_by_norm.get(key)
        if not actual:
            return None
        return self._frames.get(actual)

    def get_all(self, sheet: str) -> List[Dict[str, Any]]:
        df = self._get_df(sheet)
        return _df_records(df) if df is not None else []

    # --------------------------------------------------

    def _filter_city(self, df: pd.DataFrame, city: Optional[str]) -> pd.DataFrame:
        if df is None or not city:
            return df
        city = city.strip()
        if not city:
            return df

        for col in ("Location", "City", "Town"):
            if col in df.columns:
                series = df[col].astype(str)
                return df[series.str.contains(city, case=False, na=False)]
        return df

    def _filter_available(self, df: pd.DataFrame, available_only: Optional[bool]) -> pd.DataFrame:
        if df is None or not available_only:
            return df
        if "Available" not in df.columns:
            return df
        return df[df["Available"].apply(_truthy_yes)]

    # --------------------------------------------------
    # SEARCH
    # --------------------------------------------------

    def search_pandits(
        self,
        name: Optional[str] = None,
        city: Optional[str] = None,
        specialization: Optional[str] = None,
        available_only: Optional[bool] = None,
        max_price: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        df = self._get_df("Pandits")
        if df is None or df.empty:
            return []

        df = self._filter_city(df, city)
        df = self._filter_available(df, available_only)

        if name:
            if "Name" in df.columns:
                df = df[df["Name"].astype(str).str.contains(name, case=False, na=False)]

        if specialization:
            for col in ("Expertise", "Specialization", "Skill"):
                if col in df.columns:
                    df = df[df[col].astype(str).str.contains(specialization, case=False, na=False)]
                    break

        if max_price is not None:
            for col in ("Price", "Rate", "Fee", "Cost"):
                if col in df.columns:
                    df = df[pd.to_numeric(df[col], errors="coerce") <= float(max_price)]
                    break

        return _df_records(df)

    def search_hotels(
        self,
        city: Optional[str] = None,
        max_price: Optional[float] = None,
        min_stars: Optional[int] = None,
        available_only: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        df = self._get_df("Hotels")
        if df is None or df.empty:
            return []

        df = self._filter_city(df, city)
        df = self._filter_available(df, available_only)

        if max_price is not None:
            for col in ("Price", "Rate", "PerNight", "Cost"):
                if col in df.columns:
                    df = df[pd.to_numeric(df[col], errors="coerce") <= float(max_price)]
                    break

        if min_stars is not None:
            for col in ("Stars", "Rating"):
                if col in df.columns:
                    df = df[pd.to_numeric(df[col], errors="coerce") >= int(min_stars)]
                    break

        return _df_records(df)

    def search_cabs(
        self,
        city: Optional[str] = None,
        min_capacity: Optional[int] = None,
        available_only: Optional[bool] = None,
        ac_required: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        df = self._get_df("Cabs")
        if df is None or df.empty:
            return []

        df = self._filter_city(df, city)
        df = self._filter_available(df, available_only)

        if min_capacity is not None:
            for col in ("Capacity", "Seats", "Seating"):
                if col in df.columns:
                    df = df[pd.to_numeric(df[col], errors="coerce") >= int(min_capacity)]
                    break

        if ac_required:
            for col in ("AC", "AirConditioned"):
                if col in df.columns:
                    df = df[df[col].apply(_truthy_yes)]
                    break

        return _df_records(df)

    def get_temple_info(
        self,
        name: Optional[str] = None,
        city: Optional[str] = None,
        deity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        df = self._get_df("Temples")
        if df is None or df.empty:
            return []

        df = self._filter_city(df, city)

        if name:
            for col in ("Name", "Temple", "TempleName"):
                if col in df.columns:
                    df = df[df[col].astype(str).str.contains(name, case=False, na=False)]
                    break

        if deity:
            for col in ("Deity", "God", "MainDeity"):
                if col in df.columns:
                    df = df[df[col].astype(str).str.contains(deity, case=False, na=False)]
                    break

        return _df_records(df)

    # --------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        stats: Dict[str, Any] = {}
        for sheet in self.sheets:
            df = self._frames.get(sheet)
            if df is None:
                continue
            sheet_stats: Dict[str, Any] = {
                "count": int(len(df.index)),
                "columns": list(df.columns),
            }
            if "Available" in df.columns:
                sheet_stats["available_count"] = int(df["Available"].apply(_truthy_yes).sum())
            stats[sheet] = sheet_stats
        return stats


# Global singleton used by routes/tools
store = ExcelDataStore(EXCEL_PATH)
