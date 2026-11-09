"""Cálculo transparente de indicadores de sprints Agile Scrum, somente a partir de dados reais."""
from __future__ import annotations

import numpy as np
import pandas as pd


def project_summary(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    stats = (
        frame.groupby("projeto", as_index=False)
        .agg(
            sprints=("sprint_id", "count"),
            total_entregas=("tarefas_concluidas", "sum"),
            media_entregas=("tarefas_concluidas", "mean"),
            min_entregas=("tarefas_concluidas", "min"),
            max_entregas=("tarefas_concluidas", "max"),
            pontos_totais=("pontos_concluidos", lambda s: s.sum(min_count=1)),
            velocidade_media=("pontos_concluidos", "mean"),
            total_vinculos=("total_vinculos", lambda s: s.sum(min_count=1)),
            vinculos_completed=("vinculos_completed", lambda s: s.sum(min_count=1)),
            media_taxa_sprint=("percentual_completed", "mean"),
            adicionadas=("tarefas_adicionadas", lambda s: s.sum(min_count=1)),
            retiradas=("tarefas_retiradas", lambda s: s.sum(min_count=1)),
            alteracoes=("alteracoes", lambda s: s.sum(min_count=1)),
            media_devs=("qtd_desenvolvedores", "mean"),
        )
    )
    # Proporção agregada do recorte de vínculos existentes nas sprints originais.
    stats["taxa_vinculos"] = np.where(
        stats["total_vinculos"] > 0,
        100 * stats["vinculos_completed"] / stats["total_vinculos"], np.nan,
    )
    return stats


def pearson_by_project(frame: pd.DataFrame, x: str, y: str) -> pd.DataFrame:
    rows = []
    for project, sub in frame.groupby("projeto"):
        pair = sub[[x, y]].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        n = len(pair)
        r = np.nan
        if n >= 3 and pair[x].nunique() > 1 and pair[y].nunique() > 1:
            r = float(pair[x].corr(pair[y], method="pearson"))
        rows.append({"projeto": project, "sprints": n, "r": r})
    return pd.DataFrame(rows)


def scope_buckets(frame: pd.DataFrame) -> pd.DataFrame:
    cols = ["projeto", "faixa", "n_sprints", "media_alteracoes", "media_completed"]
    f = frame.dropna(subset=["alteracoes", "percentual_completed"]).copy()
    if f.empty:
        return pd.DataFrame(columns=cols)
    f["faixa"] = pd.cut(f["alteracoes"], bins=[-0.01, 0, 5, 15, float("inf")],
                        labels=["Nenhuma", "1 a 5", "6 a 15", "> 15"])
    result = (f.groupby(["projeto", "faixa"], as_index=False, observed=True)
              .agg(n_sprints=("sprint_id", "count"),
                   media_alteracoes=("alteracoes", "mean"),
                   media_completed=("percentual_completed", "mean")))
    return result[cols]


def significance_phrase(r: float) -> str:
    if pd.isna(r):
        return "Indisponível"
    v = abs(r)
    strength = "praticamente nula" if v < .1 else "fraca" if v < .3 else "moderada" if v < .7 else "forte"
    if v < .1:
        return "Associação praticamente nula"
    return f"Associação {'positiva' if r > 0 else 'negativa'} {strength}"


def auto_insights(stats: pd.DataFrame, h2: pd.DataFrame, h3: pd.DataFrame) -> list[tuple[str, str, str]]:
    if stats.empty:
        return []
    notes = []
    deliveries = stats.dropna(subset=["media_entregas"])
    if not deliveries.empty:
        r = deliveries.loc[deliveries["media_entregas"].idxmax()]
        notes.append(("Maior volume médio de entregas", str(r["projeto"]),
                      f"{r['media_entregas']:.1f} tarefas concluídas por sprint no recorte atual."))
    rates = stats.dropna(subset=["taxa_vinculos"])
    if not rates.empty:
        r = rates.loc[rates["taxa_vinculos"].idxmax()]
        notes.append(("Maior proporção de vínculos Completed", str(r["projeto"]),
                      f"{r['taxa_vinculos']:.1f}% de vínculos concluídos nas sprints filtradas."))
    changes = stats.dropna(subset=["alteracoes"])
    if not changes.empty:
        r = changes.loc[changes["alteracoes"].idxmax()]
        notes.append(("Maior movimentação de escopo", str(r["projeto"]),
                      f"{r['alteracoes']:,.0f} adições e retiradas no recorte; mais alterações não significam pior gestão."))
    valid = h2.dropna(subset=["r"])
    if not valid.empty:
        r = valid.loc[valid["r"].abs().idxmax()]
        notes.append(("H2 · Equipe e entregas", str(r["projeto"]),
                      f"r = {r['r']:+.3f} ({int(r['sprints'])} sprints); associação não implica causalidade."))
    valid = h3.dropna(subset=["r"])
    if not valid.empty:
        r = valid.loc[valid["r"].abs().idxmax()]
        notes.append(("H3 · Escopo e conclusão", str(r["projeto"]),
                      f"r = {r['r']:+.3f} ({int(r['sprints'])} sprints); resultado exploratório."))
    return notes
