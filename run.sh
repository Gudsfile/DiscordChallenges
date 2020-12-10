#!/bin/bash

BASEDIR=$(dirname $0)
source $BASEDIR/secret.properties

echo "Lancement de l'environnement virtuel"
source $BASEDIR/venv/bin/activate

echo "Installation des bibliothèques python"
pip install -r requirements.txt

echo "Mise à jour des varibles d'environnements"
export DISCORD_TOKEN=$discord_token

echo "Lancement du bot Discord"
python $BASEDIR/app.py
