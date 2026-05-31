import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# CONFIGURATION & INTERFACE STYLE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ImmoBot - Analyseur d'Investissement Immobilier",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏢 ImmoBot Pro : Simulateur & Assistant Fiscal")
st.write("Analysez vos annonces, estimez les prix du marché en temps réel et déterminez le meilleur statut juridique.")

# -----------------------------------------------------------------------------
# FONCTIONS DE CONNEXION INTERNET (MARKET DATA DATA)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_market_data(ville, surface):
    """
    Simule la récupération sur internet des prix moyens au m² et loyers.
    Dans une version de production avancée, vous pouvez y connecter l'API DVF de l'État.
    """
    ville_clean = ville.strip().capitalize()
    
    # Base de données de marché par défaut (Métropoles françaises)
    market_database = {
        "Paris": {"prix_m2": 10200, "loyer_m2": 32.5},
        "Lyon": {"prix_m2": 4900, "loyer_m2": 17.0},
        "Marseille": {"prix_m2": 3600, "loyer_m2": 14.2},
        "Bordeaux": {"prix_m2": 4500, "loyer_m2": 16.5},
        "Lille": {"prix_m2": 3400, "loyer_m2": 13.8},
        "Nantes": {"prix_m2": 3800, "loyer_m2": 14.5},
        "Toulouse": {"prix_m2": 3700, "loyer_m2": 14.0},
        "Nice": {"prix_m2": 5100, "loyer_m2": 18.5}
    }
    
    if ville_clean in market_database:
        data = market_database[ville_clean]
    else:
        # Valeurs moyennes nationales hors grandes métropoles
        data = {"prix_m2": 2600, "loyer_m2": 11.5}
        
    prix_m2_moyen = data["prix_m2"]
    loyer_m2_moyen = data["loyer_m2"]
    
    prix_marche_estime = prix_m2_moyen * surface
    loyer_marche_estime = loyer_m2_moyen * surface
    
    return prix_m2_moyen, loyer_m2_moyen, prix_marche_estime, loyer_marche_estime

# -----------------------------------------------------------------------------
# SIDEBAR : SAISIE DES DONNÉES DE L'ANNONCE
# -----------------------------------------------------------------------------
st.sidebar.header("📍 L'Annonce Immobilière")
url_annonce = st.sidebar.text_input("🔗 URL de l'annonce (Optionnel)", placeholder="https://www.leboncoin.fr/...")
ville = st.sidebar.text_input("🏙️ Ville du bien", "Lyon")
surface = st.sidebar.number_input("📐 Surface habitable (m²)", min_value=9, max_value=500, value=45)
prix_affiche = st.sidebar.number_input("💰 Prix affiché (€ FAI)", min_value=1000, value=180000)

st.sidebar.write("---")
st.sidebar.header("🛠️ Financement & Travaux")
travaux = st.sidebar.number_input("🚧 Budget Travaux (€)", min_value=0, value=15000, step=1000)
apport = st.sidebar.number_input("💵 Votre Apport Personnel (€)", min_value=0, value=20000, step=5000)
taux_interet = st.sidebar.number_input("📈 Taux d'intérêt du crédit (%)", min_value=0.1, max_value=10.0, value=3.8, step=0.1)
duree_credit = st.sidebar.slider("⏱️ Durée de l'emprunt (Années)", min_value=10, max_value=25, value=20)

st.sidebar.write("---")
st.sidebar.header("👤 Profil Fiscal")
tmi = st.sidebar.selectbox(
    "Tranche Marginale d'Imposition (TMI)", 
    options=[0.0, 0.11, 0.30, 0.41, 0.45],
    format_func=lambda x: f"{x*100:.0f}%",
    index=2
)

# -----------------------------------------------------------------------------
# CALCULS FINANCIERS DE BASE
# -----------------------------------------------------------------------------
prix_m2_moyen, loyer_m2_moyen, prix_marche_estime, loyer_marche_estime = fetch_market_data(ville, surface)

frais_notaire = int(prix_affiche * 0.08)
cout_total_projet = prix_affiche + frais_notaire + travaux
montant_emprunt = max(0, cout_total_projet - apport)

# Calcul mensualité crédit
if montant_emprunt > 0:
    rate_mensuel = (taux_interet / 100) / 12
    nb_mensualites = duree_credit * 12
    mensualite_credit = montant_emprunt * (rate_mensuel / (1 - (1 + rate_mensuel)**(-nb_mensualites)))
else:
    mensualite_credit = 0.0

charges_copro_annuelles = surface * 24
taxe_fonciere_annuelle = surface * 15
pno_et_divers = 250

# -----------------------------------------------------------------------------
# RENDU DU DASHBOARD
# -----------------------------------------------------------------------------
col_m1, col_m2, col_m3 = st.columns(3)

with col_m1:
    st.metric(
        label="Prix m² Annonce vs Marché",
        value=f"{int(prix_affiche/surface):,} €/m²",
        delta=f"{int(prix_affiche/surface) - prix_m2_moyen} €/m² vs moyenne",
        delta_color="inverse"
    )
with col_m2:
    st.metric(label="Loyer Marché Estimé (Mensuel)", value=f"{int(loyer_marche_estime):,} €")
with col_m3:
    st.metric(label="Coût Total du Projet Acté", value=f"{cout_total_projet:,} €")

st.write("---")
loyer_reel = st.number_input("💡 Loyer mensuel retenu pour l'analyse (€)", min_value=100, value=int(loyer_marche_estime))

# -----------------------------------------------------------------------------
# MOTEUR FISCAL COMPARATIF
# -----------------------------------------------------------------------------
revenus_bruts_annuels = loyer_reel * 12
rendement_brut = (revenus_bruts_annuels / prix_affiche) * 100

st.subheader("📊 Simulation Comparative des Régimes Fiscaux & Financiers")

statuts_data = []

# 1. Résidence Principale
cash_flow_rp = -(mensualite_credit * 12 + charges_copro_annuelles + taxe_fonciere_annuelle + pno_et_divers)
statuts_data.append({
    "Régime / Statut": "🏠 Résidence Principale",
    "Rendement Net (%)": "N/A",
    "Impôt Annuel (€)": 0,
    "Cash-Flow Mensuel (€)": round(cash_flow_rp / 12, 2),
    "Note stratégique": "Exonération totale de plus-value à la revente. Pas d'impôt foncier sur les loyers (usage propre)."
})

# 2. LMNP Réel
amortissement_estime = (prix_affiche * 0.8 * 0.033) + (travaux * 0.1)
charges_deductibles = charges_copro_annuelles + taxe_fonciere_annuelle + pno_et_divers + (montant_emprunt * taux_interet / 100 * 0.7)
base_imposable_lmnp = max(0, revenus_bruts_annuels - charges_deductibles - amortissement_estime)
impot_lmnp = base_imposable_lmnp * (tmi + 0.172)
cash_flow_lmnp = revenus_bruts_annuels - (mensualite_credit * 12 + charges_copro_annuelles + taxe_fonciere_annuelle + pno_et_divers) - impot_lmnp
rendement_net_lmnp = ((revenus_bruts_annuels - charges_deductibles - impot_lmnp) / cout_total_projet) * 100

statuts_data.append({
    "Régime / Statut": "🛋️ LMNP (Régime Réel)",
    "Rendement Net (%)": f"{rendement_net_lmnp:.2f} %",
    "Impôt Annuel (€)": int(impot_lmnp),
    "Cash-Flow Mensuel (€)": round(cash_flow_lmnp / 12, 2),
    "Note stratégique": "Excellent à court/moyen terme. L'amortissement efface l'impôt."
})

# 3. Location Nue
base_imposable_nue = max(0, revenus_bruts_annuels - charges_deductibles)
impot_nue = base_imposable_nue * (tmi + 0.172)
cash_flow_nue = revenus_bruts_annuels - (mensualite_credit * 12 + charges_copro_annuelles + taxe_fonciere_annuelle + pno_et_divers) - impot_nue
rendement_net_nue = ((revenus_bruts_annuels - charges_deductibles - impot_nue) / cout_total_projet) * 100

statuts_data.append({
    "Régime / Statut": "🪵 Location Nue (Impôt Foncier)",
    "Rendement Net (%)": f"{rendement_net_nue:.2f} %",
    "Impôt Annuel (€)": int(impot_nue),
    "Cash-Flow Mensuel (€)": round(cash_flow_nue / 12, 2),
    "Note stratégique": "Lourdement taxé si TMI > 11%. Intéressant uniquement en cas de fort déficit foncier."
})

# 4. SCI à l'IS
base_imposable_is = max(0, revenus_bruts_annuels - charges_deductibles - amortissement_estime)
impot_is = base_imposable_is * 0.15 if base_imposable_is <= 42500 else (42500 * 0.15) + ((base_imposable_is - 42500) * 0.25)
cash_flow_is = revenus_bruts_annuels - (mensualite_credit * 12 + charges_copro_annuelles + taxe_fonciere_annuelle + pno_et_divers) - impot_is
rendement_net_is = ((revenus_bruts_annuels - charges_deductibles - impot_is) / cout_total_projet) * 100

statuts_data.append({
    "Régime / Statut": "🏢 SCI à l'IS",
    "Rendement Net (%)": f"{rendement_net_is:.2f} %",
    "Impôt Annuel (€)": int(impot_is),
    "Cash-Flow Mensuel (€)": round(cash_flow_is / 12, 2),
    "Note stratégique": "Idéal pour capitaliser et réinvestir. Plus-value pro applicable en cas de revente."
})

# 5. SCI à l'IR
statuts_data.append({
    "Régime / Statut": "👪 SCI à l'IR",
    "Rendement Net (%)": f"{rendement_net_nue:.2f} %",
    "Impôt Annuel (€)": int(impot_nue),
    "Cash-Flow Mensuel (€)": round(cash_flow_nue / 12, 2),
    "Note stratégique": "Transparence fiscale. Même règles que le Nu standard, utile pour la transmission."
})

df_comparatif = pd.DataFrame(statuts_data)
st.dataframe(df_comparatif, use_container_width=True)

# -----------------------------------------------------------------------------
# VERDICT DU BOT
# -----------------------------------------------------------------------------
st.write("---")
st.subheader("🎯 Verdict de l'Analyseur ImmoBot")

options_locatives = [x for x in statuts_data if "Résidence Principale" not in x["Régime / Statut"]]
meilleure_option = max(options_locatives, key=lambda x: x["Cash-Flow Mensuel (€)"])

st.success(f"🏆 **Le meilleur statut locatif d'un point de vue Trésorerie / Cash-Flow immédiat est : {meilleure_option['Régime / Statut']}**")
st.write(f"Il génère un Cash-Flow net de **{meilleure_option['Cash-Flow Mensuel (€)']} € / mois** après impôts et crédit.")

if rendement_brut >= 8.0:
    st.balloons()
    st.info(f"🚀 **Diagnostic global : C'est une excellente affaire !** Le rendement de {rendement_brut:.2f}% est très solide.")
elif rendement_brut >= 5.0:
    st.info(f"⚖️ **Diagnostic global : Une affaire patrimoniale correcte.** Rendement de {rendement_brut:.2f}%. Idéal pour sécuriser du capital.")
else:
    st.warning(f"⚠️ **Diagnostic global : Rendement faible ({rendement_brut:.2f}%).** Risque d'effort d'épargne mensuel trop important.")
