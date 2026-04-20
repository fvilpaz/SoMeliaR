from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_configuracion_perfilusuario"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="foto_en_sidebar",
            field=models.BooleanField(default=True),
        ),
    ]
