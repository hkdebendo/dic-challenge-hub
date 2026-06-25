from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ctf.models import Event, HackathonResource


class Command(BaseCommand):
    help = "Create Nova Systems Smart Incident Estimator hackathon event data."

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
            slug="nova-systems-smart-incident-estimator",
            defaults={
                "title": "Nova Systems - Smart Incident Estimator",
                "kind": "hackathon",
                "description": (
                    "Nova Systems veut un service web intelligent qui estime le nombre d'incidents confirmes "
                    "à partir du nombre d'activités suspectes détectées. Les équipes devront comprendre un "
                    "petit dataset, construire une régression linéaire simple, produire des prédictions, "
                    "rediger le pseudo-code et imaginer l'integration web et réseau de la solution."
                ),
                "is_active": True,
                "max_team_size": 5,
                "duration_minutes": 160,
                "bonus_flag": "",
                "bonus_points": 0,
                "bonus_max_attempts": 0,
            },
        )

        HackathonResource.objects.filter(event=event).exclude(order=1).delete()
        HackathonResource.objects.update_or_create(
            event=event,
            order=1,
            defaults={
                "title": "Dataset Smart Incident Estimator",
                "file_path": "Nova-Smart-Incident-Estimator/smart_incident_train.csv",
                "description": (
                    "Petit dataset de 15 observations pour construire une régression linéaire entre "
                    "les activités suspectes détectées et les incidents confirmes."
                ),
            },
        )

        self.stdout.write(self.style.SUCCESS("Smart Incident Estimator seeded. Admin: admin@dic.local / admin12345"))



