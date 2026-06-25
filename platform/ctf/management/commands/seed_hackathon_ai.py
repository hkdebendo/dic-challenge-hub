from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ctf.models import Event, HackathonResource


class Command(BaseCommand):
    help = "Create Nova Systems Intrusion Detection hackathon event data."

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

        new_slug = "nova-systems-intrusion-detection"
        old_slug = "-".join(["ai", "day", "intrusion", "detection"])
        old_event = Event.objects.filter(slug=old_slug).first()
        if old_event and not Event.objects.filter(slug=new_slug).exists():
            old_event.slug = new_slug
            old_event.save(update_fields=["slug"])

        event, _ = Event.objects.update_or_create(
            slug=new_slug,
            defaults={
                "title": "Nova Systems - Intrusion Detection",
                "kind": "hackathon",
                "description": (
                    "Nova Systems a besoin de votre équipe pour renforcer son centre de surveillance. "
                    "Analysez les journaux de sécurité, identifiez les comportements suspects et construisez "
                    "un modèle capable de détecter les activités potentiellement malveillantes. Vous disposez "
                    "de deux heures pour transformer des données brutes en un outil d'aide à la détection."
                ),
                "is_active": True,
                "max_team_size": 5,
                "duration_minutes": 120,
                "bonus_flag": "",
                "bonus_points": 0,
                "bonus_max_attempts": 0,
            },
        )

        resources = [
            (
                1,
                "Dataset d'entraînement",
                "Nova-Intrusion-Detection/nova_security_train.csv",
                "Données d'entraînement avec la cible is_malicious.",
            ),
            (
                2,
                "Dataset de test",
                "Nova-Intrusion-Detection/nova_security_test.csv",
                "Données de test sans la cible. Les équipes produisent leurs prédictions.",
            ),
            (
                3,
                "Exemple de soumission",
                "Nova-Intrusion-Detection/sample_submission.csv",
                "Format attendu pour submission.csv.",
            ),
        ]

        for order, title, file_path, description in resources:
            HackathonResource.objects.update_or_create(
                event=event,
                order=order,
                defaults={"title": title, "file_path": file_path, "description": description},
            )

        self.stdout.write(self.style.SUCCESS("Hackathon seeded. Admin: admin@dic.local / admin12345"))



