#!/bin/bash

BASEDIR=$(dirname $0)
source $BASEDIR/secret.properties

echo "Lancement de l'environnement virtuel"
source $BASEDIR/venv/bin/activate

echo "Mise à jour de pip"
pip install --upgrade pip

echo "Installation des bibliothèques python"
pip install -r requirements.txt

echo "Installation de la librairie fr pour spacy"
spacy info fr_core_news_sm
if [ $? != 0 ]; then
  python -m spacy download fr_core_news_sm
else
  echo "Librairie déjà installée"
fi

echo "Mise à jour des varibles d'environnements"
export DISCORD_TOKEN=$bot_token

echo "Lancement du bot Discord"
python $BASEDIR/app.py
