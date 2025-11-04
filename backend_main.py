
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
from typing import List
from textblob import TextBlob

app = FastAPI(title="PaperIQ API", version="0.1")

# --- utilities (same as prototype heuristics) ---
def sentence_split(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.replace('\\n', ' ').strip() for s in sentences if len(s.strip())>0]
    return sentences

def tokenize_words(text):
    words = re.findall(r'\b[\w\']+\b', text.lower())
    return words

def type_token_ratio(words):
    if not words:
        return 0.0
    return len(set(words)) / len(words)

def avg_word_length(words):
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(words)

def avg_sentence_length(sentences):
    if not sentences:
        return 0.0
    lengths = [len(tokenize_words(s)) for s in sentences]
    return sum(lengths) / len(lengths)

def lexical_sophistication(words):
    if not words:
        return 0.0
    long_words = sum(1 for w in words if len(w) > 6)
    return long_words / len(words)

def coherence_score(sentences):
    if not sentences:
        return 0.0
    lens = [len(tokenize_words(s)) for s in sentences]
    mean = sum(lens)/len(lens)
    var = sum((l-mean)**2 for l in lens)/len(lens)
    score = max(0.0, 1.0 - (var / (mean+1)**2))
    return score

def reasoning_proxy(sentences, words):
    causal = sum(1 for s in sentences if re.search(r'\b(because|therefore|thus|hence|consequently|so)\b', s.lower()))
    modal = sum(1 for w in words if w in {"may","might","could","should","would"})
    score = (causal / (len(sentences)+1)) - (modal / (len(words)+1))
    return max(0.0, min(1.0, 0.5 + score))

def compute_features(text):
    sentences = sentence_split(text)
    words = tokenize_words(text)
    features = {}
    features['word_count'] = len(words)
    features['sentence_count'] = len(sentences)
    features['avg_sentence_len'] = avg_sentence_length(sentences)
    features['avg_word_len'] = avg_word_length(words)
    features['ttr'] = type_token_ratio(words)
    features['lex_soph'] = lexical_sophistication(words)
    features['coherence'] = coherence_score(sentences)
    features['reasoning_proxy'] = reasoning_proxy(sentences, words)
    
    # Add sentiment analysis
    blob = TextBlob(text)
    features['sentiment_polarity'] = blob.sentiment.polarity
    features['sentiment_subjectivity'] = blob.sentiment.subjectivity
    
    # Sentence-level sentiment
    sentence_sentiments = []
    for sentence in sentences:
        sent_blob = TextBlob(sentence)
        sentence_sentiments.append({
            'text': sentence,
            'polarity': sent_blob.sentiment.polarity,
            'subjectivity': sent_blob.sentiment.subjectivity
        })
    
    return features, sentences, words, sentence_sentiments

def score_paper(features):
    lang = 100 * (0.2*min(1.0, features['ttr']*1.5) + 0.3*min(1.0, features['lex_soph']*3) + 0.5*min(1.0, features['avg_word_len']/5))
    coh = 100 * features['coherence']
    reason = 100 * features['reasoning_proxy']
    composite = round((0.4*lang + 0.3*coh + 0.3*reason), 2)
    return {
        'language': round(lang,2),
        'coherence': round(coh,2),
        'reasoning': round(reason,2),
        'composite': composite
    }

def sentence_contributions(sentences, overall_features):
    contributions = []
    for s in sentences:
        words = tokenize_words(s)
        if not words:
            contributions.append((s, 0.0))
            continue
        ttr = len(set(words))/len(words)
        long = 1.0 if len(words) > max(40, overall_features['avg_sentence_len']*2) else 0.0
        causal = 1.0 if re.search(r'\b(because|therefore|thus|hence|consequently|so)\b', s.lower()) else 0.0
        neg = 0.0
        neg += long * 1.2
        neg += (1.0 - ttr) * 1.0
        neg += (1.0 - causal) * 0.5
        contributions.append((s, neg))
    contributions.sort(key=lambda x: x[1], reverse=True)
    return contributions

# --- API models ---
class AnalyzeRequest(BaseModel):
    text: str

class SentimentInfo(BaseModel):
    text: str
    polarity: float
    subjectivity: float

class AnalyzeResponse(BaseModel):
    composite: float
    language: float
    coherence: float
    reasoning: float
    diagnostics: dict
    top_flagged_sentences: List[str]
    sentiment_analysis: List[SentimentInfo]

@app.post('/analyze', response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    text = req.text or ''
    if len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail='Text too short. Provide at least 20 characters.')
    features, sentences, words, sentence_sentiments = compute_features(text)
    scores = score_paper(features)
    contribs = sentence_contributions(sentences, features)
    top_flagged = [s for s, _ in contribs[:5]]
    
    # Convert sentence sentiments to response model
    sentiment_analysis = [
        SentimentInfo(
            text=s['text'],
            polarity=s['polarity'],
            subjectivity=s['subjectivity']
        ) for s in sentence_sentiments
    ]
    
    resp = AnalyzeResponse(
        composite = scores['composite'],
        language = scores['language'],
        coherence = scores['coherence'],
        reasoning = scores['reasoning'],
        diagnostics = features,
        top_flagged_sentences = top_flagged,
        sentiment_analysis = sentiment_analysis
    )
    return resp
