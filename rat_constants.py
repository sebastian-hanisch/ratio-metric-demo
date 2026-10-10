"""Konstanten: Vehikel, Regler-Grenzen, Farben, Presets. Das Vehikel (ein Standort mit Bestand) ist das der ganzen Linie."""

# Vehikel: ein Standort, tägliche Nachbestellung (Order-up-to), Wiederbeschaffungszeit 2 Tage, Zentrallager unbegrenzt.
BASE_MEAN = 20.0          # mittlere Tagesnachfrage des Standorts (Stück)
DISP = 5                  # angenommene Dispersion der Nachfrage in der Bestellregel
LEAD = 2                  # Wiederbeschaffungszeit in Tagen
BURN_DAYS = 28            # Einschwingtage vor der Messung (gleiche Regel)
WINDOW_DAYS = 28          # Länge eines Auswertefensters der Vorgänger-Stücke (hier nur für den Vehikel-Kern)
Z_A = 1.0                 # Sicherheitsfaktor der bestehenden Regel A
ALPHA = 0.05

# Stück 8: Zeitreihen je Standort, Kennzahl als Verhältnis, Einheit der Auswertung
DAYS = 56                 # gemessene Tage je Standort (8 Wochen); Experimente nutzen die ersten 7 * Wochen Tage
POPULATIONS = ("gleich", "verschieden")
POPULATION_SHAPES = {"gleich": (5,), "verschieden": (2, 3, 4, 5, 6, 8, 12)}
POPULATION_LABELS = {"gleich": "Alle Standorte gleich", "verschieden": "Standorte dauerhaft verschieden"}
SITES_PER_POPULATION = 1000
Z_GRID = (1.2, 1.4, 1.8)  # Sicherheitsfaktoren der Regel B im Vorrat (1,0 = A/A)
Z_MIN, Z_MAX, DEFAULT_Z, Z_STEP = 1.0, 1.8, 1.4, 0.2
N_MIN, N_MAX, DEFAULT_N, N_STEP = 10, 60, 20, 10        # Standorte je Arm
W_MIN, W_MAX, DEFAULT_W = 4, 8, 8                       # Wochen Messdauer
KENNZAHLEN = ("summen", "standort", "tage", "wochen")
KENNZAHL_LABELS = {
    "summen": "Quote der Summen (Σ Fehlmenge / Σ Nachfrage)",
    "standort": "Mittel der Standort-Quoten",
    "tage": "Mittel der Tagesquoten",
    "wochen": "Mittel der Wochenquoten",
}
KENNZAHL_SHORT = {"summen": "Quote der Summen", "standort": "Standort-Mittel", "tage": "Tages-Mittel", "wochen": "Wochen-Mittel"}
SEED_MAX, DEFAULT_SEED = 999999, 35
LIVE_REPS = 1000

METHODS = ("naiv", "cluster", "standort", "wochen")
METHOD_LABELS = {
    "naiv": "Naiv: jeder Standort-Tag unabhängig",
    "cluster": "Delta-Methode, Standort als Cluster",
    "standort": "Standort-Mittel, Welch-Test über Standorte",
    "wochen": "Naiv: jede Standort-Woche unabhängig",
}
METHOD_SHORT = {"naiv": "Naiv (Tage)", "cluster": "Delta, Cluster", "standort": "Standort-Welch", "wochen": "Naiv (Wochen)"}
METHOD_COLORS = {"naiv": "#c0392b", "cluster": "#2F6B65", "standort": "#4c78a8", "wochen": "#d95f02"}

COLOR_A = "#4c78a8"
COLOR_B = "#2F6B65"
COLOR_TRUTH = "#d95f02"
COLOR_MISS = "#c0392b"
COLOR_OK = "rgba(120,120,120,0.55)"

PRESETS = {
    "Die Kennzahl entscheidet (Voreinstellung)": {"z": DEFAULT_Z, "n": DEFAULT_N, "w": DEFAULT_W, "pop": 0, "seed": DEFAULT_SEED},
    "Standorte dauerhaft verschieden": {"z": DEFAULT_Z, "n": DEFAULT_N, "w": DEFAULT_W, "pop": 1, "seed": DEFAULT_SEED},
    "Kein Effekt (A/A)": {"z": 1.0, "n": DEFAULT_N, "w": DEFAULT_W, "pop": 0, "seed": DEFAULT_SEED},
    "Kurz messen, viele Standorte": {"z": DEFAULT_Z, "n": 40, "w": 4, "pop": 0, "seed": DEFAULT_SEED},
}
PRESET_ORDER = tuple(PRESETS)
PRESET_HELP = {
    "Die Kennzahl entscheidet (Voreinstellung)": "Alle Standorte gleich, acht Wochen, 20 Standorte je Arm: dieselbe Regel, vier Kennzahlen, vier verschiedene Effekte.",
    "Standorte dauerhaft verschieden": "Jeder Standort hat eine eigene Nachfrage-Streuung: das macht den Standort zum echten Cluster.",
    "Kein Effekt (A/A)": "Beide Regeln gleich: wie oft melden die Auswertungen trotzdem einen Unterschied?",
    "Kurz messen, viele Standorte": "40 Standorte je Arm, nur vier Wochen: mehr Cluster, weniger Zeit je Cluster.",
}


def fmt_pct(x, digits=1):
    """Anteil (0..1) als Prozentzahl mit Dezimalkomma, z. B. 0,934 -> '93,4 %'."""
    return f"{100 * x:.{digits}f}".replace(".", ",") + " %"


def fmt_pp(x, digits=2):
    """Differenz in Prozentpunkten (aus Anteilen 0..1) mit Vorzeichen und Dezimalkomma."""
    return f"{100 * x:+.{digits}f}".replace(".", ",") + " Prozentpunkte"


def fmt_pkt(x, digits=1):
    """Kurzform für enge Kacheln: '+4,0 Pkt.' (Differenz in Prozentpunkten, aus Anteilen 0..1)."""
    return f"{100 * x:+.{digits}f}".replace(".", ",") + " Pkt."


def fmt_num(x, digits=1):
    return f"{x:.{digits}f}".replace(".", ",")


def fmt_int(x):
    """Ganzzahl mit Leerzeichen als Tausendertrenner."""
    return f"{int(x):,}".replace(",", " ")
