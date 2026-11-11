"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import wlt_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_lesezugriffe(naiv, watch):
    """Zwei Balken: Lesezugriffe der ganzen Suche, naiv gegen Watched (Zahl über dem Balken)."""
    fig = go.Figure(go.Bar(x=["naiv", "Watched"], y=[naiv.lesezugriffe, watch.lesezugriffe], marker_color=[C.COLOR_NAIV, C.COLOR_WATCH],
                           text=[f"{naiv.lesezugriffe:,}".replace(",", "."), f"{watch.lesezugriffe:,}".replace(",", ".")], textposition="outside",
                           hovertemplate="%{x}: %{y:,} Lesezugriffe<extra></extra>"))
    fig.update_yaxes(title_text="Lesezugriffe der ganzen Suche", rangemode="tozero")
    return _base(fig, 320)


def build_wachstum(zeilen, groessenname):
    """Lesezugriffe je Propagation (naiv, Watched) über die Größe; Größen als Text, damit Plotly keine lineare Achse mit Lücken anlegt."""
    xs = [str(z["groesse"]) for z in zeilen]
    fig = go.Figure()
    for name, schluessel, farbe in (("naiv", "naiv", C.COLOR_NAIV), ("Watched", "watch", C.COLOR_WATCH)):
        ys = [z[schluessel]["lesezugriffe"] / z[schluessel]["propagationen"] if z[schluessel]["propagationen"] else 0 for z in zeilen]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", name=name, line=dict(color=farbe, width=3),
                                 hovertemplate="%{x}: %{y:.1f} Lesezugriffe je Propagation<extra>" + name + "</extra>"))
    fig.update_xaxes(title_text=groessenname, type="category")
    fig.update_yaxes(title_text="Lesezugriffe je Propagation", rangemode="tozero")
    return _base(fig)


def build_faktor(zeilen, groessenname):
    """Gesamtfaktor naiv / Watched (Summe über die festen Formeln) mit Band Minimum bis Maximum der Faktoren je Formel."""
    ok = [z for z in zeilen if z["faktor"] is not None]
    xs = [str(z["groesse"]) for z in ok]
    fig = go.Figure()
    if all(z["faktor_min"] is not None for z in ok):
        fig.add_trace(go.Scatter(x=xs + xs[::-1], y=[z["faktor_max"] for z in ok] + [z["faktor_min"] for z in ok][::-1], fill="toself",
                                 fillcolor="rgba(76,120,168,0.18)", line=dict(width=0), hoverinfo="skip", name="Minimum bis Maximum je Formel"))
    fig.add_trace(go.Scatter(x=xs, y=[z["faktor"] for z in ok], mode="lines+markers", line=dict(color=C.COLOR_LINE, width=3), name="Gesamtfaktor",
                             hovertemplate="%{x}: %{y:.1f}-mal<extra></extra>"))
    fig.update_xaxes(title_text=groessenname, type="category")
    fig.update_yaxes(title_text="Lesezugriffe naiv / Watched", rangemode="tozero")
    return _base(fig)


def build_besuch(zeilen):
    """Gestapelte Balken: Anteil der Besuche nach Ergebnis, je Fall zwei Balken (naiv, Watched)."""
    labels = []
    for z in zeilen:
        labels += [f"{z['label']}: naiv", f"{z['label']}: Watched"]
    fig = go.Figure()
    for schluessel, name in C.ERGEBNIS_NAMEN.items():
        ys = []
        for z in zeilen:
            for modus in ("naiv", "watch"):
                besuche = z[modus]["besuche"]
                ys.append(100.0 * z[modus]["besuche_nach"][schluessel] / besuche if besuche else 0.0)
        if not any(ys):
            continue
        fig.add_trace(go.Bar(y=labels, x=ys, name=name, orientation="h", marker_color=C.ERGEBNIS_FARBEN[schluessel],
                             hovertemplate="%{y}: %{x:.1f} %<extra>" + name + "</extra>"))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text="Anteil der Besuche (%)", range=[0, 100])
    fig.update_yaxes(autorange="reversed")
    return _base(fig, 120 + 46 * len(labels))
