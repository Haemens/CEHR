# -*- coding: utf-8 -*-

# Barèmes CEHR pour 2025 (inchangés depuis plusieurs années)
BAREME_CEHR_CELIBATAIRE = {
    250000: 0.0,
    500000: 0.03,
    float('inf'): 0.04
}

BAREME_CEHR_COUPLE = {
    500000: 0.0,
    1000000: 0.03,
    float('inf'): 0.04
}

def _calculate_progressive_tax(base, bareme):
    """Calcule un impôt progressif simple par tranches à partir d'une base et d'un barème."""
    tax = 0
    lower_bound = 0
    # Le barème est un dictionnaire {seuil: taux}, on le trie par seuil.
    sorted_bareme = sorted(bareme.items())
    
    for upper_bound, rate in sorted_bareme:
        if base > lower_bound:
            # On calcule le montant du revenu imposable dans la tranche actuelle
            tranche_amount = min(base, upper_bound) - lower_bound
            tax += tranche_amount * rate
        # La borne supérieure de cette tranche devient la borne inférieure de la suivante
        lower_bound = upper_bound
        # Si la base imposable est entièrement traitée, on arrête.
        if base <= upper_bound:
            break
            
    return tax

def calculate_cehr(data):
    """
    Calcule la Contribution Exceptionnelle sur les Hauts Revenus (CEHR).
    Prend en compte le calcul de base et le mécanisme de lissage.
    """
    try:
        # --- 1. Récupération et validation des données ---
        situation_familiale = data.get('situation_familiale', 'celibataire')
        revenus_net = float(data.get('revenus_net', 0))
        charges_deductibles = float(data.get('charges_deductibles', 0))
        revenus_exoneres = float(data.get('revenus_exoneres', 0))
        abattements = float(data.get('abattements', 0))
        plus_values_liberatoires = float(data.get('plus_values_liberatoires', 0))

        # Calcul du RFR N à partir des composantes
        rfr_n = (revenus_net - charges_deductibles + revenus_exoneres + 
                 abattements + plus_values_liberatoires)
        rfr_n1 = float(data.get('rfr_n1', 0))
        rfr_n2 = float(data.get('rfr_n2', 0))

        # --- 2. Détermination du barème et des seuils applicables ---
        if situation_familiale == 'marie':
            bareme = BAREME_CEHR_COUPLE
            seuil_declenchement = 500000
        else:
            bareme = BAREME_CEHR_CELIBATAIRE
            seuil_declenchement = 250000

        # --- 3. Calcul de la CEHR de base ---
        cehr_base = _calculate_progressive_tax(rfr_n, bareme)

        # --- 4. Vérification des conditions du lissage ---
        rfr_moyen_n1_n2 = (rfr_n1 + rfr_n2) / 2
        lissage_applicable = False
        if rfr_moyen_n1_n2 > 0: # Évite la division par zéro et les cas absurdes
            lissage_applicable = (
                rfr_n > (rfr_moyen_n1_n2 * 1.5) and
                rfr_n1 < seuil_declenchement and rfr_n2 < seuil_declenchement
            )

        # --- 5. Calcul de la CEHR lissée (si applicable) ---
        cehr_lissee = None
        base_lissee = None
        if lissage_applicable:
            revenu_ordinaire = rfr_moyen_n1_n2
            revenu_exceptionnel = rfr_n - revenu_ordinaire
            base_lissee = revenu_ordinaire + (revenu_exceptionnel / 2)
            cehr_lissee = _calculate_progressive_tax(base_lissee, bareme)

        # --- 6. Détermination du résultat final ---
        cehr_finale = cehr_base
        economie = 0
        comparaison_lissee = None

        if lissage_applicable and cehr_lissee is not None:
            # La règle est de comparer la CEHR de base avec le DOUBLE de la cotisation sur base lissée.
            comparaison_lissee = cehr_lissee * 2
            
            # Le montant final est le MINIMUM des deux.
            cehr_finale = min(cehr_base, comparaison_lissee)
            economie = cehr_base - cehr_finale

        return {
            'status': 'success',
            'rfr_n': rfr_n,
            'cehr_base': round(cehr_base, 2),
            'lissage_applicable': lissage_applicable,
            'base_lissee': round(base_lissee, 2) if base_lissee is not None else None,
            'cehr_lissee_intermediaire': round(cehr_lissee, 2) if cehr_lissee is not None else None,
            'cehr_lissee_comparaison': round(comparaison_lissee, 2) if comparaison_lissee is not None else None,
            'cehr_finale': round(cehr_finale, 2),
            'economie_fiscale': round(economie, 2)
        }

    except (ValueError, TypeError) as e:
        return {'status': 'error', 'message': f'Erreur de données : {e}'}
