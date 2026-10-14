from django.core.management.base import BaseCommand
from api.models import Advisor


class Command(BaseCommand):
    help = "Create the initial Alfred advisor without replacing an existing prompt."

    def handle(self, *args, **options):
        _, created = Advisor.objects.get_or_create(
            slug="alfred",
            defaults={
                "name": "Alfred",
                "system_prompt": (
                    "Sen Aifred, Juliet Rooms & Kitchen için bir dijital otel danışmanısın. "
                    "Bu bir önizleme ortamıdır. Güncel otel bilgileri henüz doğrulanıp "
                    "yüklenmedi. Fiyat, müsaitlik, kahvaltı saati, oda özellikleri veya "
                    "otel politikaları hakkında bilgi uydurma. Bu konularda resepsiyondan "
                    "teyit iste. Rezervasyon veya sipariş oluşturduğunu iddia etme. "
                    "Genel seyahat sorularına kullanıcının dilinde kısa ve yardımcı yanıt ver."
                ),
            },
        )
        self.stdout.write("Preview advisor created." if created else "Existing advisor preserved.")
