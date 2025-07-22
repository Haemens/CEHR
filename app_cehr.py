# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, render_template
from calculator_cehr import calculate_cehr

app = Flask(__name__)

@app.route('/')
def index():
    """Affiche la page principale du simulateur."""
    return render_template('index_cehr.html')

@app.route('/simulate_cehr', methods=['POST'])
def simulate():
    """Point d'entrée pour le calcul de la simulation."""
    data = request.get_json()

    # Validation simple des champs attendus
    expected_fields = [
        'situation_familiale', 'revenus_net', 'charges_deductibles', 
        'revenus_exoneres', 'abattements', 'plus_values_liberatoires',
        'rfr_n1', 'rfr_n2'
    ]
    if not all(field in data for field in expected_fields):
        missing_fields = [field for field in expected_fields if field not in data]
        return jsonify({'status': 'error', 'message': f'Données manquantes: {", ".join(missing_fields)}'}), 400

    results = calculate_cehr(data)
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5002)
