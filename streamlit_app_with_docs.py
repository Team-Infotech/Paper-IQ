import streamlit as st
import requests
import os
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import docx
import PyPDF2
import io

# Prefer environment variable, fall back to st.secrets if present. Accessing
# `st.secrets` can raise when no secrets are configured, so protect it.
API_URL = os.environ.get("PAPERIQ_API_URL", "http://localhost:8000/analyze")
try:
    # If Streamlit secrets exist and provide API_URL, use it; otherwise keep env/default
    API_URL = st.secrets.get("API_URL", API_URL)
except Exception:
    # No secrets configured or access error — keep the environment/default value
    pass

st.set_page_config(page_title="PaperIQ (Full) with Documentation", layout="wide")
st.title("PaperIQ — AI-Powered Research Insight Analyzer")

# Create main navigation
tab_main, tab_docs = st.tabs(["📝 Analysis Tool", "📚 Documentation"])

with tab_main:
    st.markdown("### Upload your document")
    st.markdown("Supported formats: PDF (.pdf) or Word (.docx)")
    
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'docx'])
    text = ""
    
    if uploaded_file is not None:
        try:
            if uploaded_file.type == "application/pdf":
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = docx.Document(uploaded_file)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            text = ""
        
        st.markdown("### Document Preview")
        with st.expander("Show document content"):
            st.text(text[:1000] + ("..." if len(text) > 1000 else ""))

    if st.button("Analyze"):
        if not text or len(text.strip())<20:
            st.warning("Please upload a document with at least 20 characters of text.")
        else:
            try:
                resp = requests.post(API_URL, json={"text": text}, timeout=15)
                if resp.status_code != 200:
                    st.error(f"API error: {resp.status_code} - {resp.text}")
                else:
                    data = resp.json()

                    # Create tabs: scores, visualizations, and sentiment
                    tab1, tab2, tab3 = st.tabs(["📊 Scores & Analysis", "📈 Visualizations", "💭 Sentiment Analysis"])

                    with tab1:
                        col1, col2 = st.columns([1,2])
                        with col1:
                            st.metric("PaperIQ (composite)", f"{data['composite']}/100")
                            st.write(f"**Language:** {data['language']}/100")
                            st.write(f"**Coherence:** {data['coherence']}/100")
                            st.write(f"**Reasoning (proxy):** {data['reasoning']}/100")
                        with col2:
                            st.write('### Top flagged sentences')
                            for s in data.get('top_flagged_sentences', []):
                                st.markdown(f"<div style='background-color:#2e7d32;color:white;padding:8px;border-radius:4px;margin:4px 0'>{s}</div>", unsafe_allow_html=True)

                        st.markdown('---')
                        st.write('### Detailed Analysis')

                        metric_names = {
                            'word_count': 'Total Word Count',
                            'sentence_count': 'Number of Sentences',
                            'avg_sentence_len': 'Average Sentence Length',
                            'avg_word_len': 'Average Word Length',
                            'ttr': 'Vocabulary Diversity Score',
                            'lex_soph': 'Lexical Sophistication',
                            'coherence': 'Coherence Score',
                            'reasoning_proxy': 'Reasoning Assessment',
                            'sentiment_polarity': 'Overall Sentiment',
                            'sentiment_subjectivity': 'Subjectivity Score'
                        }

                        metric_explanations = {
                            'word_count': 'Total number of words in the text',
                            'sentence_count': 'Total number of complete sentences',
                            'avg_sentence_len': 'Words per sentence (ideal: 15-25)',
                            'avg_word_len': 'Average characters per word',
                            'ttr': 'Ratio of unique words to total words (0-1)',
                            'lex_soph': 'Measure of advanced vocabulary usage (0-1)',
                            'coherence': 'Text flow and consistency score (0-1)',
                            'reasoning_proxy': 'Presence of logical connections (0-1)',
                            'sentiment_polarity': 'Sentiment from -1 (negative) to 1 (positive)',
                            'sentiment_subjectivity': 'Subjectivity from 0 (objective) to 1 (subjective)'
                        }

                        for k, v in data.get('diagnostics', {}).items():
                            if k not in metric_names:
                                continue
                            if v is None:
                                formatted_value = 'N/A'
                            elif k in ['avg_sentence_len', 'avg_word_len']:
                                formatted_value = f"{v:.2f}"
                            elif k in ['ttr', 'lex_soph', 'coherence', 'reasoning_proxy', 'sentiment_polarity', 'sentiment_subjectivity']:
                                formatted_value = f"{v:.3f}"
                            else:
                                formatted_value = str(v)

                            with st.expander(f"**{metric_names[k]}**: {formatted_value}"):
                                st.write(metric_explanations[k])
                                if k == 'avg_sentence_len' and isinstance(v, (int, float)):
                                    if 15 <= v <= 25:
                                        st.success("✓ Ideal sentence length for academic writing")
                                    elif v < 15:
                                        st.warning("Consider combining some shorter sentences")
                                    else:
                                        st.warning("Consider breaking down some longer sentences")
                                if k == 'ttr' and v is not None:
                                    if v > 0.7:
                                        st.success("✓ Excellent vocabulary diversity")
                                    elif v > 0.5:
                                        st.info("Good vocabulary range")
                                    else:
                                        st.warning("Consider using more varied vocabulary")
                                if k == 'coherence' and v is not None:
                                    if v > 0.8:
                                        st.success("✓ Strong text coherence")
                                    elif v > 0.6:
                                        st.info("Acceptable coherence")
                                    else:
                                        st.warning("Consider improving text flow and transitions")

                    with tab2:
                        st.markdown("""
                        ### 📈 Analysis Dashboard
                        This dashboard provides visual insights into your text's characteristics across multiple dimensions.
                        """)

                        st.markdown("#### 📊 Key Metrics")
                        met1, met2, met3 = st.columns(3)
                        with met1:
                            st.metric("Total Words", data['diagnostics'].get('word_count', 0), help="Total number of words in your text")
                        with met2:
                            st.metric("Sentence Count", data['diagnostics'].get('sentence_count', 0), help="Number of complete sentences detected")
                        with met3:
                            avg_len = data['diagnostics'].get('avg_sentence_len', 0)
                            try:
                                avg_len_fmt = f"{round(avg_len,1)} words"
                            except Exception:
                                avg_len_fmt = str(avg_len)
                            st.metric("Avg. Sentence Length", avg_len_fmt, help="Average number of words per sentence - Good academic writing typically averages 20-25 words")

                        # Radar chart
                        st.markdown("#### 🎯 Core Scores Analysis")
                        scores = {
                            'Category': ['Language\\nQuality', 'Coherence\\n& Flow', 'Reasoning\\nStrength'],
                            'Score': [data.get('language', 0), data.get('coherence', 0), data.get('reasoning', 0)]
                        }
                        fig = go.Figure()
                        fig.add_trace(go.Scatterpolar(
                            r=scores['Score'],
                            theta=scores['Category'],
                            fill='toself',
                            name='Score Distribution',
                            fillcolor='rgba(46, 125, 50, 0.5)',
                            line=dict(color='#2e7d32', width=2)
                        ))
                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(visible=True, range=[0,100], tickfont=dict(size=12), ticksuffix='%'),
                                angularaxis=dict(tickfont=dict(size=14, family="Arial, sans-serif"))
                            ),
                            showlegend=False,
                            title=dict(text='Score Distribution by Category', x=0.5, y=0.95, font=dict(size=20)),
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
                                data['diagnostics'].get('avg_word_len', 0),
                                data['diagnostics'].get('ttr', 0),
                                data['diagnostics'].get('lex_soph', 0)
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

                    with tab3:
                        st.markdown("### 💭 Sentiment Analysis")
                        st.markdown("This section provides insights into the emotional tone and subjectivity of your text.")

                        # Overall sentiment
                        sent1, sent2 = st.columns(2)
                        with sent1:
                            polarity = data['diagnostics'].get('sentiment_polarity', 0.0)
                            st.metric("Sentiment Polarity", f"{polarity:.2f}", help="Ranges from -1 (negative) to 1 (positive)")
                            if polarity > 0.3:
                                st.success("The text has a positive tone")
                            elif polarity < -0.3:
                                st.error("The text has a negative tone")
                            else:
                                st.info("The text has a neutral tone")
                        with sent2:
                            subjectivity = data['diagnostics'].get('sentiment_subjectivity', 0.0)
                            st.metric("Subjectivity Score", f"{subjectivity:.2f}", help="Ranges from 0 (objective) to 1 (subjective)")
                            if subjectivity > 0.7:
                                st.info("The text is highly subjective")
                            elif subjectivity < 0.3:
                                st.info("The text is mostly objective")
                            else:
                                st.info("The text has a balanced subjective/objective tone")

                        # Sentence-level plot
                        sentences_df = pd.DataFrame(data.get('sentiment_analysis', []))
                        if not sentences_df.empty:
                            fig = px.scatter(sentences_df, x='polarity', y='subjectivity', hover_data=['text'], title='Sentiment Distribution by Sentence')
                            fig.update_traces(marker=dict(size=10, color='#2e7d32', opacity=0.7))
                            fig.update_layout(plot_bgcolor='rgba(245,245,245,1)', paper_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Failed to call API: {e}")

with tab_docs:
    st.markdown("""
    # 📚 PaperIQ Documentation
    
    ## Overview
    PaperIQ is an AI-powered tool designed to analyze and provide insights into academic writing. 
    It evaluates text across multiple dimensions and provides detailed feedback to help improve 
    writing quality.
    
    ## 🎯 Key Features
    
    ### 1. Composite Score
    The overall PaperIQ score combines three main components:
    - **Language Quality** (vocabulary usage, sentence structure)
    - **Coherence** (text flow and organization)
    - **Reasoning** (logical connections and argumentation)
    
    ### 2. Detailed Metrics
    
    #### Language Analysis
    - **Word Count**: Total words in the text
    - **Sentence Count**: Number of complete sentences
    - **Average Sentence Length**: Words per sentence (ideal: 15-25 words)
    - **Average Word Length**: Characters per word
    - **Vocabulary Diversity (TTR)**: Ratio of unique words to total words
    - **Lexical Sophistication**: Measure of advanced vocabulary usage
    
    #### Text Structure
    - **Coherence Score**: Measures how well ideas flow and connect
    - **Reasoning Assessment**: Evaluates logical structure and argumentation
    
    ### 3. Visualizations
    - **Radar Chart**: Shows balance between main components
    - **Bar Charts**: Detailed breakdown of language metrics
    - **Comparative Analysis**: Contextual feedback on writing style
    
    ## 💡 How to Use
    
    1. **Input Your Text**
       - Paste your text in the main text area
       - Minimum 20 characters required
    
    2. **Analyze**
       - Click the "Analyze" button
       - Wait for the analysis to complete
    
    3. **Review Results**
       - Check the main scores
       - Explore detailed metrics
       - Review visualizations
       - Read contextual feedback
    
    ## 📊 Understanding Scores
    
    ### Composite Score (0-100)
    - **90-100**: Exceptional
    - **80-89**: Strong
    - **70-79**: Good
    - **60-69**: Adequate
    - **Below 60**: Needs improvement
    
    ### Component Scores
    Each component (Language, Coherence, Reasoning) is scored from 0-100:
    - **Language**: Evaluates writing mechanics and style
    - **Coherence**: Measures text flow and organization
    - **Reasoning**: Assesses logical structure
    
    ## 🔍 Advanced Metrics Explained
    
    ### Vocabulary Diversity (TTR)
    - **>0.7**: Excellent diversity
    - **0.5-0.7**: Good range
    - **<0.5**: Limited variety
    
    ### Sentence Length
    - **15-25 words**: Ideal for academic writing
    - **<15 words**: May be too brief
    - **>25 words**: Consider breaking down
    
    ## 🚀 Best Practices
    
    1. **For Academic Papers**
       - Aim for sentence length of 15-25 words
       - Maintain high vocabulary diversity
       - Ensure strong coherence between paragraphs
    
    2. **For Technical Writing**
       - Use precise terminology
       - Maintain clear logical structure
       - Balance complexity with clarity
    
    3. **For General Writing**
       - Focus on flow and readability
       - Vary sentence structure
       - Use appropriate vocabulary
    
    ## 🛠️ Technical Details
    
    ### API Endpoint
    - Base URL: {API_URL}
    - Method: POST
    - Payload: JSON with "text" field
    - Response: Analysis results in JSON format
    
    ### Response Structure
    ```python
    {
        "composite": float,  # Overall score
        "language": float,   # Language score
        "coherence": float,  # Coherence score
        "reasoning": float,  # Reasoning score
        "diagnostics": {     # Detailed metrics
            "word_count": int,
            "sentence_count": int,
            "avg_sentence_len": float,
            "avg_word_len": float,
            "ttr": float,
            "lex_soph": float,
            "coherence": float,
            "reasoning_proxy": float
        }
    }
    ```
    """)
