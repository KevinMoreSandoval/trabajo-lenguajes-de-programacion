from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("canchas", "0002_canchabasket_canchafutbol_canchavalley_horario_and_more")]
    operations = [
        migrations.AddField(
            model_name="cancha",
            name="imagen",
            field=models.FileField(blank=True, null=True, upload_to="canchas/"),
        )
    ]
