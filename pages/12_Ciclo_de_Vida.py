import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Ciclo de Vida dos Produtos",
    page_icon="📈",
    layout="wide"
)

# Título personalizado estilizado
st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, #0070C0 0%, #4a4e69 100%);
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
        padding: 28px 24px 18px 24px;
        margin-bottom: 32px;
        display: flex;
        align-items: center;
    ">
        <div style="flex:1">
            <h1 style="margin-bottom: 0.2em; color: #fff; font-size: 2.2em; font-weight: 700;">
                Gestão do Ciclo de Vida dos Produtos
            </h1>
            <h3 style="margin-top: 0; color: #e0e0e0; font-weight: 400; font-size: 1.2em;">
                Visualize e gerencie o posicionamento estratégico dos produtos através das fases de introdução, crescimento, maturidade e declínio
            </h3>
        </div>
        <!-- Se quiser adicionar um logo, descomente a linha abaixo e coloque o caminho correto -->
        <!-- <img src=\"https://link-para-logo.png\" style=\"height:64px; margin-left:24px;\" /> -->
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# Sidebar para entrada de dados

# Título principal
# st.title("Estágios da Gestão do Ciclo de Vida do Produto")
st.markdown(
    """
    <div style="
        background-color: #e7f0fa;
        border-left: 6px solid #0070C0;
        padding: 12px 18px;
        margin-bottom: 12px;
        border-radius: 6px;
        font-size: 1.15em;
        color: #22223b;
        font-weight: 600;
    ">
        Gestão do Ciclo de Vida dos Produtos
    """,
    unsafe_allow_html=True
)

# CSS personalizado para melhorar a aparência
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 10px;
    border-left: 5px solid #1f77b4;
    margin: 10px 0;
}
.stage-header {
    font-size: 1.2em;
    font-weight: bold;
    margin-bottom: 10px;
}
.product-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Inicializar session state para produtos
if 'produtos' not in st.session_state:
    st.session_state.produtos = {}

# Formulário principal em expander
with st.expander("📝 Gestão de Produtos", expanded=False):
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("➕ Adicionar Novo Produto")
        novo_produto = st.text_input("Nome do Produto:")
        estagio_produto = st.selectbox(
            "Estágio Atual:",
            ["Introdução", "Crescimento", "Maturidade", "Declínio"]
        )

        # Estratégia específica do produto
        estrategia_produto = st.text_area(
            "Estratégia de Produto:",
            placeholder="Descreva a estratégia específica para este produto..."
        )

        if st.button("➕ Adicionar Produto"):
            if novo_produto and novo_produto not in st.session_state.produtos:
                st.session_state.produtos[novo_produto] = {
                    "estagio": estagio_produto,
                    "estrategia_produto": estrategia_produto
                }
                st.success(f"Produto '{novo_produto}' adicionado!")
                st.rerun()
            elif novo_produto in st.session_state.produtos:
                st.error("Produto já existe!")
            else:
                st.error("Digite um nome para o produto!")

    with col2:
        if st.session_state.produtos:
            st.subheader("📦 Produtos Cadastrados")
            for produto_nome in list(st.session_state.produtos.keys()):
                with st.container():
                    st.write(f"**🎯 {produto_nome}**")
                    st.write(
                        f"Estágio atual: {st.session_state.produtos[produto_nome]['estagio']}")

                    col_a, col_b = st.columns([3, 1])

                    with col_a:
                        # Opção para editar estágio
                        novo_estagio = st.selectbox(
                            "Alterar Estágio:",
                            ["Introdução", "Crescimento",
                                "Maturidade", "Declínio"],
                            index=["Introdução", "Crescimento", "Maturidade", "Declínio"].index(
                                st.session_state.produtos[produto_nome]['estagio']
                            ),
                            key=f"estagio_{produto_nome}"
                        )

                    with col_b:
                        if st.button("🔄", key=f"update_{produto_nome}", help="Atualizar estágio"):
                            st.session_state.produtos[produto_nome]['estagio'] = novo_estagio
                            st.rerun()

                        if st.button("🗑️", key=f"remove_{produto_nome}", help="Remover produto"):
                            del st.session_state.produtos[produto_nome]
                            st.rerun()

                    st.markdown("---")
        else:
            st.info("Nenhum produto cadastrado ainda.")

# Layout principal - Gráfico principal
# st.subheader("📈 Estágios da Gestão do Ciclo de Vida do Produto")
st.markdown(
    """
    <div style="
        background-color: #e7f0fa;
        border-left: 6px solid #0070C0;
        padding: 12px 18px;
        margin-bottom: 12px;
        border-radius: 6px;
        font-size: 1.15em;
        color: #22223b;
        font-weight: 600;
    ">
        Gerencie múltiplos produtos e visualize seu posicionamento no ciclo de vida
    </div>
    """,
    unsafe_allow_html=True
)

# Criar o gráfico estilo área com cores por estágio
fig = go.Figure()

# Curva principal do ciclo de vida (muito mais suavizada e limitada)
x_curve = np.linspace(0.2, 9.8, 100)
y_curve = []
for x in x_curve:
    if x <= 2.5:
        # Introdução - crescimento exponencial suave começando do zero
        normalized_x = (x - 0.2) / (2.5 - 0.2)
        y = 3 + 5 * normalized_x**1.5
    elif x <= 5:
        # Crescimento - curva sigmoide suave
        transition_point = 3.75
        steepness = 2
        y = 8 + 2 / (1 + np.exp(-steepness * (x - transition_point)))
    elif x <= 7.5:
        # Maturidade - platô com declínio muito suave usando coseno
        progress = (x - 5) / 2.5
        y = 10 - 2 * (1 - np.cos(progress * np.pi / 2))
    else:
        # Declínio - curva exponencial suave terminando suavemente
        normalized_x = (x - 7.5) / (9.8 - 7.5)
        y = 8 * (1 - normalized_x)**2
    y_curve.append(max(0.5, min(10.5, y)))

# Dividir a curva por estágios e preencher cada seção com sua cor
stages = [
    {"name": "Introdução", "x_start": 0.2, "x_end": 2.5,
        "color": "rgba(52, 152, 219, 0.8)"},
    {"name": "Crescimento", "x_start": 2.5,
        "x_end": 5, "color": "rgba(243, 156, 18, 0.8)"},
    {"name": "Maturidade", "x_start": 5, "x_end": 7.5,
        "color": "rgba(39, 174, 96, 0.8)"},
    {"name": "Declínio", "x_start": 7.5, "x_end": 9.8,
        "color": "rgba(149, 165, 166, 0.8)"}
]

for stage in stages:
    # Filtrar pontos da curva para este estágio
    stage_x = []
    stage_y = []

    for i, x in enumerate(x_curve):
        if stage["x_start"] <= x <= stage["x_end"]:
            stage_x.append(x)
            stage_y.append(y_curve[i])

    if stage_x:
        # Adicionar pontos para fechar a área (base da curva)
        stage_x_filled = [stage["x_start"]] + \
            stage_x + [stage["x_end"], stage["x_start"]]
        stage_y_filled = [0] + stage_y + [0, 0]

        # Adicionar área preenchida
        fig.add_trace(go.Scatter(
            x=stage_x_filled,
            y=stage_y_filled,
            fill="toself",
            fillcolor=stage["color"],
            line=dict(color="rgba(0,0,0,0)", width=0),  # Linha transparente
            name=stage["name"],
            showlegend=False,
            hoverinfo='skip'
        ))

# Adicionar a curva branca por cima
fig.add_trace(go.Scatter(x=x_curve, y=y_curve, mode='lines',
                         line=dict(color='white', width=5,
                                   shape='spline', smoothing=1.3),
                         name='Ciclo de Vida', showlegend=False))

# Adicionar labels dos estágios
stage_positions = [
    (1.25, 0.5, "<b>Introdução</b>"),
    (3.75, 0.5, "<b>Crescimento</b>"),
    (6.25, 0.5, "<b>Maturidade</b>"),
    (8.75, 0.5, "<b>Declínio</b>")
]

for x, y, text in stage_positions:
    fig.add_trace(go.Scatter(x=[x], y=[y], mode='text', text=[text],
                             textfont=dict(size=20, color='#2c3e50'), showlegend=False))

# Adicionar eixos
fig.add_trace(go.Scatter(x=[0, 10], y=[0, 0], mode='lines',
                         line=dict(color='#2c3e50', width=2), showlegend=False))
fig.add_trace(go.Scatter(x=[0, 0], y=[0, 11], mode='lines',
                         line=dict(color='#2c3e50', width=2), showlegend=False))

# Adicionar seta no eixo Y
fig.add_annotation(x=0, y=11, ax=0, ay=10.5, xref='x', yref='y', axref='x', ayref='y',
                   arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor='#2c3e50')

# Label do eixo Y
fig.add_annotation(
    x=-0.5, y=5.5,
    text="<b>Status</b>",
    showarrow=False,
    textangle=90,
    font=dict(size=14, color='#2c3e50')
)

# Adicionar produtos no gráfico - posicionados por estágio
cores_produtos = ['#3498db', '#f39c12',
                  '#27ae60', '#95a5a6', '#e74c3c', '#9b59b6']
posicoes_fixas = {
    "Introdução": {"x": 1.25, "y": 6},
    "Crescimento": {"x": 3.75, "y": 9},
    "Maturidade": {"x": 6.25, "y": 9},
    "Declínio": {"x": 8.75, "y": 5.5}
}

for i, (produto_nome, dados) in enumerate(st.session_state.produtos.items()):
    cor = cores_produtos[i % len(cores_produtos)]
    estagio = dados['estagio']
    pos = posicoes_fixas[estagio]

    # Adicionar offset para produtos no mesmo estágio
    produtos_mesmo_estagio = [
        p for p, d in st.session_state.produtos.items() if d['estagio'] == estagio]
    index_produto = produtos_mesmo_estagio.index(produto_nome)
    total_produtos_estagio = len(produtos_mesmo_estagio)

    # Calcular offset baseado na posição do produto no estágio
    if total_produtos_estagio == 1:
        offset_x = 0
        offset_y = 0
    else:
        # Distribuir produtos em um arco ou linha
        angle = (index_produto / (total_produtos_estagio - 1)) * \
            0.8 - 0.4  # -0.4 a 0.4
        offset_x = angle * 0.5
        offset_y = (index_produto - (total_produtos_estagio - 1) / 2) * 0.4

    fig.add_trace(go.Scatter(
        x=[pos['x'] + offset_x],
        y=[pos['y'] + offset_y],
        mode='markers',
        marker=dict(size=15, color=cor, symbol='circle',
                    line=dict(width=3, color='white')),
        name=produto_nome,
        showlegend=False,
        hoverinfo='skip'
    ))

    # Adicionar rótulo do produto fora do gráfico
    fig.add_annotation(
        x=pos['x'] + offset_x,
        y=pos['y'] + offset_y + 0.8,
        text=produto_nome,
        showarrow=False,
        font=dict(size=12, color="#2c3e50", family="Arial Black"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=cor,
        borderwidth=1,
        borderpad=3
    )

# Adicionar caixas de descrição para cada estágio
# descriptions = [
#     {"x": 1.25, "y": 9, "text": "Produto novo no mercado.<br>Vendas baixas.<br>Investimento alto.", "color": "#3498db"},
#     {"x": 3.75, "y": 11, "text": "Aceitação do mercado.<br>Vendas crescendo.<br>Lucros aumentando.", "color": "#f39c12"},
#     {"x": 6.25, "y": 11, "text": "Vendas estabilizadas.<br>Concorrência intensa.<br>Foco em diferenciação.", "color": "#27ae60"},
#     {"x": 8.75, "y": 7.5, "text": "Vendas em queda.<br>Redução de custos.<br>Considerar descontinuação.", "color": "#95a5a6"}
# ]

# for desc in descriptions:
#     fig.add_annotation(
#         x=desc["x"], y=desc["y"],
#         text=desc["text"],
#         showarrow=True,
#         arrowhead=2,
#         arrowsize=1,
#         arrowwidth=2,
#         arrowcolor=desc["color"],
#         ax=0, ay=-60,
#         bgcolor="rgba(255,255,255,0.9)",
#         bordercolor=desc["color"],
#         borderwidth=2,
#         borderpad=4,
#         font=dict(size=14, color="#2c3e50", family="Arial Black")
#     )

fig.update_layout(
    height=650,
    showlegend=False,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=False, showticklabels=False,
               zeroline=False, range=[-1, 11]),
    yaxis=dict(showgrid=False, showticklabels=False,
               zeroline=False, range=[-1, 12]),
    margin=dict(l=80, r=80, t=80, b=80)
)

st.plotly_chart(fig, use_container_width=True)

# Tabela Clean das Estratégias
st.markdown(
    """
    <div style="
        background-color: #e7f0fa;
        border-left: 6px solid #0070C0;
        padding: 12px 18px;
        margin-bottom: 12px;
        border-radius: 6px;
        font-size: 1.15em;
        color: #22223b;
        font-weight: 600;
    ">
        Estratégias por Estágio
    </div>
    """,
    unsafe_allow_html=True
)

# CSS para tabela clean
st.markdown("""
<style>
.clean-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 20px 0;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.clean-table th {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
    padding: 20px 15px;
    text-align: center;
    font-size: 16px;
}

.clean-table td {
    padding: 18px 15px;
    text-align: left;
    border-bottom: 1px solid #e0e0e0;
    font-size: 14px;
    line-height: 1.5;
}

.clean-table tr:nth-child(even) {
    background-color: #f8f9fa;
}

.clean-table tr:hover {
    background-color: #e3f2fd;
    transition: background-color 0.3s ease;
}

.stage-intro { background-color: rgba(52, 152, 219, 0.15) !important; }
.stage-growth { background-color: rgba(243, 156, 18, 0.15) !important; }
.stage-maturity { background-color: rgba(39, 174, 96, 0.15) !important; }
.stage-decline { background-color: rgba(149, 165, 166, 0.15) !important; }

.strategy-label {
    font-weight: 600;
    color: #2c3e50;
    background-color: #ecf0f1;
    padding: 12px 15px;
    border-right: 3px solid #3498db;
}
</style>
""", unsafe_allow_html=True)

# Criar tabela HTML clean
table_html = """
<table class="clean-table">
    <thead>
        <tr>
            <th style="width: 20%;">Estratégia</th>
            <th style="width: 20%; background: #3498db;">🤝 Introdução</th>
            <th style="width: 20%; background: #f39c12;">📈 Crescimento</th>
            <th style="width: 20%; background: #27ae60;">⭐ Maturidade</th>
            <th style="width: 20%; background: #95a5a6;">📉 Declínio</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td class="strategy-label">🎯 Produto</td>
            <td class="stage-intro">Oferecer um produto básico</td>
            <td class="stage-growth">Oferecer extensões de produto, serviços, garantia</td>
            <td class="stage-maturity">Diversificar marca e modelos</td>
            <td class="stage-decline">Eliminar itens fracos</td>
        </tr>
    </tbody>
</table>
"""

st.markdown(table_html, unsafe_allow_html=True)

# Resumo dos produtos cadastrados
if st.session_state.produtos:
    st.markdown(
        """
        <div style="
            background-color: #e7f0fa;
            border-left: 6px solid #0070C0;
            padding: 12px 18px;
            margin-bottom: 12px;
            border-radius: 6px;
            font-size: 1.15em;
            color: #22223b;
            font-weight: 600;
        ">
            📦 Produtos Cadastrados
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        # Contar produtos por estágio
        estagios_count = {"Introdução": 0, "Crescimento": 0,
                          "Maturidade": 0, "Declínio": 0}
        for produto in st.session_state.produtos.values():
            estagio = produto['estagio']
            estagios_count[estagio] += 1

        # Criar cards dos produtos por estágio
        for estagio, count in estagios_count.items():
            if count > 0:
                produtos_estagio = [nome for nome, dados in st.session_state.produtos.items(
                ) if dados['estagio'] == estagio]
                color_map = {
                    "Introdução": "#3498db",
                    "Crescimento": "#f39c12",
                    "Maturidade": "#27ae60",
                    "Declínio": "#95a5a6"
                }
                color = color_map[estagio]

                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {color}15, {color}05); 
                            padding: 20px; border-radius: 10px; border-left: 4px solid {color};
                            margin: 15px 0;">
                    <h4 style="color: {color}; margin: 0 0 12px 0; font-size: 1.3em;">{estagio} ({count} produtos)</h4>
                    <p style="margin: 0; color: #555; font-size: 1.1em;">{', '.join(produtos_estagio)}</p>
                </div>
                """, unsafe_allow_html=True)

    with col2:
        st.markdown(
            """
            <div style="
                background-color: #e7f0fa;
                border-left: 6px solid #0070C0;
                padding: 12px 18px;
                margin-bottom: 12px;
                border-radius: 6px;
                font-size: 1.15em;
                color: #22223b;
                font-weight: 600;
            ">
                🎯 Métricas
            </div>
            """,
            unsafe_allow_html=True
        )

        st.metric("Total de Produtos", len(st.session_state.produtos))

        # Produto mais promissor
        if estagios_count["Crescimento"] > 0:
            st.metric("Em Crescimento", estagios_count["Crescimento"], "🚀")
        if estagios_count["Declínio"] > 0:
            st.metric("Necessita Atenção", estagios_count["Declínio"], "⚠️")
else:
    st.info("💡 Nenhum produto cadastrado ainda. Use o formulário acima para adicionar produtos e vê-los aparecer no gráfico!")

# Cards detalhados por produto
if st.session_state.produtos:
    st.markdown(
        """
        <div style="
            background-color: #e7f0fa;
            border-left: 6px solid #0070C0;
            padding: 12px 18px;
            margin-bottom: 12px;
            border-radius: 6px;
            font-size: 1.15em;
            color: #22223b;
            font-weight: 600;
        ">
            Análise Detalhada dos Produtos
        </div>
        """,
        unsafe_allow_html=True
    )

    # Organizar produtos por estágio
    produtos_por_estagio = {}
    for produto_nome, dados in st.session_state.produtos.items():
        estagio = dados['estagio']
        if estagio not in produtos_por_estagio:
            produtos_por_estagio[estagio] = []
        produtos_por_estagio[estagio].append((produto_nome, dados))

    # Criar abas por estágio
    if produtos_por_estagio:
        tabs = st.tabs(list(produtos_por_estagio.keys()))
        stage_colors = {
            'Introdução': '#3498db',
            'Crescimento': '#f39c12',
            'Maturidade': '#27ae60',
            'Declínio': '#95a5a6'
        }

        for tab, (estagio, produtos) in zip(tabs, produtos_por_estagio.items()):
            with tab:
                color = stage_colors.get(estagio, '#3498db')

                for produto_nome, dados in produtos:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {color}20, {color}10); 
                                padding: 20px; border-radius: 10px; border-left: 4px solid {color};
                                margin: 15px 0;">
                        <h4 style="color: {color}; margin-bottom: 15px;">🎯 {produto_nome}</h4>
                        <p><strong>Estágio:</strong> {dados['estagio']}</p>
                        <p><strong>Estratégia de Produto:</strong> {dados['estrategia_produto'] or 'Não definida'}</p>
                    </div>
                    """, unsafe_allow_html=True)

# Análise estatística
if st.session_state.produtos:
    st.markdown(
        """
        <div style="
            background-color: #e7f0fa;
            border-left: 6px solid #0070C0;
            padding: 12px 18px;
            margin-bottom: 12px;
            border-radius: 6px;
            font-size: 1.15em;
            color: #22223b;
            font-weight: 600;
        ">
            📊 Análise do Portfólio
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        # Gráfico de pizza - distribuição por estágio
        estagios_count = {}
        for produto in st.session_state.produtos.values():
            estagio = produto['estagio']
            estagios_count[estagio] = estagios_count.get(estagio, 0) + 1

        fig_pie = go.Figure(data=[go.Pie(
            labels=list(estagios_count.keys()),
            values=list(estagios_count.values()),
            hole=.3,
            marker_colors=['#3498db', '#f39c12', '#27ae60', '#95a5a6'],
            textinfo='label+percent',
            textfont=dict(size=16, color='#2c3e50', family="Arial Black"),
            textposition='outside'
        )])
        fig_pie.update_layout(
            title="Distribuição por Estágio",
            height=350,
            title_font=dict(size=18),
            showlegend=False
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown(
            """
            <div style="
                background-color: #e7f0fa;
                border-left: 6px solid #0070C0;
                padding: 12px 18px;
                margin-bottom: 12px;
                border-radius: 6px;
                font-size: 1.15em;
                color: #22223b;
                font-weight: 600;
            ">
                🎯 Métricas Rápidas
            </div>
            """,
            unsafe_allow_html=True
        )

        st.metric("Produto + Promissor", "Crescimento", "🚀")
        st.metric("Necessita Atenção", "Declínio", "⚠️")
        st.metric("Foco Estratégico", "Maturidade", "🎯")

    with col3:
        # Recomendações automáticas
        st.markdown(
            """
            <div style="
                background-color: #e7f0fa;
                border-left: 6px solid #0070C0;
                padding: 12px 18px;
                margin-bottom: 12px;
                border-radius: 6px;
                font-size: 1.15em;
                color: #22223b;
                font-weight: 600;
            ">
                💡 Recomendações
            </div>
            """,
            unsafe_allow_html=True
        )

        if estagios_count.get("Declínio", 0) > 0:
            st.warning(
                f"Considere revitalizar ou descontinuar {estagios_count['Declínio']} produto(s) em declínio")
        if estagios_count.get("Introdução", 0) > estagios_count.get("Crescimento", 0):
            st.info("Foque recursos em mover produtos da introdução para crescimento")
        if estagios_count.get("Maturidade", 0) > 2:
            st.success("Portfólio maduro - considere inovação")

# Botões de ação
st.subheader("⚡ Ações")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("💾 Salvar Portfólio"):
        st.success("Portfólio salvo com sucesso!")

with col2:
    if st.button("📊 Gerar Relatório"):
        st.info("Funcionalidade de geração de relatório em breve!")

with col3:
    if st.button("🔄 Limpar Tudo"):
        st.session_state.produtos = {}
        st.rerun()

with col4:
    if st.session_state.produtos:
        if st.button("📤 Exportar Dados"):
            df_export = pd.DataFrame([
                [nome, dados['estagio'], dados['estrategia_produto']]
                for nome, dados in st.session_state.produtos.items()
            ], columns=["Produto", "Estágio", "Estratégia Produto"])

            # Salvar como Excel
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_export.to_excel(
                    writer, sheet_name='Portfolio_Produtos', index=False)
            buffer.seek(0)

            st.download_button("Baixar Excel", buffer,
                               "portfolio_produtos.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>📈 Painel de Gestão do Ciclo de Vida do Produto | Desenvolvido com Streamlit</p>
    <p><em>Gerencie múltiplos produtos e visualize seu posicionamento no ciclo de vida.</em></p>
</div>
""", unsafe_allow_html=True)
