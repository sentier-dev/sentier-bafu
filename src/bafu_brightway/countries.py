"""The factors of single countries, read from sentier-methods.

sentier-methods holds, beside each method's factors without a location, factors of single
countries: for water use mostly, and for land use. The installer's reader of the methods
(``sentier_brightway.methods``) leaves them out. They are read here, from the same file, so
that a flow that names a country can take its country's factor (``located.py``)."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

import pandas as pd
from sentier_brightway._frames import codes_from_iris, data_root_error, require_columns
from sentier_brightway.constants import METHODS_FOLDER, REPO_METHODS
from sentier_brightway.methods import CF_COLUMNS

FILE = "characterization-factors.parquet"


def load_factors_of_countries(data_root: Path) -> Mapping[str, Mapping[tuple[str, str], float]]:
    """``{method id: {(EF flow code, location): factor}}``; a method without a factor of a
    single country is left out."""
    path = Path(data_root) / REPO_METHODS / "data" / METHODS_FOLDER / FILE
    if not path.is_file():
        raise data_root_error(FILE, path)
    cfs = pd.read_parquet(path)
    require_columns(cfs, CF_COLUMNS, path)
    located = cfs[cfs["location"].notna()]
    doubled = located.duplicated(subset=["method_id", "flow", "location"], keep=False)
    if doubled.any():
        triples = list(
            located.loc[doubled, ["method_id", "flow", "location"]]
            .drop_duplicates()
            .itertuples(index=False, name=None)
        )
        raise ValueError(
            f"{path}: duplicate (method_id, flow, location) among the characterization "
            f"factors of single countries: {triples[:5]}"
        )
    located = located.assign(
        code=codes_from_iris(located["flow"].astype(str), path),
        factor_value=located["factor_value"].astype(float),
        location=located["location"].astype(str),
    )
    return MappingProxyType(
        {
            str(method_id): MappingProxyType(
                {
                    (str(code), str(location)): float(value)
                    for code, location, value in zip(
                        rows["code"], rows["location"], rows["factor_value"], strict=True
                    )
                }
            )
            for method_id, rows in located.groupby("method_id", sort=False)
        }
    )
