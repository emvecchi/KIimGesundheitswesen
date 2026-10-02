"""IT interview questions. REG.py and MED.py use the same schema."""

SCENARIO = """
Es soll in Ihrem Krankenhaus ein neues KI-gestütztes System eingeführt werden.
Das System ist zugelassen und hat einen nachweislichen Nutzen. Es ist
DSGVO-konform, ist nach aktuellem Stand regulatorisch konform und ein
MDR-zertifiziertes Produkt. Trotz dieser Grundvoraussetzungen ist die tatsächliche
Umsetzung KI-gestützter Systeme in den klinischen Alltag mit erheblichen
Herausforderungen verbunden. Die dies hemmenden bzw. begünstigenden Faktoren
sollen anhand folgender Fragen identifiziert werden:
"""

QUESTIONS = [
    {
        "id": "q1", "type": "textarea",
        "label": "Q1: Werden in Ihrem Arbeitsumfeld bereits **KI-gestützte Systeme** angewendet? Wenn ja, was waren die **entscheidenden Faktoren** auf IT-Ebene für die tatsächliche Anwendung eines Systems?",
    },
    {
        "id": "q2", "type": "multiselect",
        "label": "Q2: Wer ist in Ihrem Arbeitsumfeld dafür **verantwortlich**, wenn ein von Ärzten verwendetes (KI-)**System** bei der Therapie eines Patienten **versagt**?",
        "options": ["Ärzteschaft", "IT-Abteilung", "Krankenhausleitung", "Hersteller des Systems", "Zertifizierungsstellen", "Krankenkasse", "Sonstige"],
        "other_option": "Sonstige",
    },
    {
        "id": "q3", "type": "radio", "horizontal": True,
        "label": "Q3: Sind die **lokalen Daten** in Ihrem Arbeitsumfeld gut genug, um ein KI-System zu betreiben?",
        "options": ["Gar nicht", "Eher nicht", "Weder noch", "Eher schon", "Sehr"],
    },
    {
        "id": "q4", "type": "radio",
        "label": "Q4: Wo liegen Ihrer Erfahrung nach die **größten Herausforderungen** bei der **Einführung** und von wem gehen sie aus?",
        "options": ["Ärzteschaft", "Pflegepersonal", "IT-Abteilung", "Patienten", "Krankenhaus-Organisation", "Sonstige"],
        "other_option": "Sonstige",
    },
]
