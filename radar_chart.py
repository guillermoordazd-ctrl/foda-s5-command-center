import plotly.graph_objects as go

def crear_radar_foda(df_f, df_o, df_d, df_a):
    """
    Crea un gráfico de radar con los valores promedio (Peso*10) de cada cuadrante.
    Recibe DataFrames con columnas ['Factor','Peso','Calificación'].
    """
    # Calcular promedio ponderado simple: (Peso * Calificación) medio, luego escalar *10
    def valor(df):
        if df.empty:
            return 0
        return (df['Peso'] * df['Calificación']).mean() * 10

    r_vals = [
        valor(df_f),
        valor(df_o),
        valor(df_d),
        valor(df_a),
        valor(df_f)  # cerrar el gráfico
    ]
    categorias = ['F (Fortalezas)', 'O (Oportunidades)', 'D (Debilidades)', 'A (Amenazas)', '']

    fig = go.Figure(data=go.Scatterpolar(
        r=r_vals,
        theta=categorias,
        fill='toself',
        fillcolor='rgba(0, 242, 255, 0.2)',
        line=dict(color='#00f2ff', width=2)
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=False, range=[0, max(r_vals)*1.1 if max(r_vals)>0 else 10])
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#00f2ff"),
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    return fig