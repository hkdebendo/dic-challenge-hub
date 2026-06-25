# DIC CTF - Operation Nova

Plateforme locale de creation et de gestion CTF pour le Digital Innovation Club.

## Installation rapide

```powershell
pip install -r requirements.txt
python platform/manage.py makemigrations
python platform/manage.py migrate
python platform/manage.py seed_nova
python platform/manage.py runserver 127.0.0.1:8000
```

Dans un second terminal, lancer le challenge web :

```powershell
python C5/app.py
```

## Acces

Plateforme :

```text
http://127.0.0.1:8000
```

Challenge 5 :

```text
http://127.0.0.1:5005
```

Compte organisateur cree par defaut :

```text
admin@dic.local
admin12345
```

Les utilisateurs normaux peuvent creer leur compte depuis la page d'accueil.

## Notes organisateur

- L'evenement est visible tant qu'il est actif, mais les fichiers, indices et soumissions restent bloques tant qu'il n'est pas demarre.
- Depuis la vue organisateur, l'admin peut demarrer ou relancer l'evenement avec une duree en minutes.
- L'admin voit tous les inscrits, peut supprimer un inscrit, creer/supprimer une team, ajouter/retirer des membres et choisir un capitaine.
- Un compte admin ne peut pas participer, rejoindre une team, etre membre ou capitaine.
- Le mode test admin permet d'essayer les flags et les indices sans modifier le classement reel.
