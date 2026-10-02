import hashlib
import importlib.util
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components
from streamlit.components.v1 import html as st_html
from markdown import markdown

ROOT = Path(__file__).resolve().parent
BATCHES = {"IT", "REG", "MED"}
TITLE = "KI-gestützte Systeme im Klinischen Alltag: Erfahrungen und Perspektiven"
st.set_page_config(page_title=TITLE, layout="centered")


def setting(name, default=None):
    value = os.environ.get(name)
    if value is not None:
        return value
    try:
        return st.secrets.get(name, default)
    except FileNotFoundError:
        return default

def load_questions(batch):
    path = ROOT / "questions" / f"{batch}.py"
    if not path.is_file():
        raise ValueError(f"Die Frage-Datei questions/{batch}.py fehlt.")
    spec = importlib.util.spec_from_file_location(f"survey_{batch}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    questions = module.QUESTIONS
    seen = set()
    for question in questions:
        if question["id"] in seen or question["type"] not in {"text", "textarea", "radio", "multiselect"}:
            raise ValueError("Ungültige oder doppelte Frage in der Frage-Datei.")
        seen.add(question["id"])
        if question["type"] in {"radio", "multiselect"} and not question.get("options"):
            raise ValueError("Antwortoptionen fehlen.")
    if not questions:
        raise ValueError("Die Frage-Datei enthält keine Fragen.")
    version = hashlib.sha256(path.read_bytes()).hexdigest()
    return getattr(module, "SCENARIO", ""), questions, version

def response_path(user_id, page):
    # Participant IDs are validated before they are used as directory names.
    return f"{user_id}/{page}.json"

def storage():
    mode = setting("FILESYSTEM", "hf")
    output_dir = setting("OUTPUT_DIR")
    if not output_dir:
        raise ValueError("OUTPUT_DIR ist nicht konfiguriert.")
    if mode == "hf":
        from huggingface_hub import HfFileSystem
        token = setting("HF_TOKEN_WRITE")
        if not token:
            raise ValueError("HF_TOKEN_WRITE ist nicht konfiguriert.")
        if not output_dir.startswith("datasets/"):
            raise ValueError("OUTPUT_DIR muss mit datasets/ beginnen.")
        return HfFileSystem(token=token), output_dir.rstrip("/")
    if mode == "local":
        from fsspec.implementations.local import LocalFileSystem
        return LocalFileSystem(), str(ROOT / output_dir)
    raise ValueError("FILESYSTEM muss hf oder local sein.")

def save_page(page, answers):
    payload = {
        "survey": TITLE, "schema_version": 1,
        "question_version": question_version,
        "user_id": user_id, "batch": batch, "page": page,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "answers": answers,
    }
    try:
        fs, output_dir = storage()
        path = f"{output_dir}/{response_path(user_id, page)}"
        if setting("FILESYSTEM", "hf") == "local":
            fs.makedirs(f"{output_dir}/{user_id}", exist_ok=True)
        with fs.open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
    except Exception:
        st.error("Die Antworten konnten nicht gespeichert werden. Bitte versuchen Sie es erneut. Ihre Eingaben bleiben auf dieser Seite erhalten.")
        return False
    return True

def render_questions(questions, prefix):
    answers, errors = {}, []
    for question in questions:
        condition = question.get("show_if")
        if condition and answers.get(condition[0]) != condition[1]:
            continue
        name = question["id"]
        key = f"{prefix}_{name}"
        label = question["label"] + (" *" if question.get("required", True) else "")
        kind = question["type"]
        if kind == "textarea":
            value = st.text_area(label, key=key)
        elif kind == "text":
            value = st.text_input(label, key=key)
        elif kind == "radio":
            value = st.radio(label, question["options"], index=None, key=key, horizontal=question.get("horizontal", False))
        else:
            value = st.multiselect(label, question["options"], key=key)
        answers[name] = value.strip() if isinstance(value, str) else value
        if question.get("required", True) and answers[name] in (None, "", []):
            errors.append(question["label"])
        other = question.get("other_option")
        selected = other and (other in value if isinstance(value, list) else value == other)
        if selected:
            detail = st.text_input("Sonstige – bitte erläutern:", key=f"{key}_other").strip()
            answers[f"{name}_other"] = detail
            if not detail:
                errors.append("Bitte erläutern Sie Ihre Auswahl bei ‚Sonstige‘.")
    return answers, errors

BACKGROUND = [
    {"id": "profession", "type": "radio", "label": "Was ist Ihre berufliche Tätigkeit?",
     "options": ["Pflegefachperson", "Ärztin / Arzt", "Forscherin / Forscher", "IT-Spezialistin / IT-Spezialist", "Krankenversicherung", "Ethikkommission", "Verwaltung / Management", "Sonstige"], "other_option": "Sonstige"},
    {"id": "experience", "type": "radio", "label": "Wie lange sind Sie in Ihrem Beruf tätig?",
     "options": ["Weniger als 1 Jahr", "1–5 Jahre", "6–10 Jahre", "Mehr als 10 Jahre"]},
    {"id": "ai_use", "type": "radio", "label": "Nutzen Sie KI in Ihren täglichen beruflichen Aktivitäten?", "options": ["Ja", "Nein"]},
    {"id": "ai_purposes", "type": "multiselect", "label": "Für welche Zwecke nutzen Sie KI?", "show_if": ("ai_use", "Ja"),
     "options": ["Schreibunterstützung", "Zusammenfassung", "Aufgabenorganisation", "Wissensunterstützung", "Diagnostik / Therapieunterstützung", "Datenanalyse", "Sonstige"], "other_option": "Sonstige"},
    {"id": "ai_experience", "type": "radio", "label": "Wie schätzen Sie Ihre Erfahrung mit KI ein?",
     "options": ["Keine", "Gering", "Mittel", "Hoch", "Sehr hoch"]},
]

batch = st.query_params.get("batch", "").upper()
if batch not in BATCHES:
    st.error("Bitte öffnen Sie den bereitgestellten Umfragelink mit batch=IT, batch=REG oder batch=MED.")
    st.stop()
user_id = st.query_params.get("user_id", "")
if not user_id:
    user_id = uuid4().hex
    st.query_params["user_id"] = user_id
if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", user_id):
    st.error("Ungültige Teilnehmer-ID im Umfragelink.")
    st.stop()
try:
    scenario, questions, question_version = load_questions(batch)
    consent_text = (ROOT / "consent_form.md").read_text(encoding="utf-8")
except (OSError, ValueError, AttributeError, KeyError) as error:
    st.error(f"Die Umfrage ist noch nicht vollständig eingerichtet: {error}")
    st.stop()

# Start a new session when the participant or questionnaire changes.
identity = (user_id, batch)
if st.session_state.get("identity") != identity:
    st.session_state.clear()
    st.session_state.identity = identity
    st.session_state.page = 0

st.title(TITLE)
page = st.session_state.page
if page == 3:
    st.success("Vielen Dank! Ihre Antworten wurden erfolgreich gespeichert.")
    st.stop()
st.caption(f"Seite {page + 1} von 3 · Mit * markierte Fragen sind erforderlich.")

if page == 0:
    st.subheader("Einwilligung")
    st.markdown(consent_text)
    consent = st.checkbox("Ich habe die Informationen gelesen und willige in die Teilnahme ein.", key="consent")
    answers, errors = {"consent": consent}, [] if consent else ["Bitte bestätigen Sie Ihre Einwilligung."]
elif page == 1:
    st.subheader("Hintergrund und Erfahrung")
    answers, errors = render_questions(BACKGROUND, "background")
else:
    st.subheader("Interviewfragen")
    st.markdown(scenario)
    answers, errors = render_questions(questions, f"survey_{batch}")

if st.button("Antworten absenden" if page == 2 else "Speichern und weiter", type="primary"):
    if errors:
        st.error("Bitte beantworten Sie alle erforderlichen Fragen und ergänzen Sie ausgewählte Sonstige-Antworten.")
    elif save_page(["consent", "background", "survey"][page], answers):
        st.session_state.page += 1
        st.rerun()

