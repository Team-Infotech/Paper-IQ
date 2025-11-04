import streamlit as st
import requests
import os
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Prefer environment variable, fall back to st.secrets if present. Accessing
# `st.secrets` can raise when no secrets are configured, so protect it.
API_URL = os.environ.get("PAPERIQ_API_URL", "http://localhost:8000/analyze")
try:
    # If Streamlit secrets exist and provide API_URL, use it; otherwise keep env/default
    API_URL = st.secrets.get("API_URL", API_URL)
except Exception:
    # No secrets configured or access error — keep the environment/default value
    pass

st.set_page_config(page_title="PaperIQ (Full)", layout="wide")
st.title("PaperIQ — AI-Powered Research Insight Analyzer (Full Version)")
st.write("Frontend: Streamlit UI calling FastAPI backend. Make sure the backend is running (uvicorn main:app --reload)")

text = st.text_area("Paste your paper / essay / abstract here", height=300)
col1, col2 = st.columns([1,2])

if st.button("Analyze"):
    if not text or len(text.strip())<20:
        st.warning("Please paste at least 20 characters of text.")
    else:
        try:
            resp = requests.post(API_URL, json={"text": text}, timeout=15)
            if resp.status_code != 200:
                st.error(f"API error: {resp.status_code} - {resp.text}")
            else:
                data = resp.json()
                
                # Main scores tab and visualizations tab
                tab1, tab2 = st.tabs(["📊 Scores & Analysis", "📈 Visualizations"])
                
                with tab1:
                    col1, col2 = st.columns([1,2])
                    with col1:
                        st.metric("PaperIQ (composite)", f"{data['composite']}/100")
                        st.write(f"**Language:** {data['language']}/100")
                        st.write(f"**Coherence:** {data['coherence']}/100")
                        st.write(f"**Reasoning (proxy):** {data['reasoning']}/100")
                    st.markdown('---')
                    st.write('### Detailed Analysis')
                    
                    # Create a more readable mapping of metric names
                    metric_names = {
                        'word_count': 'Total Word Count',
                        'sentence_count': 'Number of Sentences',
                        'avg_sentence_len': 'Average Sentence Length',
                        'avg_word_len': 'Average Word Length',
                        'ttr': 'Vocabulary Diversity Score',
                        'lex_soph': 'Lexical Sophistication',
                        'coherence': 'Coherence Score',
                        'reasoning_proxy': 'Reasoning Assessment'
                    }
                    
                    # Create a formatted explanation for each metric
                    metric_explanations = {
                        'word_count': 'Total number of words in the text',
                        'sentence_count': 'Total number of complete sentences',
                        'avg_sentence_len': 'Words per sentence (ideal: 15-25)',
                        'avg_word_len': 'Average characters per word',
                        'ttr': 'Ratio of unique words to total words (0-1)',
                        'lex_soph': 'Measure of advanced vocabulary usage (0-1)',
                        'coherence': 'Text flow and consistency score (0-1)',
                        'reasoning_proxy': 'Presence of logical connections (0-1)'
                    }

                    # Display metrics with better formatting and explanations
                    for k, v in data['diagnostics'].items():
                        # Format the value based on the metric type
                        if k in ['avg_sentence_len', 'avg_word_len']:
                            formatted_value = f"{v:.2f}"
                        elif k in ['ttr', 'lex_soph', 'coherence', 'reasoning_proxy']:
                            formatted_value = f"{v:.3f}"
                        else:
                            formatted_value = str(v)
                        
                        # Create expander for each metric with details
                        with st.expander(f"**{metric_names[k]}**: {formatted_value}"):
                            st.write(metric_explanations[k])
                            
                            # Add contextual feedback
                            if k == 'avg_sentence_len':
                                if 15 <= v <= 25:
                                    st.success("✓ Ideal sentence length for academic writing")
                                elif v < 15:
                                    st.warning("Consider combining some shorter sentences")
                                else:
                                    st.warning("Consider breaking down some longer sentences")
                            elif k == 'ttr' and v is not None:
                                if v > 0.7:
                                    st.success("✓ Excellent vocabulary diversity")
                                elif v > 0.5:
                                    st.info("Good vocabulary range")
                                else:
                                    st.warning("Consider using more varied vocabulary")
                            elif k == 'coherence' and v is not None:
                                if v > 0.8:
                                    st.success("✓ Strong text coherence")
                                elif v > 0.6:
                                    st.info("Acceptable coherence")
                                else:
                                    st.warning("Consider improving text flow and transitions")
                
                with col2:
                        st.write('### Top flagged sentences')
                        for s in data['top_flagged_sentences']:
                            st.markdown(f"<div style='background-color:#2e7d32;color:white;padding:8px;border-radius:4px;margin:4px 0'>{s}</div>", unsafe_allow_html=True)
                
                with tab2:
                    st.markdown("""
                    ### 📈 Analysis Dashboard
                    This dashboard provides visual insights into your text's characteristics across multiple dimensions.
                    """)

                    # Key metrics at the top with explanations
                    st.markdown("#### 📊 Key Metrics")
                    met1, met2, met3 = st.columns(3)
                    with met1:
                        st.metric("Total Words", data['diagnostics']['word_count'],
                                help="Total number of words in your text")
                    with met2:
                        st.metric("Sentence Count", data['diagnostics']['sentence_count'],
                                help="Number of complete sentences detected")
                    with met3:
                        avg_len = round(data['diagnostics']['avg_sentence_len'], 1)
                        st.metric("Avg. Sentence Length", f"{avg_len} words",
                                help="Average number of words per sentence - Good academic writing typically averages 20-25 words")

                    # Radar chart with improved design
                    st.markdown("#### 🎯 Core Scores Analysis")
                    st.markdown("This radar chart shows how your text performs across the three main assessment dimensions.")
                    
                    scores = {
                        'Category': ['Language\nQuality', 'Coherence\n& Flow', 'Reasoning\nStrength'],
                        'Score': [data['language'], data['coherence'], data['reasoning']]
                    }
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=scores['Score'],
                        theta=scores['Category'],
                        fill='toself',
                        name='Score Distribution',
                        fillcolor='rgba(46, 125, 50, 0.5)',  # Transparent green
                        line=dict(color='#2e7d32', width=2)
                    ))
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100],
                                tickfont=dict(size=12),
                                ticksuffix='%'
                            ),
                            angularaxis=dict(
                                tickfont=dict(size=14, family="Arial, sans-serif")
                            )
                        ),
                        showlegend=False,
                        title=dict(
                            text='Score Distribution by Category',
                            x=0.5,
                            y=0.95,
                            font=dict(size=20)
                        ),
                        margin=dict(t=100, b=50),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Advanced metrics with explanations
                    st.markdown("#### 📐 Advanced Metrics")
                    st.markdown("""
                    These metrics provide deeper insight into your text's sophistication and structure.
                    Hover over the bars for detailed explanations.
                    """)
                    
                    metric_explanations = {
                        'Average Word Length': 'Average number of characters per word. Higher values often indicate more technical/academic language.',
                        'Vocabulary Diversity': 'Ratio of unique words to total words (0-1). Higher values show more diverse vocabulary.',
                        'Language Sophistication': 'Measure of complex word usage (0-1). Higher values indicate more sophisticated language.'
                    }
                    
                    word_metrics = {
                        'Metric': list(metric_explanations.keys()),
                        'Value': [
                            data['diagnostics']['avg_word_len'],
                            data['diagnostics']['ttr'],
                            data['diagnostics']['lex_soph']
                        ],
                        'Explanation': list(metric_explanations.values())
                    }
                    df = pd.DataFrame(word_metrics)
                    
                    fig = px.bar(df, 
                                x='Metric', 
                                y='Value',
                                title='Detailed Language Analysis',
                                labels={'Value': 'Score', 'Metric': ''},
                                color_discrete_sequence=['#1e88e5'],  # Material blue
                                custom_data=['Explanation'])
                                
                    fig.update_traces(
                        hovertemplate="<b>%{x}</b><br>Score: %{y:.2f}<br><br>%{customdata[0]}"
                    )
                    
                    fig.update_layout(
                        title=dict(
                            font=dict(size=20),
                            x=0.5,
                            xanchor='center'
                        ),
                        hoverlabel=dict(
                            bgcolor="white",
                            font_size=14,
                            font_family="Arial"
                        ),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(245,245,245,1)',  # Light gray background
                        yaxis=dict(
                            title="Score",
                            tickformat='.2f',
                            gridcolor='rgba(200,200,200,0.2)',
                            range=[0, max(df['Value']) * 1.2]  # Add 20% padding to top
                        ),
                        xaxis=dict(
                            title="",
                            showgrid=False
                        )
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Add a comparative analysis section
                    if data['diagnostics']['avg_sentence_len'] > 0:
                        st.markdown("#### 📋 Analysis Summary")
                        analysis_col1, analysis_col2 = st.columns(2)
                        
                        with analysis_col1:
                            st.markdown("**Vocabulary Analysis**")
                            vocab_score = data['diagnostics']['ttr'] * 100
                            if vocab_score > 80:
                                st.success("✨ Excellent vocabulary diversity!")
                            elif vocab_score > 60:
                                st.info("👍 Good vocabulary range")
                            else:
                                st.warning("Consider using more varied vocabulary")
                                
                        with analysis_col2:
                            st.markdown("**Sentence Structure**")
                            avg_len = data['diagnostics']['avg_sentence_len']
                            if 15 <= avg_len <= 25:
                                st.success(f"✨ Ideal sentence length ({avg_len:.1f} words)")
                            elif avg_len < 15:
                                st.warning("Sentences may be too short for academic writing")
                            else:
                                st.warning("Consider breaking down some longer sentences")
        except Exception as e:
            st.error(f"Failed to call API: {e}")
