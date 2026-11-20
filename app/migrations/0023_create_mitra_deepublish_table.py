from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0022_kategoriartikel_state"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[],
            database_operations=[],
        ),
    ]
