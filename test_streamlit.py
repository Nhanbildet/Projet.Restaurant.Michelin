import streamlit as st
import pandas as pd 
import requests
import ast
import folium
from streamlit_folium import st_folium
import google.generativeai as genai

#####
df = pd.read_csv('data1902.csv', sep=',').dropna()

#fonction display title restarant:
def Mapsfolium(df):
    mean_longitude = df['Coordinates'].dropna().apply(lambda x: eval(x)[0]).mean()
    mean_latitude = df['Coordinates'].dropna().apply(lambda x: eval(x)[1]).mean()
    maps = folium.Map(location=[mean_latitude, mean_longitude], zoom_start=12)
    for i  in range(0,len(df)):
            latitude = eval(df['Coordinates'].iloc[i])[1]  # Latitude
            longitude = eval(df['Coordinates'].iloc[i])[0]  # Longitude
    # Ajouter un marqueur avec popup
            popup_text = f"""
            <b>{df['Nom'].iloc[i]}</b><br>
            ⭐ {df['etoile'].iloc[i]}<br>
            🍽️ {df['Façon Cuisine'].iloc[i]}<br>
                {df['Adress'].iloc[i]}<br>
            <img src="{df['image'].iloc[i]}" width="150">
            """
            folium.Marker(
                location=(latitude, longitude),
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=df['Nom'].iloc[i],  # Info qui s'affiche au survol
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(maps)

            # Afficher la carte dans Streamlit
    st_folium(maps, width=700, height=500)

def displaytitle(df):
    Nom = df['Nom'].strip()
    #derse = df['Derssert']
    add = df['Adress']
    cuisineManier = df['Façon Cuisine']
    try:
        image = df['image']
        st.image(image, caption=cuisineManier, width=200)
    except Exception as e:
        st.warning(f"Image non disponible pour {Nom}")
    st.write(f'{Nom}')
    st.write(f'{add}')
         
######
def afficher_etoiles(df, etoile):
    df_etoil = df[df['etoile'] == etoile]
    n = len(df_etoil) // 3 + 1 
    for row in range(n):
        cols = st.columns(3)
        for col_index in range(3):
            rest_index = row * 3 + col_index
            if rest_index < len(df_etoil):
                with cols[col_index]:
                    displaytitle(df_etoil.iloc[rest_index, :])
                    #detail = st.checkbox("Detail")

######
#Fonction pour afficher toutes les informations concrètes d'un restaurant 
def display(df):
    image = df.iloc[0,:]['image']
    Nom = df.iloc[0,:]['Nom'].strip()
    Add = df.iloc[0,:]['Adress'] 
    cuisineManier = df.iloc[0,:]['Façon Cuisine']
    marque =df.iloc[0,:]['étoils cusine']
    web = df.iloc[0,:]['Website']
    tel = df.iloc[0,:]['Telephone']
    des = df.iloc[0,:]['Description']
    etoils = df_selected.sample(1).iloc[0,:]['etoile']
    st.markdown("<hr style='border: 0.3px solid white;'>", unsafe_allow_html=True)
    st.subheader(f'Restaurant {Nom}')
    st.write(f'🌟:',etoils)
    col1, col2= st.columns(2)
    with col1: 
        st.write(f'Façon de cuisine:',cuisineManier)
        st.write(f'Location:',Add)
    with col2:
        st.write(f'Telephone:',tel)
        st.page_link(web,label="link Website")
    col1, col2= st.columns(2)
    with col1:
        st.image(image, caption= marque)
    with col2:
        st.write(des)
    API_KEY = "AIzaSyBejG-xOzeM7CUOI23TVkwg1CjTiXu235E" 
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "input": Nom.strip(),
        "language": "fr",
        "components": "country:fr",
        "types": "establishment",
        "key": API_KEY}

    response = requests.get(url, params=params)
    data = response.json()
    if response.status_code == 200 and 'predictions' in data and len(data['predictions']) > 0:
        df_placeid = pd.json_normalize(data, record_path= 'predictions')
        filtered = df_placeid[df_placeid['structured_formatting.main_text'].str.contains(Nom.strip(), case=False, na=False)]
        if not filtered.empty:
            place_id = filtered.iloc[0]['place_id']       
            # Intégration de la carte dans l'application Streamlit
            st.title("Google Maps")
            map_url = f"https://www.google.com/maps/embed/v1/place?key={API_KEY}&q=place_id:{place_id}"
                
            st.components.v1.iframe(map_url, width=600, height=450)
            
            #  Récupérer les détails (dont les avis)
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                        "place_id": place_id,
                        "fields": "name,rating,user_ratings_total,price_level,reviews",
                        "key": API_KEY
                         }
            details_response = requests.get(details_url, params=details_params)
            details_data = details_response.json()
            if "reviews" in details_data.get("result", {}):
                rating = details_data["result"].get("rating", "Aucune note")
                user_ratings_total = details_data["result"].get("user_ratings_total", "Aucun avis")
                price_level = details_data["result"].get("price_level", "Inconnu")
                st.subheader(f"Avis sur Google Maps pour {details_data['result']['name']}")
                st.write(f"🌟 **Note moyenne** : {rating}/5")
                st.write(f"📝 **Nombre d'avis** : {user_ratings_total}")
                st.write(f"💸 **Niveau de prix** : {price_level}")
                for review in details_data["result"]["reviews"]:
                        st.write(f"🌟 Note : {review['rating']}/5")
                        st.write(f"🗨️ Avis : {review['text']}")
                        st.write(f"👤 Auteur : {review['author_name']}")
                        st.write("---")
            else:
                st.warning("Aucun avis trouvé pour ce lieu.")
        else:
            st.warning(f"Aucun Avis trouvé sur Google maps avec restaurant- '{Nom}'.")

# creer fonction avec chat box Gemini
def chatGemini(session_key ="default" ):

    genai.configure(api_key="AIzaSyDhdpdEjsX7f6AE325IIIEitDbWgsc363g")

    model = genai.GenerativeModel("gemini-pro")

    # Initialiser l'historique des messages pour cette session spécifique
    if session_key not in st.session_state:
        st.session_state[session_key] = {"messages": []}
    # Bouton de réinitialisation du chat
    if st.button("🔄 Réinitialiser ou Quitter",key=f"reset_{session_key}"):
        st.session_state[session_key]["messages"] = []
        st.rerun()  # Recharge la page

    # Affichage des messages
    for msg in st.session_state[session_key]["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Entrée utilisateur (⚠ appelée une seule fois !)
    prompt = st.chat_input("Posez vos questions à un expert des restaurants Michelin ...", key=f"chat_input_{session_key}")

    if prompt:
        # Ajouter le message utilisateur
        st.session_state[session_key]["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            # Générer la réponse avec Gemini
            response = model.generate_content(prompt)
            reply = response.text if response else "Je n'ai pas compris votre question."

        except Exception as e:
            reply = f"Erreur : {e}"  # Gestion d'erreur

        # Ajouter la réponse du chatbot
        st.session_state[session_key]["messages"].append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

####
st.title('Les restaurants Michelin en France')

list_ville = sorted(df['Ville'].unique())
ville = st.selectbox('Sélection de la ville:', list_ville, index= None)
df_selected = df

if ville:
    st.write(f'Vous cherchez des restaurants à {ville} ')
    df_selected  = df_selected.loc[df_selected['Ville'] == ville] 
    col1, col2 = st.columns(2)
    with col1: 
        st.dataframe(pd.DataFrame([df_selected['etoile'].value_counts().to_dict()]),hide_index= True)
    with col2:
        list_cuisine =sorted(df_selected['Façon Cuisine'].str.split(',').explode().unique())
        cuisine = st.selectbox('Choisissez le mode de cuisson:', list_cuisine, index= None)
        if cuisine:
            df_selected = df_selected.loc[df_selected['Façon Cuisine'].str.contains(cuisine)]      
     
    st.write(f'Vous cherchez un restaurant à {ville}')
    st.markdown("<hr style='border: 0.3px solid white;'>", unsafe_allow_html=True) 
    tab1, tab2, tab3, tab4, tab5= st.tabs( ["Trois étoiles'", "Deux étoiles", "Une étoile","Cuisine Gourmande", "Chat avec moi"])
    with tab1:  
        if not df_selected.loc[df_selected['etoile'] == "Trois étoiles"].empty:
            list_restau = sorted(df_selected.loc[df_selected['etoile'] == "Trois étoiles"]['Nom'])
            Nom1 = st.selectbox('Choisissez un restaurant pour consulter les avis et les détails:', list_restau, index= None, key= 'avis')
            Mapsfolium(df_selected.loc[df_selected['etoile'] == "Trois étoiles"])
            afficher_etoiles(df_selected, "Trois étoiles") 
            Nom2 = st.selectbox('Choisissez un restaurant pour consulter les avis et les détails:', list_restau, index= None, key= 'detail')
           
            if Nom1 or Nom2:       
                df_selected = df_selected.loc[(df_selected['Nom']== Nom1)|(df_selected['Nom']== Nom2)]
                display(df_selected)
                chatGemini(session_key="chat1")
        else:
            st.write("Désolé, aucun restaurant n’a été trouvé ici")
    with tab2:
        if not df_selected.loc[df_selected['etoile'] == "Deux étoiles"].empty:
            list_restau = sorted(df_selected.loc[df_selected['etoile'] == "Deux étoiles"]['Nom'])
            Nom1 = st.selectbox('Choisissez un restaurant pour consulter les avis et les détails:', list_restau, index= None, key= 'consulter')
            Mapsfolium(df_selected.loc[df_selected['etoile'] == "Deux étoiles"])
            Nom2 = st.selectbox('Choisissez un restaurant pour consulter les avis et les détails:', list_restau, index= None, key= 'nhan')
            afficher_etoiles(df_selected, "Deux étoiles") 
            if Nom1 or Nom2:       
                df_selected = df_selected.loc[(df_selected['Nom']== Nom1)|(df_selected['Nom']== Nom2)]
                display(df_selected)
                chatGemini(session_key="chat2")
        else:
            st.write("Désolé, aucun restaurant n’a été trouvé ici")
    with tab3:
        if not df_selected.loc[df_selected['etoile'] == "Une étoile"].empty:
            list_restau = sorted(df_selected.loc[df_selected['etoile'] == "Une étoile"]['Nom'])
            Nom1 = st.selectbox('Choisissez un restaurant pour consulter les avis et les détails:', list_restau, index= None, key= 'michelin')
            Mapsfolium(df_selected.loc[df_selected['etoile'] == "Une étoile"])
            afficher_etoiles(df_selected, "Une étoile")
            Nom2 = st.selectbox('Choisissez un restaurant pour consulter les avis et les détails:', list_restau, index= None, key= 'restaurant')
            if Nom1 or Nom2:       
                df_selected = df_selected.loc[(df_selected['Nom']== Nom1)|(df_selected['Nom']== Nom2)]
                chatGemini(session_key="chat3")
        else:
            st.write("Désolé, aucun restaurant n’a été trouvé ici")
    with tab4:
        if not df_selected.loc[df_selected['etoile'] == "Gourmande"].empty: 
            list_restau = sorted(df_selected.loc[df_selected['etoile'] == "Gourmande"]['Nom'])
            Nom1 = st.selectbox('Choisissez un restaurant pour consulter les avis et les détails:', list_restau, index= None,key='group1')
            Mapsfolium(df_selected.loc[df_selected['etoile'] == "Gourmande"])
            afficher_etoiles(df_selected, "Gourmande")
            Nom1 = st.selectbox('Choisissez un restaurant pour consulter les avis et les détails:', list_restau, index= None,key='group42')
            if Nom1 or Nom2:       
                df_selected = df_selected.loc[(df_selected['Nom']== Nom1)|(df_selected['Nom']== Nom2)]
        else:
            st.write("Désolé, aucun restaurant n’a été trouvé ici")
            chatGemini(session_key="chat4")
    with tab5:
        st.image('chatavecmoi.png')
        chatGemini(session_key="chat5")
else:
        st.write('👉 "Sélectionnez votre ville pour obtenir la liste des restaurants disponibles')
        
        #st.markdown("<hr style='border: 0.3px solid white;'>", unsafe_allow_html=True)

import streamlit as st
import google.generativeai as genai

def chatGemini(session_key="default"):
    """Chatbot Gemini fonctionnant avec une session unique."""
    
    # Configurer l'API Gemini
    genai.configure(api_key="TA_CLE_API")  # Remplace par ta clé API

    model = genai.GenerativeModel("gemini-pro")

    # Initialiser l'historique des messages pour cette session spécifique
    if session_key not in st.session_state:
        st.session_state[session_key] = {"messages": []}
    # Bouton de réinitialisation du chat
    if st.button("🔄 Réinitialiser le chat"):
        st.session_state[session_key]["messages"] = []
        st.rerun()  # Recharge la page

    # Affichage des messages
    for msg in st.session_state[session_key]["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Entrée utilisateur (⚠ appelée une seule fois !)
    prompt = st.chat_input("Posez vos questions à un expert des restaurants Michelin ...")

    if prompt:
        # Ajouter le message utilisateur
        st.session_state[session_key]["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            # Générer la réponse avec Gemini
            response = model.generate_content(prompt)
            reply = response.text if response else "Je n'ai pas compris votre question."

        except Exception as e:
            reply = f"Erreur : {e}"  # Gestion d'erreur

        # Ajouter la réponse du chatbot
        st.session_state[session_key]["messages"].append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

    # Bouton pour quitter l'application
    st.markdown("""
        <script>
        function closeWindow() {
            window.close();
        }
        </script>
        <button onclick="closeWindow()">❌ Quitter</button>
    """, unsafe_allow_html=True)

 

