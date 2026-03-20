import streamlit as st
import pandas as pd
import json
import openpyxl
from io import BytesIO

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Portal do Representante",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif !important;
}

.stApp {
    background: linear-gradient(155deg, #143f50 0%, #1a5268 100%);
    color: white;
}

/* Métricas */
[data-testid="metric-container"] {
    background: #1e6070;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 18px;
    padding: 20px !important;
}
[data-testid="metric-container"] label {
    color: rgba(255,255,255,0.6) !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.09em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #F47920 !important;
    font-size: 22px !important;
    font-weight: 800 !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    color: rgba(255,255,255,0.5) !important;
}

/* Tabs */
[data-baseweb="tab-list"] {
    background: transparent !important;
    gap: 6px;
}
[data-baseweb="tab"] {
    background: rgba(0,0,0,0.22) !important;
    border-radius: 10px !important;
    color: white !important;
    font-weight: 700 !important;
    border: none !important;
    padding: 8px 18px !important;
}
[aria-selected="true"] {
    background: #F47920 !important;
    box-shadow: 0 4px 16px rgba(244,121,32,0.27) !important;
}
[data-baseweb="tab-highlight"] { display: none !important; }
[data-baseweb="tab-border"]    { display: none !important; }

/* DataFrames */
[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
}
.stDataFrame thead tr th {
    background: #1e6070 !important;
    color: rgba(255,255,255,0.6) !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Inputs */
input, select, textarea {
    background: rgba(0,0,0,0.25) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: white !important;
    font-family: 'Syne', sans-serif !important;
}

/* Botões */
.stButton > button {
    background: #F47920 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-family: 'Syne', sans-serif !important;
    transition: opacity 0.15s;
}
.stButton > button:hover { opacity: 0.85; }

/* Selectbox */
[data-baseweb="select"] > div {
    background: rgba(0,0,0,0.25) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: white !important;
}

/* Esconder rodapé Streamlit */
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
header { visibility: hidden; }

.block-container { padding-top: 1.5rem !important; }

/* Cards customizados */
.kpi-green [data-testid="stMetricValue"] { color: #8DC63F !important; }
.kpi-yellow [data-testid="stMetricValue"] { color: #f5c842 !important; }
.kpi-blue   [data-testid="stMetricValue"] { color: #4db8d4 !important; }

/* Barra de progresso */
.prog-bar-bg {
    background: rgba(0,0,0,0.3);
    border-radius: 99px;
    height: 14px;
    overflow: hidden;
    margin: 8px 0;
}
.prog-bar-fill {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #8DC63F, #a8e05f);
    transition: width 0.6s ease;
}

/* Badge status */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# DADOS
# ═══════════════════════════════════════════════════════════════

def safe_float(v):
    try: return float(v or 0)
    except: return 0.0

def fmt_date(v):
    if hasattr(v, 'strftime'): return v.strftime("%d/%m/%Y")
    return str(v or "")

def load_from_excel(file_bytes):
    wb = openpyxl.load_workbook(BytesIO(file_bytes))

    # Estoque
    ws = wb['Estoque']
    estoque = []
    for r in range(4, ws.max_row + 1):
        m2    = safe_float(ws.cell(r, 8).value)
        rolos = safe_float(ws.cell(r, 9).value)
        if m2 <= 0 and rolos <= 0: continue
        estoque.append({
            "filial": str(ws.cell(r, 1).value or "").strip(),
            "familia": str(ws.cell(r, 2).value or "").strip(),
            "desc_produto": str(ws.cell(r, 3).value or "").strip(),
            "sku": str(ws.cell(r, 4).value or "").strip(),
            "produto": str(ws.cell(r, 5).value or "").strip(),
            "largura": safe_float(ws.cell(r, 6).value),
            "comprimento": safe_float(ws.cell(r, 7).value),
            "m2_disponivel": round(m2, 2),
            "rolos_disponivel": round(rolos, 2),
        })

    # Pedidos
    ws2 = wb['Pedidos']
    pedidos = []
    for r in range(4, ws2.max_row + 1):
        vend = str(ws2.cell(r, 12).value or "").strip()
        if vend in ('', 'Vendedor'): continue
        pedidos.append({
            "filial": str(ws2.cell(r, 1).value or "").strip(),
            "pedido": str(ws2.cell(r, 2).value or "").strip(),
            "uf": str(ws2.cell(r, 3).value or "").strip(),
            "emissao": fmt_date(ws2.cell(r, 4).value),
            "entrega": fmt_date(ws2.cell(r, 5).value),
            "cliente": str(ws2.cell(r, 7).value or "").strip()[:55],
            "segmento": str(ws2.cell(r, 8).value or "").strip(),
            "sku": str(ws2.cell(r, 10).value or "").strip(),
            "produto": str(ws2.cell(r, 11).value or "").strip()[:55],
            "vendedor": vend,
            "status": str(ws2.cell(r, 14).value or "").strip(),
            "valor_vendido": round(safe_float(ws2.cell(r, 15).value), 2),
            "valor_atendido": round(safe_float(ws2.cell(r, 16).value), 2),
            "valor_a_entregar": round(safe_float(ws2.cell(r, 17).value), 2),
            "m2_vendido": round(safe_float(ws2.cell(r, 29).value), 2),
            "m2_atendido": round(safe_float(ws2.cell(r, 30).value), 2),
            "m2_saldo": round(safe_float(ws2.cell(r, 31).value), 2),
        })

    return estoque, pedidos


@st.cache_data
def load_seed_data():
    with open("estoque.json", encoding="utf-8") as f: estoque = json.load(f)
    with open("pedidos.json", encoding="utf-8") as f: pedidos = json.load(f)
    with open("users.json",   encoding="utf-8") as f: users   = json.load(f)
    return estoque, pedidos, users


def init_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.current_user = None

    if "data_loaded" not in st.session_state:
        estoque, pedidos, users = load_seed_data()
        st.session_state.estoque = estoque
        st.session_state.pedidos = pedidos
        st.session_state.users   = users
        st.session_state.data_loaded = True


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

BRL = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
M2  = lambda v: f"{v:,.2f} m²".replace(",", "X").replace(".", ",").replace("X", ".")

STATUS_COLOR = {
    "Aguardando Faturamento":           "#f5c842",
    "Aguardando Faturamento - Parcial": "#f5c842",
    "Pedido de Venda em Aberto":        "#4db8d4",
    "Aguardando Separação":             "#F47920",
    "Financeiro Rejeitado":             "#e05555",
    "Aguardando Liberação Estoque":     "#b07aff",
    "Aguardando Liberação Comercial":   "#b07aff",
    "Sem Status":                       "rgba(255,255,255,0.4)",
}

def status_badge(s):
    color = STATUS_COLOR.get(s, "rgba(255,255,255,0.3)")
    return f'<span class="badge" style="background:{color}22;color:{color};border:1px solid {color}55">{s}</span>'

def section_header(title, sub=None):
    st.markdown(f"""
    <div style="margin-bottom:20px">
        <div style="font-weight:800;font-size:22px;letter-spacing:-0.02em;color:white">{title}</div>
        {f'<div style="color:rgba(255,255,255,0.6);font-size:13px;margin-top:4px">{sub}</div>' if sub else ''}
    </div>
    """, unsafe_allow_html=True)

def prog_bar(pct, label_left, label_right):
    color = "#8DC63F" if pct >= 70 else "#f5c842" if pct >= 40 else "#e05555"
    st.markdown(f"""
    <div style="margin:12px 0">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <span style="font-weight:700;font-size:14px;color:white">% Atendido da Carteira</span>
            <span style="font-weight:800;font-size:22px;color:{color}">{pct:.1f}%</span>
        </div>
        <div class="prog-bar-bg">
            <div class="prog-bar-fill" style="width:{pct}%;background:linear-gradient(90deg,{color},{color}bb)"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:12px;color:rgba(255,255,255,0.5);margin-top:6px">
            <span>Atendido: {label_left}</span><span>Total: {label_right}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def card_wrap(content_fn):
    st.markdown('<div style="background:#1e6070;border-radius:18px;border:1px solid rgba(255,255,255,0.1);padding:24px">', unsafe_allow_html=True)
    content_fn()
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════

def render_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;margin:40px 0 32px">
            <div style="width:68px;height:68px;border-radius:20px;background:linear-gradient(135deg,#F47920,#ff9a40);
                display:flex;align-items:center;justify-content:center;margin:0 auto 16px;
                font-size:32px;box-shadow:0 12px 40px rgba(244,121,32,0.35)">📦</div>
            <div style="font-size:28px;font-weight:800;letter-spacing:-0.03em;color:white">Portal do Representante</div>
            <div style="color:rgba(255,255,255,0.6);font-size:14px;margin-top:6px">Gestão de Estoque &amp; Carteira</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            login    = st.text_input("Usuário", placeholder="seu.login")
            password = st.text_input("Senha", type="password", placeholder="••••••••")
            submit   = st.form_submit_button("Entrar →", use_container_width=True)

            if submit:
                user = next((u for u in st.session_state.users
                             if u["login"] == login and u["password"] == password), None)
                if user:
                    st.session_state.logged_in    = True
                    st.session_state.current_user = user
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

        st.markdown("""
        <div style="text-align:center;margin-top:16px;color:rgba(255,255,255,0.5);font-size:12px">
            Admin: <strong style="color:white">admin</strong> / <strong style="color:white">admin123</strong>
            &nbsp;·&nbsp; Reps: senha padrão <strong style="color:white">123456</strong>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════

def render_header(subtitle):
    user = st.session_state.current_user
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;padding:8px 0 20px">
            <div style="width:42px;height:42px;border-radius:13px;background:#F47920;display:flex;
                align-items:center;justify-content:center;font-size:20px;
                box-shadow:0 4px 16px rgba(244,121,32,0.4)">📦</div>
            <div>
                <div style="font-weight:800;font-size:17px;letter-spacing:-0.01em">Portal do Representante</div>
                <div style="color:rgba(255,255,255,0.6);font-size:12px">{subtitle}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="text-align:right;padding:8px 0 4px">
            <div style="font-weight:700;font-size:13px">{user['name'][:30]}</div>
            <div style="color:rgba(255,255,255,0.5);font-size:11px">{user.get('segmento','')}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Sair", key="logout_btn"):
            st.session_state.logged_in    = False
            st.session_state.current_user = None
            st.rerun()
    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.1);margin:0 0 24px'>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# PRODUTO SEARCH
# ═══════════════════════════════════════════════════════════════

def render_produto_search():
    estoque = st.session_state.estoque
    df = pd.DataFrame(estoque)

    section_header("🔍 Busca de Produtos", f"{len(df)} produtos com saldo disponível")

    mode = st.radio("Modo de busca", ["Por SKU / Nome", "Por Configuração"], horizontal=True)

    if mode == "Por SKU / Nome":
        query = st.text_input("SKU, Código ou Descrição", placeholder="Ex: PA.43.21... ou FITA CREPE...")
        if query:
            q = query.lower()
            mask = (df["sku"].str.lower().str.contains(q, na=False) |
                    df["produto"].str.lower().str.contains(q, na=False) |
                    df["desc_produto"].str.lower().str.contains(q, na=False))
            result = df[mask]
        else:
            result = df
    else:
        c1, c2, c3, c4 = st.columns(4)
        familias = ["Todas"] + sorted(df["familia"].dropna().unique().tolist())
        filiais  = ["Todas"] + sorted(df["filial"].dropna().unique().tolist())
        with c1: fam = st.selectbox("Família", familias)
        with c2: fil = st.selectbox("Filial", filiais)
        with c3: larg = st.text_input("Largura (mm)", placeholder="Ex: 25")
        with c4: comp = st.text_input("Comprimento (m)", placeholder="Ex: 50")

        result = df.copy()
        if fam != "Todas": result = result[result["familia"] == fam]
        if fil != "Todas": result = result[result["filial"]  == fil]
        if larg:
            try: result = result[result["largura"] == float(larg)]
            except: pass
        if comp:
            try: result = result[result["comprimento"] == float(comp)]
            except: pass

    st.markdown(f"**{len(result)}** produto{'s' if len(result) != 1 else ''} encontrado{'s' if len(result) != 1 else ''}")

    if not result.empty:
        display = result[["sku","produto","familia","filial","largura","comprimento","m2_disponivel","rolos_disponivel"]].copy()
        display.columns = ["SKU","Produto","Família","Filial","Larg.(mm)","Comp.(m)","M² Disp.","Rolos"]
        display["M² Disp."] = display["M² Disp."].apply(lambda v: f"{v:,.2f}")
        display["Rolos"]    = display["Rolos"].apply(lambda v: f"{v:,.0f}")
        st.dataframe(display.head(300), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# PERFORMANCE REP
# ═══════════════════════════════════════════════════════════════

def render_performance_rep(vendedor):
    pedidos = st.session_state.pedidos
    my = [p for p in pedidos if p["vendedor"] == vendedor]
    df = pd.DataFrame(my) if my else pd.DataFrame()

    section_header("📈 Minha Performance", "Visão consolidada da sua carteira")

    if df.empty:
        st.info("Nenhum pedido encontrado para este representante.")
        return

    cart_brl = df["valor_vendido"].sum()
    fat_brl  = df["valor_atendido"].sum()
    sal_brl  = df["valor_a_entregar"].sum()
    cart_m2  = df["m2_vendido"].sum()
    fat_m2   = df["m2_atendido"].sum()
    sal_m2   = df["m2_saldo"].sum()
    pct      = (fat_brl / cart_brl * 100) if cart_brl > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🛒 Carteira Total",   BRL(cart_brl), M2(cart_m2))
    c2.metric("✅ Atendido",         BRL(fat_brl),  M2(fat_m2))
    c3.metric("⏳ Saldo a Faturar",  BRL(sal_brl),  M2(sal_m2))
    c4.metric("📋 Itens em Carteira", len(df))

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    prog_bar(pct, BRL(fat_brl), BRL(cart_brl))

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 🏆 Top Produtos Atendidos")
        fat_df = df[df["valor_atendido"] > 0].groupby("produto").agg(
            Valor=("valor_atendido","sum"), M2=("m2_atendido","sum")
        ).sort_values("Valor", ascending=False).head(5)
        if fat_df.empty:
            st.info("Sem atendimentos registrados.")
        else:
            for i, (prod, row) in enumerate(fat_df.iterrows()):
                pct_bar = row["Valor"] / fat_df["Valor"].iloc[0] * 100
                st.markdown(f"""
                <div style="margin-bottom:12px">
                    <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">
                        <span><span style="color:#F47920;font-weight:700">#{i+1}</span> {prod[:40]}</span>
                        <span style="color:#8DC63F;font-weight:700">{BRL(row['Valor'])}</span>
                    </div>
                    <div style="background:rgba(0,0,0,0.3);border-radius:99px;height:7px">
                        <div style="height:100%;width:{pct_bar}%;background:linear-gradient(90deg,#F47920,#f5c842);border-radius:99px"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with col_b:
        st.markdown("#### 📊 Status dos Pedidos")
        status_df = df.groupby("status").size().reset_index(name="Qtd").sort_values("Qtd", ascending=False)
        for _, row in status_df.iterrows():
            color = STATUS_COLOR.get(row["status"], "rgba(255,255,255,0.4)")
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:13px">
                <span style="color:{color}">{row['status'] or 'Sem Status'}</span>
                <span style="background:{color}22;color:{color};border:1px solid {color}55;
                    border-radius:20px;padding:2px 10px;font-size:11px;font-weight:700">{row['Qtd']}</span>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# PERFORMANCE ADMIN
# ═══════════════════════════════════════════════════════════════

def render_performance_admin():
    users   = st.session_state.users
    pedidos = st.session_state.pedidos
    reps    = [u for u in users if u["role"] == "rep"]
    medals  = ["🥇", "🥈", "🥉"]

    section_header("📈 Performance Geral", "Ranking de todos os representantes com pedidos ativos")

    sort_opt = st.radio("Ordenar por", ["Carteira R$", "Atendido R$", "Saldo R$", "% Atend.", "Nº Itens"], horizontal=True)
    sort_map = {"Carteira R$":"cart_brl","Atendido R$":"fat_brl","Saldo R$":"sal_brl","% Atend.":"pct","Nº Itens":"itens"}
    sort_key = sort_map[sort_opt]

    stats = []
    for u in reps:
        my = [p for p in pedidos if p["vendedor"] == u["vendedor"]]
        if not my: continue
        cart_brl = sum(p["valor_vendido"]    for p in my)
        fat_brl  = sum(p["valor_atendido"]   for p in my)
        sal_brl  = sum(p["valor_a_entregar"] for p in my)
        cart_m2  = sum(p["m2_vendido"]       for p in my)
        fat_m2   = sum(p["m2_atendido"]      for p in my)
        pct      = (fat_brl / cart_brl * 100) if cart_brl > 0 else 0
        stats.append({**u, "cart_brl":cart_brl,"fat_brl":fat_brl,"sal_brl":sal_brl,
                      "cart_m2":cart_m2,"fat_m2":fat_m2,"pct":pct,"itens":len(my)})

    stats.sort(key=lambda x: x[sort_key], reverse=True)

    tCart = sum(r["cart_brl"] for r in stats)
    tFat  = sum(r["fat_brl"]  for r in stats)
    tSal  = sum(r["sal_brl"]  for r in stats)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🛒 Carteira Total",   BRL(tCart))
    c2.metric("✅ Total Atendido",   BRL(tFat))
    c3.metric("⏳ Saldo a Faturar",  BRL(tSal))
    c4.metric("👥 Representantes",   len(stats), "com pedidos ativos")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    max_cart = stats[0]["cart_brl"] if stats else 1

    for i, r in enumerate(stats):
        bar_w   = (r["cart_brl"] / max_cart * 100) if max_cart > 0 else 0
        bar_col = "#8DC63F" if i == 0 else "#F47920"
        pct_col = "#8DC63F" if r["pct"]>=70 else "#f5c842" if r["pct"]>=40 else "#e05555"
        medal   = medals[i] if i < 3 else f"#{i+1}"

        st.markdown(f"""
        <div style="background:#1e6070;border-radius:18px;border:1px solid rgba(255,255,255,0.1);
            padding:16px 22px;margin-bottom:10px">
            <div style="display:flex;flex-wrap:wrap;gap:16px;align-items:center">
                <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:200px">
                    <div style="font-size:26px;min-width:32px;text-align:center">{medal}</div>
                    <div>
                        <div style="font-weight:700;font-size:14px">{r['name'][:35]}</div>
                        <div style="color:rgba(255,255,255,0.5);font-size:11px;margin-top:2px">{r['itens']} itens em carteira</div>
                    </div>
                </div>
                <div style="display:flex;gap:24px;flex-wrap:wrap">
                    <div><div style="color:rgba(255,255,255,0.5);font-size:9px;font-weight:700;text-transform:uppercase">Carteira</div>
                         <div style="color:#F47920;font-weight:800;font-size:15px">{BRL(r['cart_brl'])}</div></div>
                    <div><div style="color:rgba(255,255,255,0.5);font-size:9px;font-weight:700;text-transform:uppercase">Atendido</div>
                         <div style="color:#8DC63F;font-weight:800;font-size:15px">{BRL(r['fat_brl'])}</div></div>
                    <div><div style="color:rgba(255,255,255,0.5);font-size:9px;font-weight:700;text-transform:uppercase">Saldo</div>
                         <div style="color:#f5c842;font-weight:800;font-size:15px">{BRL(r['sal_brl'])}</div></div>
                    <div><div style="color:rgba(255,255,255,0.5);font-size:9px;font-weight:700;text-transform:uppercase">% Atend.</div>
                         <div style="color:{pct_col};font-weight:800;font-size:15px">{r['pct']:.1f}%</div></div>
                </div>
            </div>
            <div style="margin-top:12px;background:rgba(0,0,0,0.3);border-radius:99px;height:7px">
                <div style="height:100%;width:{bar_w}%;background:linear-gradient(90deg,{bar_col}88,{bar_col});border-radius:99px"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# REP DASHBOARD
# ═══════════════════════════════════════════════════════════════

def render_rep_dashboard():
    user    = st.session_state.current_user
    pedidos = st.session_state.pedidos
    estoque = st.session_state.estoque

    render_header("Meu Painel")

    my  = [p for p in pedidos if p["vendedor"] == user["vendedor"]]
    df  = pd.DataFrame(my) if my else pd.DataFrame()
    est = pd.DataFrame(estoque)

    # KPIs topo
    cart_brl = df["valor_vendido"].sum()   if not df.empty else 0
    fat_brl  = df["valor_atendido"].sum()  if not df.empty else 0
    sal_brl  = df["valor_a_entregar"].sum()if not df.empty else 0
    cart_m2  = df["m2_vendido"].sum()      if not df.empty else 0
    sal_m2   = df["m2_saldo"].sum()        if not df.empty else 0
    est_m2   = est["m2_disponivel"].sum()

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🏭 Estoque Total",    M2(est_m2))
    c2.metric("🛒 Carteira Total",   BRL(cart_brl), M2(cart_m2))
    c3.metric("✅ Atendido",         BRL(fat_brl))
    c4.metric("⏳ Saldo a Faturar",  BRL(sal_brl),  M2(sal_m2))

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🛒 Minha Carteira", "🏭 Estoque", "🔍 Produtos", "📈 Performance"])

    with tab1:
        if df.empty:
            st.info("Nenhum pedido em carteira.")
        else:
            show = df[["pedido","sku","cliente","produto","status","uf","m2_vendido","m2_atendido","m2_saldo","valor_vendido","valor_atendido","valor_a_entregar","emissao","entrega"]].copy()
            show.columns = ["Pedido","SKU","Cliente","Produto","Status","UF","m² Vend.","m² Aten.","m² Saldo","R$ Vendido","R$ Atend.","R$ Saldo","Emissão","Entrega"]
            for col in ["R$ Vendido","R$ Atend.","R$ Saldo"]:
                show[col] = show[col].apply(BRL)
            for col in ["m² Vend.","m² Aten.","m² Saldo"]:
                show[col] = show[col].apply(lambda v: f"{v:,.2f}")
            st.dataframe(show, use_container_width=True, hide_index=True)

    with tab2:
        show_est = est[["sku","produto","familia","filial","largura","comprimento","m2_disponivel","rolos_disponivel"]].copy()
        show_est.columns = ["SKU","Produto","Família","Filial","Larg.(mm)","Comp.(m)","M² Disp.","Rolos"]
        show_est["M² Disp."] = show_est["M² Disp."].apply(lambda v: f"{v:,.2f}")
        show_est["Rolos"]    = show_est["Rolos"].apply(lambda v: f"{v:,.0f}")
        st.dataframe(show_est, use_container_width=True, hide_index=True)

    with tab3:
        render_produto_search()

    with tab4:
        render_performance_rep(user["vendedor"])


# ═══════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════

def render_admin_dashboard():
    render_header("Painel Administrativo")

    pedidos = st.session_state.pedidos
    estoque = st.session_state.estoque
    users   = st.session_state.users
    reps    = [u for u in users if u["role"] == "rep"]

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Visão Geral", "📈 Performance", "🛒 Carteira Geral", "🔍 Produtos", "👥 Representantes"
    ])

    # ── VISÃO GERAL ──────────────────────────────────────────────
    with tab1:
        section_header("📊 Visão Geral")

        df  = pd.DataFrame(pedidos)
        est = pd.DataFrame(estoque)

        tCart = df["valor_vendido"].sum()
        tFat  = df["valor_atendido"].sum()
        tSal  = df["valor_a_entregar"].sum()
        tM2   = est["m2_disponivel"].sum()

        c1,c2,c3,c4,c5,c6 = st.columns(6)
        c1.metric("🛒 Carteira Total",  BRL(tCart))
        c2.metric("✅ Total Atendido",  BRL(tFat))
        c3.metric("⏳ Saldo a Faturar", BRL(tSal))
        c4.metric("🏭 Estoque M²",      M2(tM2))
        c5.metric("👥 Representantes",  len(reps))
        c6.metric("📋 Itens Carteira",  len(df))

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown("#### Resumo por Representante")

        rows = []
        for u in reps:
            my = df[df["vendedor"] == u["vendedor"]] if not df.empty else pd.DataFrame()
            rows.append({
                "Representante": u["name"][:35],
                "Itens": len(my),
                "Carteira R$":  BRL(my["valor_vendido"].sum()    if not my.empty else 0),
                "Atendido R$":  BRL(my["valor_atendido"].sum()   if not my.empty else 0),
                "Saldo R$":     BRL(my["valor_a_entregar"].sum() if not my.empty else 0),
                "m² Carteira":  f"{my['m2_vendido'].sum():,.2f}" if not my.empty else "0,00",
                "m² Saldo":     f"{my['m2_saldo'].sum():,.2f}"   if not my.empty else "0,00",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── PERFORMANCE ──────────────────────────────────────────────
    with tab2:
        render_performance_admin()

    # ── CARTEIRA GERAL ───────────────────────────────────────────
    with tab3:
        section_header("🛒 Carteira Geral", f"{len(pedidos)} itens no total")
        df = pd.DataFrame(pedidos)
        if not df.empty:
            show = df[["pedido","sku","cliente","produto","vendedor","status","uf","m2_vendido","m2_saldo","valor_vendido","valor_a_entregar","emissao"]].copy()
            show.columns = ["Pedido","SKU","Cliente","Produto","Vendedor","Status","UF","m² Vend.","m² Saldo","R$ Vendido","R$ Saldo","Emissão"]
            for col in ["R$ Vendido","R$ Saldo"]:
                show[col] = show[col].apply(BRL)
            st.dataframe(show, use_container_width=True, hide_index=True)

    # ── PRODUTOS ─────────────────────────────────────────────────
    with tab4:
        render_produto_search()

    # ── REPRESENTANTES ───────────────────────────────────────────
    with tab5:
        section_header("👥 Representantes", f"{len(users) - 1} usuários cadastrados")

        # Upload de nova planilha
        with st.expander("📁 Atualizar dados — Upload de Planilha Excel"):
            st.markdown("Suba a planilha `BASE_APP_2.xlsx` (com abas **Estoque** e **Pedidos**) para atualizar os dados.")
            uploaded = st.file_uploader("Escolha o arquivo .xlsx", type=["xlsx","xls"])
            if uploaded:
                with st.spinner("Processando planilha..."):
                    try:
                        novo_est, novo_ped = load_from_excel(uploaded.read())
                        st.session_state.estoque = novo_est
                        st.session_state.pedidos = novo_ped
                        st.success(f"✅ {len(novo_est)} produtos e {len(novo_ped)} pedidos carregados!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar: {e}")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Novo representante
        with st.expander("➕ Cadastrar novo representante"):
            with st.form("new_user_form"):
                c1,c2,c3 = st.columns(3)
                with c1:
                    nome     = st.text_input("Nome *")
                    vendedor = st.text_input("Vendedor (exato na planilha) *")
                with c2:
                    segmento = st.text_input("Segmento")
                    login    = st.text_input("Login *")
                with c3:
                    password = st.text_input("Senha *", type="password")
                    role     = st.selectbox("Perfil", ["rep", "admin"])

                salvar = st.form_submit_button("Salvar ✓", use_container_width=True)
                if salvar:
                    if not all([nome, vendedor, login, password]):
                        st.error("Preencha todos os campos obrigatórios.")
                    elif any(u["login"] == login for u in st.session_state.users):
                        st.error("Login já existe.")
                    else:
                        st.session_state.users.append({
                            "id": max(u["id"] for u in st.session_state.users) + 1,
                            "name": nome, "vendedor": vendedor, "segmento": segmento,
                            "login": login, "password": password, "role": role,
                        })
                        st.success(f"Representante '{nome}' cadastrado!")
                        st.rerun()

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Lista de usuários
        for u in [x for x in st.session_state.users if x["id"] != 1]:
            col1, col2, col3, col4, col5 = st.columns([3, 3, 2, 1.2, 1.2])
            role_color = "#F47920" if u["role"] == "admin" else "#8DC63F"
            col1.markdown(f"<span style='font-weight:700'>{u['name'][:30]}</span>", unsafe_allow_html=True)
            col2.markdown(f"<span style='color:rgba(255,255,255,0.5);font-size:12px'>{u['login']}</span>", unsafe_allow_html=True)
            col3.markdown(f"<span style='background:{role_color}22;color:{role_color};border:1px solid {role_color}55;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:700;text-transform:uppercase'>{u['role']}</span>", unsafe_allow_html=True)

            with col4:
                label = "↓ Rep" if u["role"] == "admin" else "↑ Admin"
                if st.button(label, key=f"toggle_{u['id']}"):
                    for usr in st.session_state.users:
                        if usr["id"] == u["id"]:
                            usr["role"] = "rep" if usr["role"] == "admin" else "admin"
                    st.rerun()

            with col5:
                if st.button("✕ Remover", key=f"del_{u['id']}"):
                    st.session_state.users = [x for x in st.session_state.users if x["id"] != u["id"]]
                    st.rerun()

            st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.05);margin:4px 0'>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    init_state()

    if not st.session_state.logged_in:
        render_login()
        return

    user = st.session_state.current_user
    # Atualiza dados do usuário se mudou (ex: role alterado)
    updated = next((u for u in st.session_state.users if u["id"] == user["id"]), None)
    if updated:
        st.session_state.current_user = updated

    if st.session_state.current_user["role"] == "admin":
        render_admin_dashboard()
    else:
        render_rep_dashboard()


if __name__ == "__main__":
    main()
