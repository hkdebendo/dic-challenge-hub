from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ctf.models import Challenge, Event, Hint


class Command(BaseCommand):
    help = "Create Operation Nova demo data."

    def handle(self, *args, **options):
        admin, created = User.objects.get_or_create(
            username="admin@dic.local",
            defaults={
                "email": "admin@dic.local",
                "first_name": "Admin",
                "last_name": "DIC",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin12345")
            admin.save()

        event, _ = Event.objects.update_or_create(
            slug="operation-nova",
            defaults={
                "title": "Operation Nova",
                "description": "Challenge CTF du Digital Innovation Club : investigation, crypto, steganographie, logs et sécurité web.",
                "is_active": True,
                "max_team_size": 4,
                "duration_minutes": 120,
                "bonus_flag": "DIC{NOVA_47_PIXEL_TRACE_GATE}",
                "bonus_points": 100,
                "bonus_max_attempts": 1,
            },
        )

        data = [
            {
                "order": 1,
                "title": "Le document mal nomme",
                "category": "Investigation numerique",
                "difficulty": "Tres facile",
                "points": 100,
                "statement": (
                    "Un rapport a été récupéré sur l'ordinateur d'un employé de Nova Systems.\n\n"
                    "Le fichier fourni s'appelle rapport_final.pdf, mais il ne s'ouvre pas correctement comme un vrai PDF. "
                    "Le responsable informatique affirme pourtant qu'il contient une information importante.\n\n"
                    "Votre objectif : comprendre le vrai format du fichier, l'ouvrir avec l'outil adapte, puis retrouver le flag.\n\n"
                    "Format attendu : DIC{...}"
                ),
                "flag": "DIC{une_extension_ne_suffit_pas}",
                "fragment": "NOVA",
                "attachment_path": "C1/rapport_final.pdf",
                "unlock_after_solves": 0,
                "hints": [
                    "Le nom d'un fichier ne garantit pas son veritable format.",
                    "Essayez de l'ouvrir avec un editeur de texte ou un gestionnaire d'archives.",
                    "L'extension .pdf n'est pas la bonne.",
                ],
            },
            {
                "order": 2,
                "title": "La transmission inversee",
                "category": "Cryptographie legere",
                "difficulty": "Facile",
                "points": 200,
                "statement": (
                    "Une transmission a été interceptée. Le message semble encodé, mais il ne donne rien de comprehensible tel quel.\n\n"
                    "Une note accompagnait le message : \"Avant de decoder, remettez les choses dans le bon sens.\"\n\n"
                    "Votre objectif : analyser la chaine fournie dans transmission.txt, remettre les caracteres dans le bon ordre, "
                    "puis identifier l'encodage obtenu pour récupérér le flag.\n\n"
                    "Format attendu : DIC{...}"
                ),
                "flag": "DIC{deux_etapes_pour_decoder}",
                "fragment": "47",
                "attachment_path": "C2/transmission.txt",
                "unlock_after_solves": 0,
                "hints": [
                    "Les caracteres de fin semblent places au mauvais endroit.",
                    "Commencez par lire toute la chaine dans le sens oppose.",
                    "Une fois inversee, la chaine utilisé un encodage tres courant.",
                ],
            },
            {
                "order": 3,
                "title": "Le secret de l'image",
                "category": "Steganographie",
                "difficulty": "Moyenne",
                "points": 300,
                "statement": (
                    "Une capture du bureau d'un employé a été retrouvee.\n\n"
                    "L'image semble normale a l'oeil nu. Pourtant, son auteur affirme avoir laisse un message "
                    "\"derriere l'image, et non dans ce qu'elle montre\".\n\n"
                    "Votre objectif : ne pas vous limiter au contenu visible de l'image. Inspectez les informations du fichier, "
                    "cherchez une indication utile, puis verifiez si l'image contient autre chose que des pixels.\n\n"
                    "Format attendu : DIC{...}"
                ),
                "flag": "DIC{une_image_peut_contenir_plus}",
                "fragment": "PIXEL",
                "attachment_path": "C3/bureau_nova.png",
                "unlock_after_solves": 1,
                "hints": [
                    "Regardez les informations du fichier, pas uniquement l'image.",
                    "Les metadonnées contiennent une donnee utile.",
                    "L'image contient egalement une petite archive.",
                ],
            },
            {
                "order": 4,
                "title": "La connexion de trop",
                "category": "Analyse de logs",
                "difficulty": "Moyenne+",
                "points": 400,
                "statement": (
                    "Un fichier confidentiel a été téléchargé depuis le serveur de Nova Systems.\n\n"
                    "Les administrateurs savent qu'un utilisateur s'est connecte depuis une adresse inhabituelle, "
                    "mais l'adresse IP ne se trouve pas directement dans le fichier des téléchargements.\n\n"
                    "Votre objectif : analyser les deux journaux fournis dans l'archive, reconstruire la chronologie, "
                    "identifier la session suspecte, puis relier cette session au téléchargement correspondant.\n\n"
                    "Vous devez retrouver trois éléments : l'utilisateur compromis, l'adresse IP suspecte et le fichier téléchargé.\n\n"
                    "Format attendu : DIC{utilisateur_ip_fichier}\n"
                    "Exemple de structure uniquement : DIC{nom_192.168.1.10_document.pdf}"
                ),
                "flag": "DIC{admin_192.168.10.77_clients_nova.csv}",
                "fragment": "TRACE",
                "attachment_path": "C4/nova_logs.zip",
                "unlock_after_solves": 2,
                "hints": [
                    "Les deux fichiers ne contiennent pas les mêmes informations.",
                    "Une session permet de relier une connexion à une action.",
                    "Recherchez S-481 dans les deux fichiers.",
                ],
            },
            {
                "order": 5,
                "title": "Le portail oublie",
                "category": "Securite web",
                "difficulty": "Plus difficile",
                "points": 500,
                "statement": (
                    "Nova Systems utilisait autrefois un portail interne pour consulter des documents employés.\n\n"
                    "Le développeur affirme que les anciens fichiers ont été supprimés et que les pages sensibles sont protégées. "
                    "La page principale indique qu'aucun document public n'est disponible.\n\n"
                    "Votre objectif : explorer le portail local, chercher les chemins oublies, inspecter le code cote client "
                    "et comprendre comment les rapports sont charges par l'API. Le rapport public n'est pas le rapport confidentiel.\n\n"
                    "Adresse du portail : http://127.0.0.1:5005\n"
                    "Format attendu : DIC{...}"
                ),
                "flag": "DIC{un_identifiant_ne_remplace_pas_une_autorisation}",
                "fragment": "GATE",
                "attachment_path": "",
                "unlock_after_solves": 3,
                "hints": [
                    "Les moteurs de recherche recoivent parfois des instructions interessantes.",
                    "Consultez le fichier /robots.txt.",
                    "Le JavaScript revele comment les rapports sont charges.",
                    "Le serveur verifie l'identifiant du rapport, mais pas son proprietaire.",
                ],
            },
        ]

        for item in data:
            hints = item.pop("hints")
            challenge, _ = Challenge.objects.update_or_create(
                event=event,
                order=item["order"],
                defaults=item,
            )
            challenge.hints.all().delete()
            for index, text in enumerate(hints, start=1):
                Hint.objects.create(
                    challenge=challenge,
                    order=index,
                    text=text,
                    penalty_percent=index * 10,
                )

        self.stdout.write(self.style.SUCCESS("Operation Nova seeded. Admin: admin@dic.local / admin12345"))



