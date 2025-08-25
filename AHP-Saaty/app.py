# app.py — AHP (Saaty) sin Excel, modo entrevista, sin numpy/pandas
# Flujo:
# 1) Usuario define variables (criterios)
# 2) Entrevista par a par con escala de Saaty 9 … 1/9 (con reciprocidad automática)
# 3) Cálculo de Wi, λmax, CI, CR (valida consistencia + explicación + alerta si CR>0.10)
# 4) Entrevista 1–5 por criterio → IC y categoría según rangos comunes editables

import streamlit as st

# ---------------------------
# Config y tablas base
# ---------------------------
RI_TABLE = {1:0,2:0,3:0.58,4:0.90,5:1.12,6:1.24,7:1.32,8:1.41,9:1.45,10:1.49}

DEFAULT_RANGES = [
    {"label":"Bajo",        "min":1.00, "max":1.80},
    {"label":"Medio Bajo",  "min":1.81, "max":2.60},
    {"label":"Medio",       "min":2.61, "max":3.40},
    {"label":"Medio Alto",  "min":3.41, "max":4.20},
    {"label":"Alto",        "min":4.21, "max":4.60},
    {"label":"Extremo",     "min":4.61, "max":5.00},
]

SAATY_OPTIONS = [
    ("9 – Absolutamente más importante",       9.0),
    ("7 – Muy fuertemente más importante",     7.0),
    ("5 – Fuertemente más importante",         5.0),
    ("3 – Moderadamente más importante",       3.0),
    ("1 – Igual importancia",                  1.0),
    ("1/3 – Moderadamente menos importante",   1/3),
    ("1/5 – Fuertemente menos importante",     1/5),
    ("1/7 – Muy fuertemente menos importante", 1/7),
    ("1/9 – Absolutamente menos importante",   1/9),
]

# ---------------------------
# Utilidades de estado
# ---------------------------
def init_state():
    ss = st.session_state
    ss.setdefault("step", 1)
    ss.setdefault("criteria", [])
    ss.setdefault("pairwise", [])   # matriz pareada
    ss.setdefault("weights", [])
    ss.setdefault("metrics", {})    # lambda_max, CI, CR, valid
    ss.setdefault("scores", {})     # 1–5 por criterio
    ss.setdefault("ranges", [r.copy() for r in DEFAULT_RANGES])

def reset_all():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()  # <- reemplazo

def build_empty_matrix(n: int):
    return [[1.0 if i == j else 1.0 for j in range(n)] for i in range(n)]

# ---------------------------
# Núcleo AHP (sin numpy)
# ---------------------------
def ahp_from_pairwise(pairwise):
    """Retorna (weights, lambda_max, CI, CR)."""
    n = len(pairwise)
    # Sumas de columnas
    col_sums = [sum(pairwise[i][j] for i in range(n)) for j in range(n)]
    # Normaliza por columna
    norm = [[pairwise[i][j] / (col_sums[j] or 1.0) for j in range(n)] for i in range(n)]
    # Pesos = promedio por fila
    weights = [sum(norm[i]) / n for i in range(n)]
    # Normaliza por si acaso
    s = sum(weights) or 1.0
    weights = [w / s for w in weights]
    # λmax
    Aw = [sum(pairwise[i][j] * weights[j] for j in range(n)) for i in range(n)]
    lambdas = [Aw[i] / (weights[i] or 1e-12) for i in range(n)]
    lambda_max = sum(lambdas) / n
    # Consistencia
    CI = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    RI = RI_TABLE.get(n, 1.49)
    CR = 0.0 if RI == 0 else CI / RI
    return weights, lambda_max, CI, CR

def categorize(IC: float, ranges):
    for r in ranges:
        if r["min"] <= IC <= r["max"]:
            return r["label"]
    return "No clasificado"

# ---------------------------
# App
# ---------------------------
def main():
    st.set_page_config(page_title="AHP (entrevista) — sin Excel", page_icon="🧭", layout="centered")
    init_state()
    ss = st.session_state

    # Barra lateral
    with st.sidebar:
        st.header("Rangos de criticidad (1–5)")
        new_ranges = []
        for i, r in enumerate(ss["ranges"]):
            c1, c2, c3 = st.columns([1.6, 1, 1])
            with c1:
                lbl = st.text_input("Etiqueta", value=r["label"], key=f"lbl_{i}")
            with c2:
                vmin = st.number_input("min", value=float(r["min"]), step=0.01, key=f"min_{i}")
            with c3:
                vmax = st.number_input("max", value=float(r["max"]), step=0.01, key=f"max_{i}")
            new_ranges.append({"label": lbl, "min": float(vmin), "max": float(vmax)})
        ss["ranges"] = new_ranges

        st.markdown("---")
        if st.button("🔄 Reiniciar"):
            reset_all()

    st.title("AHP — Entrevista por pares (Saaty)")
    st.caption("Define variables, compáralas par a par (escala 9…1/9), calcula Wi/λmax/CI/CR y luego asigna impacto 1–5 para obtener IC y categoría.")

    # ---------------------------
    # Paso 1: Variables
    # ---------------------------
    st.subheader("1) Nombres de variables (criterios)")
    n = st.number_input("¿Cuántas variables quieres evaluar?", min_value=3, max_value=10,
                        value=max(3, len(ss["criteria"]) or 3), step=1)
    current = ss["criteria"] or [f"Criterio {i+1}" for i in range(int(n))]
    # Ajusta tamaño si cambió
    if len(current) != int(n):
        if int(n) > len(current):
            current = current + [f"Criterio {i+1}" for i in range(len(current), int(n))]
        else:
            current = current[:int(n)]

    new_criteria = []
    for i in range(int(n)):
        new_criteria.append(st.text_input(f"Variable {i+1}", value=current[i], key=f"crit_{i}"))
    ss["criteria"] = new_criteria

    if st.button("Continuar a confrontación por pares"):
        ss["pairwise"] = build_empty_matrix(len(ss["criteria"]))
        ss["step"] = 2
        st.rerun()  # <- reemplazo

    # ---------------------------
    # Paso 2: Entrevista par a par (Saaty)
    # ---------------------------
    if ss.get("step", 1) >= 2:
        st.subheader("2) Confrontación por pares (escala de Saaty 9…1/9)")
        crit = ss["criteria"]
        n = len(crit)
        if not ss.get("pairwise") or len(ss["pairwise"]) != n:
            ss["pairwise"] = build_empty_matrix(n)

        for i in range(n):
            for j in range(i+1, n):
                st.markdown(f"**¿Qué tan más importante es _{crit[i]}_ respecto de _{crit[j]}_?**")
                label = f"cmp_{i}_{j}"
                default_idx = 4  # "1 – Igual importancia"
                selected_text = st.selectbox(
                    "Elige una opción:",
                    options=[opt[0] for opt in SAATY_OPTIONS],
                    index=default_idx,
                    key=label
                )
                val_map = dict(SAATY_OPTIONS)
                val = float(val_map[selected_text])
                ss["pairwise"][i][j] = val
                ss["pairwise"][j][i] = 1.0 / val

        if st.button("Calcular pesos y consistencia"):
            w, lmax, CI, CR = ahp_from_pairwise(ss["pairwise"])
            ss["weights"] = w
            ss["metrics"] = {"lambda_max": lmax, "CI": CI, "CR": CR, "valid": (CR < 0.10)}
            st.success("Pesos y consistencia calculados.")

    # ---------------------------
    # Paso 3: Resultados AHP
    # ---------------------------
    if ss.get("step", 1) >= 2 and ss.get("weights"):
        st.subheader("3) Resultados AHP")
        crit = ss["criteria"]
        w = ss["weights"]
        metrics = ss["metrics"]

        st.write("**Pesos (Wi):**")
        for i, wi in enumerate(w):
            st.write(f"- {crit[i]}: {wi:.4f}")

        cons_text = "ACEPTABLE ✅" if metrics["valid"] else "NO ACEPTABLE ⚠️"
        st.write(
            f"**λmax:** {metrics['lambda_max']:.4f} | "
            f"**CI:** {metrics['CI']:.4f} | "
            f"**CR:** {metrics['CR']:.4f} → **Consistencia {cons_text}**"
        )

        # Explicación de consistencia
        with st.expander("ℹ️ ¿Qué significa la consistencia?"):
            st.markdown("""
La **consistencia** mide si las comparaciones par a par que hiciste son **lógicas entre sí**.  
- Un **CR ≤ 0.10 (10%)** indica que los juicios son **coherentes** y fiables.  
- Si **CR > 0.10**, puede haber **contradicciones** (p. ej., A > B, B > C, pero C > A).  
En ese caso conviene **revisar las comparaciones** y ajustarlas.
            """)

        # Alerta automática si CR > 0.10
        if not metrics["valid"]:
            st.error(
                "La razón de consistencia **CR** es **> 0.10** (inconsistencia significativa). "
                "Te recomiendo **revisar** algunas comparaciones:"
            )
            st.markdown("""
- Revisa pares donde pusiste valores **muy extremos** (9, 7, 1/7, 1/9) y confirma si realmente son tan desequilibrados.  
- Asegúrate de mantener **transitividad lógica**: si *A* ≫ *B* y *B* ≫ *C*, entonces *A* debería ≫ *C*.  
- Considera **igualar (1)** aquellos pares donde no tengas evidencia clara.
            """)
            if st.button("⬅️ Volver a confrontación por pares y ajustar"):
                ss["step"] = 2
                st.rerun()  # <- reemplazo

    # ---------------------------
    # Paso 4: Entrevista 1–5 (IC)
    # ---------------------------
    if ss.get("step", 1) >= 2 and ss.get("weights"):
        st.subheader("4) Entrevista: Impacto por criterio (escala 1–5)")
        st.markdown("""
**Guía de referencia:**
- **1 = Muy bajo** → impacto nulo o despreciable, control inmediato  
- **2 = Bajo** → afecta parcialmente pero controlable  
- **3 = Medio** → disrupción moderada  
- **4 = Alto** → requiere gran despliegue de recursos  
- **5 = Extremo** → paraliza operación o amenaza vital
        """)

        crit = ss["criteria"]
        scores = {}
        for c in crit:
            choice = st.radio(
                f"Impacto de **{c}**:",
                options=[
                    "1 – Muy bajo",
                    "2 – Bajo",
                    "3 – Medio",
                    "4 – Alto",
                    "5 – Extremo"
                ],
                index=2,  # por defecto "3 – Medio"
                key=f"impact_{c}"
            )
            scores[c] = int(choice.split("–")[0].strip())
        ss["scores"] = scores

        if st.button("Calcular Índice de Criticidad (IC) y categoría"):
            IC = sum(ss["weights"][i] * ss["scores"][crit[i]] for i in range(len(crit)))
            cat = categorize(IC, ss["ranges"])
            st.success(f"**Nivel de criticidad:** {cat} **(IC = {IC:.2f})**")
            st.info("Rangos usados: " + " | ".join([f"{r['label']} {r['min']:.2f}–{r['max']:.2f}" for r in ss['ranges']]))

if __name__ == "__main__":
    main()
