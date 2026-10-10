"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Scrollen auf dem Handy nicht zoomt."""

import numpy as np
import plotly.graph_objects as go

import rat_constants as C

_LAYOUT = dict(margin=dict(l=10, r=10, t=40, b=10), height=340, legend=dict(orientation="h", y=-0.25))


def _finish(fig, title, xtitle=None, ytitle=None, **extra):
    fig.update_layout(title=dict(text=title, x=0), xaxis=dict(title=xtitle, fixedrange=True),
                      yaxis=dict(title=ytitle, fixedrange=True), **{**_LAYOUT, **extra})
    return fig


def build_estimands(a, b, truth):
    """Die vier Kennzahl-Definitionen: gemessene Differenz B minus A im Experiment und wahre Wirkung (Prozentpunkte)."""
    labels = [C.KENNZAHL_SHORT[k] for k in C.KENNZAHLEN]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=[100 * (b[k] - a[k]) for k in C.KENNZAHLEN], name="gemessen in diesem Experiment",
                         marker_color=C.COLOR_B))
    fig.add_trace(go.Bar(x=labels, y=[100 * truth[k] for k in C.KENNZAHLEN], name="wahre Wirkung",
                         marker_color=C.COLOR_TRUTH))
    fig.update_layout(barmode="group")
    return _finish(fig, "Dieselbe Regel, vier Kennzahlen, vier Wirkungen", None, "Prozentpunkte Servicegrad")


def build_intervals(methods, truth):
    """95-%-Intervalle der vier Auswertungen untereinander; Raute: wahre Wirkung der jeweiligen Kennzahl."""
    fig = go.Figure()
    order = list(reversed(C.METHODS))
    for i, m in enumerate(order):
        r = methods[m]
        fig.add_trace(go.Scatter(x=[100 * r["diff"]], y=[i], mode="markers", name=C.METHOD_SHORT[m], showlegend=False,
                                 error_x=dict(type="data", symmetric=False, array=[100 * (r["hi"] - r["diff"])],
                                              arrayminus=[100 * (r["diff"] - r["lo"])], thickness=3, width=9,
                                              color=C.METHOD_COLORS[m]),
                                 marker=dict(color=C.METHOD_COLORS[m], size=11)))
        fig.add_trace(go.Scatter(x=[100 * truth[r["target"]]], y=[i], mode="markers", showlegend=False,
                                 marker=dict(color="white", size=11, symbol="diamond", line=dict(color=C.COLOR_TRUTH, width=2)),
                                 hovertemplate="wahr %{x:.2f}<extra></extra>"))
    fig.add_vline(x=0, line=dict(color="gray", width=1.2))
    fig.update_yaxes(tickmode="array", tickvals=list(range(len(order))), ticktext=[C.METHOD_SHORT[m] for m in order],
                     range=[-0.6, len(order) - 0.4])
    return _finish(fig, "95-%-Intervalle der vier Auswertungen (Raute: wahre Wirkung der Kennzahl)", "Prozentpunkte Servicegrad", None,
                   height=320)


def build_rates(rows, rows_null, has_effect):
    """Befundraten je Auswertung: ohne Wirkung (Fehlalarm) und mit Wirkung."""
    labels = [C.METHOD_SHORT[m] for m in C.METHODS]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=[100 * rows_null[m]["reject"] for m in C.METHODS], name="ohne Wirkung (Fehlalarm)",
                         marker_color=C.COLOR_MISS))
    if has_effect:
        fig.add_trace(go.Bar(x=labels, y=[100 * rows[m]["reject"] for m in C.METHODS], name="mit Wirkung (Teststärke)",
                             marker_color=C.COLOR_B))
    fig.add_hline(y=5, line=dict(color="gray", dash="dot"), annotation_text="Soll 5 %", annotation_position="top right")
    fig.update_layout(barmode="group")
    fig.update_yaxes(range=[0, 100])
    return _finish(fig, "Was die Auswertungen melden", None, "Anteil der Experimente in %")


def build_more_data(points):
    """Fehlalarmrate gegen die Zahl der Standorte je Arm für naiv und Cluster. points: {Methode: [(Beschriftung, Rate)]}."""
    fig = go.Figure()
    for m, pts in points.items():
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[100 * p[1] for p in pts], mode="lines+markers", name=C.METHOD_SHORT[m],
                                 line=dict(color=C.METHOD_COLORS[m], width=3)))
    fig.add_hline(y=5, line=dict(color="gray", dash="dot"), annotation_text="Soll 5 %", annotation_position="bottom right")
    fig.update_yaxes(range=[0, max(30, 100 * max(p[1] for pts in points.values() for p in pts) * 1.1)])
    return _finish(fig, "Ohne Wirkung: mehr Daten machen die naive Auswertung nicht besser", "Standorte je Arm und Wochen",
                   "Fehlalarmrate in %")
