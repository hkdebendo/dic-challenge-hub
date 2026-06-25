from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ctf", "0004_event_kind_hackathonresource_hackathonsubmission"),
    ]

    operations = [
        migrations.AlterField(
            model_name="hackathonsubmission",
            name="prediction_file",
            field=models.FileField(blank=True, upload_to="hackathon_deliverables/submissions/"),
        ),
        migrations.AlterField(
            model_name="hackathonsubmission",
            name="presentation",
            field=models.FileField(blank=True, upload_to="hackathon_deliverables/presentations/"),
        ),
    ]
