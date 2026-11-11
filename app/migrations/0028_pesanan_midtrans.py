from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0027_footersocial_nomor_telepon_alter_footersocial_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="pesanan",
            name="midtrans_transaction_id",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="pesanan",
            name="midtrans_payment_type",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="pesanan",
            name="midtrans_fraud_status",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
        migrations.AddField(
            model_name="pesanan",
            name="stok_dikurangi",
            field=models.BooleanField(default=False),
        ),
    ]
