import streamlit as st
import pandas as pd
from datetime import date
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection

# --- APP UI SETUP ---
st.set_page_config(page_title="Volleyball Fitness", layout="centered")

# --- DATENBANK VERBINDUNG (GOOGLE SHEETS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_all_data():
    try:
        return conn.read(worksheet="Workouts", usecols=list(range(5)))
    except:
        return pd.DataFrame(columns=['date', 'exercise', 'weight', 'reps', 'rpe'])

def save_set(exercise, weight, reps, rpe):
    df = get_all_data()
    df = df.dropna(how='all') 
    
    new_row = pd.DataFrame([{
        'date': date.today().strftime("%Y-%m-%d"),
        'exercise': exercise,
        'weight': weight,
        'reps': reps,
        'rpe': rpe
    }])
    
    updated_df = pd.concat([df, new_row], ignore_index=True)
    conn.update(worksheet="Workouts", data=updated_df)
    st.cache_data.clear()

def get_exercise_history(exercise):
    df = get_all_data()
    df = df.dropna(how='all')
    if df.empty:
        return pd.DataFrame()
    history = df[df['exercise'] == exercise].tail(3)
    return history.rename(columns={'date': 'Datum', 'weight': 'Gewicht (kg)', 'reps': 'Wdh', 'rpe': 'RPE'})

def get_recent_workouts():
    df = get_all_data()
    df = df.dropna(how='all')
    return df.tail(15)

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
    
    # Detailinformationen zu den Übungen
    exercise_details = {
        "Hip Thrusts": {"sets": "3 Sätze x 8-10 Wdh.", "desc": "Schultern auf der Bank, Hüfte explosiv strecken. Das Kniegelenk bleibt unbelastet von Scherkräften, voller Fokus auf das Gesäß."},
        "Brustpresse (Maschine)": {"sets": "3 Sätze x 8-12 Wdh.", "desc": "Geführte Bewegung, Schulterblätter hinten fixieren. Schont den Ellbogen im Vergleich zum freien Drücken."},
        "Beinbeuger (Maschine)": {"sets": "3 Sätze x 10-12 Wdh.", "desc": "Bewegung isoliert aus dem Kniegelenk. Keine axiale Stauchung oder Druck auf den Knieknorpel."},
        "Seitheben": {"sets": "3 Sätze x 12-15 Wdh.", "desc": "Arme nur leicht angewinkelt heben. Vermeide zu starkes Greifen, um den Tennisellbogen nicht zu triggern."},
        "Planks": {"sets": "3 Sätze x Max. Zeit", "desc": "Unterarmstütz, Rumpf und Gesäß fest anspannen. Komplett statisch, keine Gelenkbelastung."},
        "Romanian Deadlifts (mit Zughilfen)": {"sets": "3 Sätze x 8-10 Wdh.", "desc": "Hüftdominante Bewegung (Gesäß nach hinten schieben), Knie nur minimal beugen. Zughilfen sind Pflicht für den Ellbogen!"},
        "Kabelrudern (mit Zughilfen)": {"sets": "3 Sätze x 10-12 Wdh.", "desc": "Breiter Griff, Schulterblätter aktiv zusammenziehen. Auch hier Zughilfen nutzen, um die Unterarme zu entlasten."},
        "Glute Bridge": {"sets": "3 Sätze x 10-12 Wdh.", "desc": "Aus der Rückenlage die Hüfte heben. Sehr knieschonende Alternative für die hintere Kette."},
        "Pallof Press": {"sets": "3 Sätze x 10-12 Wdh.", "desc": "Seitlich zum Kabelzug stehen, Griff vor die Brust drücken und den Rotationswiderstand durch den Rumpf ausgleichen."},
        "Wadenheben": {"sets": "3 Sätze x 12-15 Wdh.", "desc": "Bewegung rein aus dem Sprunggelenk, das Knie bleibt statisch in seiner Position."}
    }

    workout_day = st.selectbox("Welches Workout steht heute an?", list(workouts.keys()))
    exercise = st.selectbox("Übung", workouts[workout_day])
    
    # Ausführung und Vorgaben einblenden
    st.info(f"**🎯 Ziel:** {exercise_details[exercise]['sets']}\n\n**💡 Ablauf:** {exercise_details[exercise]['desc']}")

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
        recent_data = get_recent_workouts()
        if recent_data.empty:
            st.warning("Trage zuerst ein paar Sätze ein, bevor du die Analyse startest.")
        else:
            with st.spinner("Gemini analysiert deine heutigen Sätze..."):
                try:
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel('gemini-3.8-flash')
                    
                    prompt = f"""
                    Du bist der persönliche Fitnesstrainer eines Volleyballspielers. 
                    Der Spieler hat einen Knorpelschaden Grad 4 im Knie und einen Tennisellbogen. 
                    Hier sind seine letzten Trainingssätze:
                    
                    {recent_data.to_string(index=False)}
                    
                    Analysiere das Training kurz und prägnant. Antworte in 3 kurzen Stichpunkten:
                    1. **Progression:** Kurze Einschätzung der Leistung.
                    2. **Empfehlung:** Konkrete Handlungsempfehlung für das nächste Training basierend auf der RPE.
                    3. **Verletzungs-Check:** Kurze Erinnerung an die schonende Ausführung.
                    """
                    
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e:
                    st.error("Es gab ein Problem bei der Analyse.")
                    st.write(e)

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
            
    st.divider()
    
    # NEU: KI-Rezeptgenerator basierend auf vorhandenen Zutaten
    st.header("👨‍🍳 KI-Resteverwertung")
    st.write("Was hast du noch im Kühlschrank? Gemini erstellt dir ein passendes Rezept.")
    
    available_ingredients = st.text_input("Deine Zutaten (z.B. Paprika, 2 Eier, Reis, Pute)")
    
    if st.button("Rezept generieren"):
        if not available_ingredients:
            st.warning("Bitte gib zuerst ein paar Zutaten ein.")
        else:
            with st.spinner("Gemini kocht..."):
                try:
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel('gemini-3.8-flash')
                    
                    recipe_prompt = f"""
                    Ich habe folgende Zutaten zu Hause: {available_ingredients}.
                    Erstelle mir daraus ein kurzes, einfaches und leckeres Rezept.
                    Das Rezept sollte sich grob an den 'Teller-Trick' für Athleten halten (ca. 1/2 Gemüse, 1/4 Protein, 1/4 Kohlenhydrate). 
                    Ergänze maximal 2-3 absolute Basis-Zutaten (wie Öl, Salz, Pfeffer), falls nötig.
                    Strukturiere die Antwort mit:
                    1. **Titel des Gerichts**
                    2. **Benötigte Zutaten**
                    3. **Kurze Zubereitung (max. 3 Schritte)**
                    """
                    
                    recipe_response = model.generate_content(recipe_prompt)
                    st.success("Hier ist dein Rezeptvorschlag:")
                    st.write(recipe_response.text)
                except Exception as e:
                    st.error("Es gab ein Problem bei der Rezeptgenerierung.")
                    st.write(e)
