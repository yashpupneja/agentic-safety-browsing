#!/usr/bin/env python3

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import streamlit as st

from src.utils.llm_client import LLMClient
from src.processors.untrusted_input_processor import UntrustedInputProcessor
from src.agents.operator_critic import OperatorAgent, CriticAgent
from src.policy.engine import PolicyEngine
from src.agents.baseline_agent import BaselineAgent


def load_attack_files() -> Dict[str, str]:
    attacks_dir = project_root / 'data' / 'attacks'
    attacks_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    for p in sorted(attacks_dir.glob('attack_*.html')):
        title = p.stem.replace('_', ' ').title()
        files[p.name] = title
    return files


def run_eval(attack_file: str, user_query: str, model: str) -> Dict:
    html = (project_root / 'data' / 'attacks' / attack_file).read_text(encoding='utf-8')

    os.environ['OPENAI_MODEL'] = model

    vuln_start = time.time()
    client = LLMClient(model=model)
    processor = UntrustedInputProcessor()
    operator = OperatorAgent()
    critic = CriticAgent()
    policy = PolicyEngine()

    # Vulnerable baseline agent path
    try:
        baseline = BaselineAgent()
        vuln_resp = baseline.act(page_content=html[:4000], user_query=user_query).text
    except Exception as e:
        vuln_resp = f"Error: {e}"
    vuln_ms = (time.time() - vuln_start) * 1000

    # Protected path
    prot_start = time.time()
    processed = processor.process(html, attack_file)
    proposed = operator.propose_intent(processed.summary, user_query)
    risk = critic.assess_risk(proposed, processed.risk_signals)
    decision = policy.evaluate_intent(proposed.intent, risk.risk_score, risk.flags)
    prot_ms = (time.time() - prot_start) * 1000

    return {
        'vulnerable': {
            'response': vuln_resp,
            'latency_ms': vuln_ms
        },
        'protected': {
            'signals': processed.risk_signals,
            'intent': proposed.intent[:160],
            'risk': risk.risk_score,
            'policy': decision.decision,
            'latency_ms': prot_ms
        }
    }


def main():
    st.set_page_config(page_title='Separating Control and Data Planes for Safe Agentic Browsing', page_icon='🛡️', layout='wide')
    st.title('🛡️ Separating Control and Data Planes for Safe Agentic Browsing')
    st.caption('Control–data plane separation demo')

    st.sidebar.header('API')
    api_key = st.sidebar.text_input('OpenRouter API Key', type='password')
    if api_key:
        os.environ['OPENROUTER_API_KEY'] = api_key

    st.sidebar.header('Config')
    attacks = load_attack_files()
    attack = st.sidebar.selectbox('Attack', list(attacks.keys()))
    user_query = st.sidebar.text_area('User Query', 'Summarize this content safely', height=80)
    model = st.sidebar.selectbox('Model', ['openai/gpt-4o-mini', 'openai/gpt-4o', 'qwen/qwen-2.5-7b-instruct'])

    if st.button('Run Evaluation'):
        if not os.getenv('OPENROUTER_API_KEY'):
            st.error('Set OPENROUTER_API_KEY or enter in sidebar')
            st.stop()
        with st.spinner('Evaluating...'):
            res = run_eval(attack, user_query, model)
        st.subheader('Vulnerable Agent')
        st.code(res['vulnerable']['response'][:1500])
        st.write(f"Latency: {res['vulnerable']['latency_ms']:.0f} ms")

        st.subheader('Protected Agent')
        st.write(f"Signals: {', '.join(res['protected']['signals'])}")
        st.write(f"Intent: {res['protected']['intent']}")
        st.write(f"Risk: {res['protected']['risk']}")
        st.write(f"Policy: {res['protected']['policy']}")
        st.write(f"Latency: {res['protected']['latency_ms']:.0f} ms")


if __name__ == '__main__':
    main()
