"""Verhältniskennzahlen und Cluster - wer ist die Einheit? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Achtes Stück der Konzepte-Linie "Experimente und Wirkungsmessung": Der Servicegrad ist ein Verhältnis (Σ Fehlmenge / Σ
Nachfrage) aus täglichen Werten je Standort. Zwei Fragen entscheiden über jede Zahl, die ein Experiment liefert: Wie wird das
Verhältnis gebildet (Quote der Summen, Mittel der Tages- oder Wochenquoten)? Und welche Einheit ist unabhängig (der
Standort-Tag, die Standort-Woche, der Standort)? Siehe README.

Lauffähig mit: streamlit run app.py
"""

import numpy as np
import streamlit as st

import rat_constants as C
from rat_evaluation import lag1_autocorrelation, load_sites, nearest_z, run_one, summarize, true_effects
from rat_presets import (apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed,
                         sync_query_params)
from rat_visualization import build_estimands, build_intervals, build_more_data, build_rates

st.set_page_config(page_title="Verhältniskennzahlen – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _sites():
    return load_sites()


@st.cache_data(show_spinner=False)
def _one(pop, z, n, weeks, seed):
    return run_one(_sites(), {"pop": pop, "z": z, "n": n, "weeks": weeks, "seed": seed})


@st.cache_data(show_spinner=False)
def _many(pop, z, n, weeks):
    r = summarize(_sites(), pop, z, n, weeks, reps=C.LIVE_REPS)
    return {k: r[k] for k in ("rows", "truth")}


@st.cache_data(show_spinner=False)
def _more(pop):
    sites = _sites()
    combos = ((10, 4), (20, 4), (40, 4), (20, 8), (40, 8))
    out = {"naiv": [], "cluster": []}
    for n, w in combos:
        rows = summarize(sites, pop, 1.0, n, w, reps=C.LIVE_REPS, tag=11)["rows"]
        for m in out:
            out[m].append((f"{n} Standorte, {w} Wochen", rows[m]["reject"]))
    return out


@st.cache_data(show_spinner=False)
def _lag(pop):
    return lag1_autocorrelation(_sites(), pop)


st.title("➗ Verhältniskennzahlen und Cluster: wer ist die Einheit?")
st.markdown(
    """
Der Servicegrad ist ein **Verhältnis**: Fehlmenge geteilt durch Nachfrage, aus Hunderten Standort-Tagen. Daraus folgen zwei
Fragen, die beide den ausgewiesenen Effekt oder seine Unsicherheit verändern. **Erstens:** Wie wird das Verhältnis gebildet,
als Quote der Summen oder als Mittel der Tages-, Wochen- oder Standort-Quoten? Dieselbe Regel zeigt je nach Definition einen
anderen Effekt. **Zweitens:** Welche Einheit ist **unabhängig**? Zugeteilt wird je Standort, aber die Tage eines Standorts hängen
zusammen (ein Bestandsloch von gestern wirkt heute nach). Wer jeden Tag als unabhängige Einheit behandelt, rechnet ein
Intervall, das zu schmal ist.
"""
)
st.caption(
    "Achtes Stück der Linie „Experimente und Wirkungsmessung“, aufbauend auf "
    "[ab-test-demo](https://sebastianhanisch-ab-test-demo.streamlit.app/) und "
    "[cuped-demo](https://sebastianhanisch-cuped-demo.streamlit.app/) (gleiches Vehikel; Standort-Eigenheit wie dort). Neu: "
    "die Messung ist eine **Zeitreihe je Standort** (täglich), nicht ein Fenster. Jedes Folgestück hebt eine der Annahmen "
    "unter „Wo die Annahmen enden“ auf."
)

with st.expander("So unterscheiden sich Kennzahl und Einheit", expanded=True):
    st.markdown(
        """
- **Quote der Summen:** Σ Fehlmenge / Σ Nachfrage über alle Tage und Standorte eines Arms. Das ist der betriebliche
  Servicegrad; große Tage zählen mehr.
- **Mittel der Standort-, Tages- oder Wochenquoten:** erst die Quote je Einheit, dann der Mittelwert. Jede Einheit zählt
  gleich, auch ein Tag mit wenig Nachfrage. Die Zahl ist eine andere.
- **Einheit der Auswertung:** der **Standort-Tag** (hier hängen Nachbartage zusammen), die **Standort-Woche** (schwächer) oder
  der **Standort** (unabhängig, weil je Standort zugeteilt wurde).
- **Delta-Methode:** Standardfehler für ein Verhältnis aus Summen, mit dem Standort als Cluster: Abweichungen
  S − Quote · D je Standort statt je Tag.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_cols = st.columns(len(C.PRESET_ORDER))
for i, name in enumerate(C.PRESET_ORDER):
    with preset_cols[i]:
        st.button(name, key=f"preset_{i}", width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name])
st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Wahrheit**")
    pop_index = st.radio("Wie verschieden sind die Standorte?", options=list(range(len(C.POPULATIONS))), key="pop_radio",
                         format_func=lambda i: C.POPULATION_LABELS[C.POPULATIONS[i]],
                         help="Dauerhafte Unterschiede, weil die wahre Nachfrage-Streuung von der Planannahme abweicht.")
    z = st.slider("Sicherheitsfaktor z von Regel B", *bounds("z_slider"), step=C.Z_STEP, key="z_slider", format="%.1f",
                  help="Regel A fährt z = 1,0. Bei z = 1,0 ist es ein A/A-Test ohne Wirkung.")
    st.markdown("**Experiment**")
    n = st.slider("Standorte je Arm", *bounds("n_slider"), step=C.N_STEP, key="n_slider",
                  help="Zugeteilt wird je Standort; jeder Standort liefert eine Zeitreihe.")
    weeks = st.slider("Wochen Messdauer", *bounds("w_slider"), step=1, key="w_slider",
                      help="Jede Woche hat sieben Standort-Tage je Standort.")
    seed = st.number_input("Zufalls-Seed", min_value=bounds("seed_input")[0], max_value=bounds("seed_input")[1], step=1,
                           key="seed_input", help="Bestimmt die Standorte des einen Experiments unten.")
    st.button("🎲 Neues Experiment würfeln", on_click=randomize_seed)

z, n, weeks, seed = nearest_z(float(z)), int(n), int(weeks), int(seed)
pop = C.POPULATIONS[int(pop_index)]
sync_query_params({"z_slider": z, "n_slider": n, "w_slider": weeks, "pop_radio": int(pop_index), "seed_input": seed})

sites = _sites()
aa = z <= C.Z_A
truth = true_effects(sites, pop, z, weeks)

# --- Ein Experiment ---------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.markdown("## 🧪 Ein Experiment")
one = _one(pop, z, n, weeks, seed)
st.caption(
    f"{n} Standorte je Arm, {weeks} Wochen ({7 * weeks} Tage), „{C.POPULATION_LABELS[pop]}“; Regel B mit z = "
    f"{C.fmt_num(z)}" + (" (gleich wie A)." if aa else ".")
)
if not aa:
    st.plotly_chart(build_estimands(one["a"], one["b"], truth), width="stretch", key=f"est_{pop}_{z}_{n}_{weeks}_{seed}")
    st.caption(
        f"Die wahre Wirkung derselben Regel ist **{C.fmt_pp(truth['summen'])}** als Quote der Summen, "
        f"**{C.fmt_pp(truth['wochen'])}** als Mittel der Wochenquoten und **{C.fmt_pp(truth['tage'])}** als Mittel der "
        "Tagesquoten. Fehlmengen entstehen fast nur an Tagen mit großer Nachfrage; in der Quote der Summen zählen diese Tage "
        "mit ihrer Menge, im Tagesmittel nur je ein Tag."
    )
st.plotly_chart(build_intervals(one["methods"], truth), width="stretch", key=f"int_{pop}_{z}_{n}_{weeks}_{seed}")
rows_md = ["| Auswertung | Differenz | 95-%-Intervall | p-Wert |", "|---|---|---|---|"]
for m in C.METHODS:
    r = one["methods"][m]
    rows_md.append(f"| {C.METHOD_LABELS[m]} | {C.fmt_pkt(r['diff'], 2)} | {C.fmt_pkt(r['lo'], 2)} bis {C.fmt_pkt(r['hi'], 2)} | "
                   f"{C.fmt_num(r['p'], 3)} |")
st.markdown("\n".join(rows_md))

# --- Viele Experimente ----------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("📐 Tausend Experimente: welche Auswertung hält, was sie verspricht?")
with st.spinner("Rechne …"):
    many = _many(pop, z, n, weeks)
    null_many = _many(pop, 1.0, n, weeks) if not aa else many
rows = many["rows"]
st.plotly_chart(build_rates(rows, null_many["rows"], not aa), width="stretch", key=f"rates_{pop}_{z}_{n}_{weeks}")
tab = ["| Auswertung | Fehlalarm (ohne Wirkung) | Teststärke | Abdeckung des Intervalls | SE-Treue |", "|---|---|---|---|---|"]
for m in C.METHODS:
    tab.append(f"| {C.METHOD_SHORT[m]} | {C.fmt_pct(null_many['rows'][m]['reject'])} | "
               f"{C.fmt_pct(rows[m]['reject']) if not aa else '–'} | {C.fmt_pct(rows[m]['coverage'])} | "
               f"{C.fmt_num(rows[m]['se_fidelity'], 2)} |")
st.markdown("\n".join(tab))
st.caption("SE-Treue = mittlerer Standardfehler / tatsächliche Streuung der Schätzung (Soll 1; unter 1 heißt: zu optimistisch).")
nz = null_many["rows"]
st.error(
    f"**Wer jeden Standort-Tag als unabhängig behandelt, meldet ohne jede Wirkung in {C.fmt_pct(nz['naiv']['reject'], 0)} der "
    f"Experimente einen Unterschied** (versprochen waren 5 %); das 95-%-Intervall deckt die Wahrheit nur in "
    f"{C.fmt_pct(rows['naiv']['coverage'], 0)}. Mit dem Standort als Cluster sind es {C.fmt_pct(nz['cluster']['reject'])}. "
    f"Die Tage eines Standorts hängen zusammen (Autokorrelation 1. Ordnung {C.fmt_num(_lag(pop), 2)}): "
    "ein Tag trägt weniger neue Information, als die Zählung unterstellt."
)

st.markdown("---")
st.subheader("📈 Helfen mehr Standorte oder mehr Wochen?")
more = _more(pop)
st.plotly_chart(build_more_data(more), width="stretch", key=f"more_{pop}")
st.info(
    "Die naive Auswertung wird mit mehr Standorten oder Wochen **nicht besser**: sie zählt jeden Tag, aber die Tage eines "
    "Standorts sind verwandt, und bei dauerhaft verschiedenen Standorten kommt der Unterschied zwischen den Standorten dazu. "
    "Der Cluster-Ansatz bleibt bei 5 %."
)

# --- Grenzen ---------------------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Man weiß, welche Kennzahl gemeint ist** | Die Definition verschiebt den Effekt um bis zu ein Drittel; ein Dashboard mit Tagesmittel zeigt etwas anderes als der betriebliche Servicegrad. | (dieses Stück) |
| **Die Einheit der Auswertung ist die Einheit der Zuteilung** | Tage oder Wochen als unabhängige Einheiten zu zählen, macht Intervalle zu schmal. | (dieses Stück) |
| **Zugeteilt wird je Standort und Standorte beeinflussen sich nicht** | Teilen Standorte Kundschaft oder Lager, braucht es Cluster nach Nachbarschaft oder Zeitblöcke. | Interferenz und Switchback |
| **Wenige Cluster genügen** | Mit zehn Standorten je Arm ist die Delta-Methode mit Normalquantil leicht liberal (6,9 % statt 5,2 % Fehlalarm bei gleichen Standorten); die Demo nutzt das t-Quantil. | (dieses Stück) |
| **Ein Test, eine Kennzahl** | Vier Kennzahlen auf denselben Daten sind selbst vier Tests. | Viele Kennzahlen: Mehrfachtests und Gewinnerfluch |
| **Es gibt eine Vorperiode** | Mit ihr lässt sich die Standort-Streuung herausrechnen. | Varianzreduktion (CUPED) |
"""
)
st.caption(
    "Die Zahlen stammen aus dem erfundenen Vehikel dieses Stücks (Standorte mit Zeitreihen über 56 Tage, Nachfrage je Standort "
    "dieselbe unter A und B)."
)

st.markdown("---")
with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Quote der Summen.** Mit Fehlmenge $S_{it}$ und Nachfrage $D_{it}$ je Standort $i$ und Tag $t$ ist
$\hat R = \sum S_{it}/\sum D_{it}$ und der Servicegrad $1 - \hat R$. **Mittel der Quoten:** $\frac{1}{N}\sum_{u} S_u/D_u$ über
Einheiten $u$ (Tage, Wochen, Standorte); wegen $E[S/D] \ne E[S]/E[D]$ ist die Zahl eine andere.

**Delta-Methode.** Für $\hat R = \sum S_u/\sum D_u$ mit Einheiten $u$ ist
$\widehat{\mathrm{Var}}(\hat R) \approx \frac{n}{n-1}\sum_u (S_u - \hat R\, D_u)^2 / (\sum D_u)^2$. Bei **Cluster = Standort**
sind $u$ die Standorte (Summen über alle Tage), bei „naiv“ die Standort-Tage.

**Warum naiv zu eng ist.** Hat jeder Standort über $m$ Tage die Autokorrelation $\rho_1$ (und bei dauerhaft verschiedenen
Standorten die Intraklassenkorrelation $\mathrm{ICC}$), ist die Varianz des Mittels etwa das $1 + 2\rho_1 \approx 1{,}6$-Fache
(Korrelation nur zum Nachbartag) bis $(1+\rho_1)/(1-\rho_1) \approx 1{,}8$-Fache (AR(1)) der naiven, bei Clustern das
$1 + (m-1)\,\mathrm{ICC}$-Fache. Gemessen: Standardfehler zu 0,76-fach, also Varianz zu $1/0{,}76^2 \approx 1{,}7$; bei
verschiedenen Standorten kommt die Standort-Streuung dazu.

**t-Quantil.** Das Intervall nutzt $t_{n_A + n_B - 2}$, nicht 1,96: bei zehn Standorten je Arm ist der Unterschied relevant.

Implementiert in `rat_evaluation.py` (Kennzahlen, Delta-Methode, Welch, Zusammenfassungen), `rat_vehicle.py` (Standort mit
Tagesreihe), `generate_precomputed.py` (Standort-Populationen).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
