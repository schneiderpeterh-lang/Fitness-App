import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import google.generativeai as genai

# --- DATENBANK SETUP ---
def init_db():
    conn = sqlite3.connect('volleyball_fitness.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            exercise TEXT,
            weight REAL,
            reps INTEGER,
            rpe INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def save_set(exercise, weight, reps, rpe):
    conn = sqlite3.connect('volleyball_fitness.db')
    c = conn.cursor()
    c.execute('INSERT INTO workouts (date, exercise, weight, reps, rpe) VALUES (?, ?, ?, ?, ?)',
              (date.today().strftime("%Y-%m-%d"), exercise, weight, reps, rpe))
    conn.commit()
    conn.close()

def get_exercise_history(exercise):
    conn = sqlite3.connect('volleyball_fitness.db')
    df = pd.read_sql_query(f"SELECT date as Datum, weight as 'Gewicht (kg)', reps as Wdh, rpe as RPE FROM workouts WHERE exercise='{exercise}' ORDER BY id DESC LIMIT 3", conn)
    conn.close()
    return df

def get_recent_workouts():
    conn = sqlite3.connect('volleyball_fitness.db')
    df = pd.read_sql_query("SELECT date, exercise, weight, reps, rpe FROM workouts ORDER BY id DESC LIMIT 15", conn)
    conn.close()
    return df

init_db()

# --- APP UI ---
st.set_page_config(page_title="Volleyball Fitness", layout="centered")

# ==========================================
# SEITENLEISTE (API & TEST)
# ==========================================
st.sidebar.title("⚙️ Einstellungen")
api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Hole dir einen kostenlosen API Key im Google AI Studio.")

if st.sidebar.button("API-Verbindung testen"):
    if not api_key:
        st.sidebar.error("Bitte gib zuerst einen API-Key ein.")
    else:
        with st.spinner("Teste Verbindung..."):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-3.8-flash')
                response = model.generate_content("Antworte mit einem extrem kurzen, motivierenden Satz für einen Volleyballer, um zu bestätigen, dass die API geht.")
                st.sidebar.success("✅ Erfolgreich verbunden!")
                st.sidebar.info(f"Gemini sagt: {response.text}")
            except Exception as e:
                st.sidebar.error("❌ Fehler bei der Verbindung. Stimmt der API-Key?")
                st.sidebar.write(e)

st.title("🏐 Athletik Tracker")

tab1, tab2 = st.tabs(["🏋️ Training & Analyse", "🥗 Ernährung & Einkauf"])

# ==========================================
# TAB 1: TRAINING
# ==========================================
with tab1:
    st.header("Workout Tracking")

    workouts = {
        "Tag 1 (Unterkörper/Druck)": ["Hip Thrusts", "Brustpresse (Maschine)", "Beinbeuger (Maschine)", "Seitheben", "Planks"],
        "Tag 2 (Rücken/Hüfte)": ["Romanian Deadlifts (mit Zughilfen)", "Kabelrudern (mit Zughilfen)", "Glute Bridge", "Pallof Press", "Wadenheben"]
    }

    workout_day = st.selectbox("Welches Workout steht heute an?", list(workouts.keys()))
    exercise = st.selectbox("Übung", workouts[workout_day])

    st.subheader(f"Letzte Sätze: {exercise}")
    history_df = get_exercise_history(exercise)
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("Noch keine Daten vorhanden.")

    st.subheader("Neuen Satz eintragen")
    col_w, col_r, col_rpe = st.columns(3)
    with col_w:
        gewicht = st.number_input("Gewicht (kg)", min_value=0.0, step=1.0)
    with col_r:
        reps = st.number_input("Wdh.", min_value=0, step=1)
    with col_rpe:
        rpe = st.selectbox("Anstrengung (RPE)", list(range(1, 11)), index=7) 

    if st.button("Satz speichern"):
        save_set(exercise, gewicht, reps, rpe)
        st.success(f"Gespeichert: {exercise} | {gewicht} kg | {reps} Wdh. | RPE: {rpe}")
        st.rerun()

    st.divider()
    
    st.header("🧠 KI-Trainingsanalyse")
    if st.button("Training analysieren"):
        if not api_key:
            st.error("Bitte trage links in der Seitenleiste deinen Gemini API Key ein.")
        else:
            recent_data = get_recent_workouts()
            if recent_data.empty:
                st.warning("Trage zuerst ein paar Sätze ein, bevor du die Analyse startest.")
            else:
                with st.spinner("Gemini analysiert deine heutigen Sätze..."):
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-3.8-flash')
                        
                        prompt = f"""
                        Du bist der persönliche Fitnesstrainer eines Volleyballspielers. 
                        Der Spieler hat einen Knorpelschaden Grad 4 im Knie und einen Tennisellbogen. 
                        Hier sind seine letzten protokollierten Trainingssätze (Gewicht in kg, Wiederholungen, RPE von 1-10):
                        
                        {recent_data.to_string(index=False)}
                        
                        Analysiere das Training kurz und prägnant. Antworte in 3 kurzen Stichpunkten:
                        1. **Progression:** Kurze Einschätzung der Leistung.
                        2. **Empfehlung:** Konkrete Handlungsempfehlung für das nächste Training basierend auf der RPE (z.B. Gewicht hoch/runter).
                        3. **Verletzungs-Check:** Eine kurze Erinnerung an die schonende Ausführung für Knie oder Ellbogen bei den trainierten Übungen.
                        
                        Verwende keine langen Einleitungen, starte direkt mit den Punkten.
                        """
                        
                        response = model.generate_content(prompt)
                        st.write(response.text)
                    except Exception as e:
                        st.error("Es gab ein Problem bei der Analyse. Hast du den API-Key richtig eingegeben?")

# ==========================================
# TAB 2: ERNÄHRUNG & EINKAUF
# ==========================================
with tab2:
    st.header("Teller-Trick Check")
    st.write("Ernährung nach der 80/20-Regel: ½ Gemüse, ¼ Protein, ¼ Kohlenhydrate?[cite: 1]")
    
    col_f, col_m, col_a = st.columns(3)
    with col_f:
        fruehstueck_ok = st.checkbox("Frühstück", key="f_ok")
    with col_m:
        mittag_ok = st.checkbox("Mittagessen", key="m_ok")
    with col_a:
        abend_ok = st.checkbox("Abendessen", key="a_ok")
        
    if fruehstueck_ok and mittag_ok and abend_ok:
        st.success("Perfekt! Regeneration optimal unterstützt.")

    st.divider()

    st.header("Tagesplan & Einkaufsliste")
    
    # Mahlzeiten-Datenbank
    meal_database = {
        "Frühstück": {
            "Haferflocken-Bowl": ["Haferflocken", "Milch/Pflanzendrink", "Proteinpulver", "Tiefkühlbeeren"],
            "Herzhaftes Brot": ["Vollkornbrot", "Eier", "Körniger Frischkäse"]
        },
        "Mittagessen": {
            "Kalter Wrap": ["Vollkorn-Wraps", "Putenbrust oder Räuchertofu", "Salat", "Gurke", "Hummus"],
            "Schneller Salat": ["Salatmix", "Thunfisch oder Kichererbsen", "Feta", "Olivenöl"],
            "Reste vom Abendessen": []
        },
        "Snack": {
            "Nüsse & Banane": ["Bananen", "Ungesalzene Nüsse (Mandeln/Walnüsse)"],
            "Naturjoghurt": ["Naturjoghurt (mager)"]
        },
        "Abendessen": {
            "Ofengemüse mit Protein": ["Kartoffeln", "Paprika", "Zucchini", "Hähnchenbrust oder Feta", "Olivenöl"],
            "Gesunde Bolognese": ["Vollkornnudeln", "Passierte Tomaten", "Rinderhack oder Rote Linsen", "Karotten", "Sellerie"],
            "Bowl-Style": ["Reis", "Tofu oder Lachs", "Edamame", "Brokkoli", "Sojasauce"]
        }
    } #[cite: 1]

    c1, c2 = st.columns(2)
    with c1:
        breakfast = st.selectbox("Frühstück", list(meal_database["Frühstück"].keys()))
        lunch = st.selectbox("Mittagessen", list(meal_database["Mittagessen"].keys()))
    with c2:
        snack = st.selectbox("Snack", list(meal_database["Snack"].keys()))
        dinner = st.selectbox("Abendessen", list(meal_database["Abendessen"].keys()))

    st.subheader("🛒 Einkaufsliste")
    selected_ingredients = []
    selected_ingredients.extend(meal_database["Frühstück"][breakfast]) #[cite: 1]
    selected_ingredients.extend(meal_database["Mittagessen"][lunch]) #[cite: 1]
    selected_ingredients.extend(meal_database["Snack"][snack]) #[cite: 1]
    selected_ingredients.extend(meal_database["Abendessen"][dinner]) #[cite: 1]

    if selected_ingredients:
        unique_ingredients = sorted(list(set(selected_ingredients))) #[cite: 1]
        for item in unique_ingredients:
            st.checkbox(item)
    else:
        st.info("Wähle Mahlzeiten aus, um die Liste zu füllen.")