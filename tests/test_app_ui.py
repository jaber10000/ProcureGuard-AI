from pathlib import Path
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')
PAGES = ['Dashboard Overview', 'Upload Documents', 'All Documents', 'Approved', 'Rejected', 'Human Review', 'Purchase Request', 'Reports & Analytics']

@pytest.fixture
def at(tmp_path, monkeypatch):
    monkeypatch.setenv('PROCUREGUARD_STORAGE', str(tmp_path / 's'))
    st.cache_resource.clear()
    a = AppTest.from_file(APP, default_timeout=60); a.run()
    assert not a.exception
    return a

def test_every_page_renders(at):
    for p in PAGES:
        at.session_state['nav'] = p; at.run()
        assert not at.exception, (p, at.exception)

def test_dashboard_card_navigates_to_status_page(at):
    btn = next(b for b in at.button if b.key == 'stat_Rejected'); btn.click(); at.run()
    assert at.session_state['nav'] == 'Rejected' and not at.exception
    assert '5' in at.caption[0].value  # "5 Documents"

def test_open_detail_from_approved_card(at):
    at.session_state['nav'] = 'Approved'; at.run()
    next(b for b in at.button if b.key.startswith('open_Approved_')).click(); at.run()
    assert not at.exception and at.session_state['selected_doc'] is not None
    assert any('All rules passed' in s.value for s in at.success)

def test_human_review_form_saves_decision(at):
    at.session_state['nav'] = 'Human Review'; at.run()
    at.sidebar.text_input[0].set_value('Rahim Uddin').run()
    form_btn = at.button[0]
    assert form_btn.label == 'Submit Review Decision'
    at.text_area[0].set_value('ok').run()
    at.button[0].click().run()
    assert not at.exception
    assert 'Decision saved' in at.success[0].value
    assert at.session_state['nav'] == 'Human Review'
    assert any('Approved  (3)' in o for o in at.sidebar.radio[0].options)
    assert any('Human Review  (2)' in o for o in at.sidebar.radio[0].options)

def test_review_requires_name(at):
    at.session_state['nav'] = 'Human Review'; at.run()
    at.button[0].click().run()
    assert any('name is required' in e.value for e in at.error)
