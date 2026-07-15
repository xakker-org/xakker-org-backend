from django.core.management.base import BaseCommand

from chatbot.models import ChatbotKnowledge

ENTRIES = [
    {
        "title": "Xakker.org nədir?",
        "category": "Platforma haqqında",
        "content": (
            "Xakker.org kibertəhlükəsizlik öyrənmək üçün Azərbaycan dilində praktiki "
            "təlim platformasıdır. İstifadəçilər kurslar, missiyalar və real lablar "
            "(rooms/tasks) vasitəsilə pentesting, veb təhlükəsizlik, şəbəkə və digər "
            "kibertəhlükəsizlik sahələrini əməli şəkildə öyrənirlər."
        ),
    },
    {
        "title": "Kurslar, Missiyalar və Lablar necə işləyir?",
        "category": "Platforma haqqında",
        "content": (
            "Kurslar video/mətn dərslər və sual-cavablardan ibarətdir. Missiyalar "
            "ardıcıl 'pass'lardan (mərhələlərdən) və yekun imtahandan ibarətdir, "
            "tamamlandıqda XP qazandırır. Lablar (rooms) real mühitlərdə (Docker/VM) "
            "tapşırıqları (tasks) həll etməyi tələb edir — flag, mətn və ya çoxseçimli "
            "cavablarla yoxlanılır, ipucu (hint) almaq mümkündür."
        ),
    },
    {
        "title": "Xakker.org-un üstünlükləri",
        "category": "Platforma haqqında",
        "content": (
            "Ana dildə (Azərbaycan dilində) məzmun, praktiki tapşırıqlar, XP və "
            "rütbə sistemi ilə motivasiya, real lab mühitləri, addım-addım izahlar "
            "və müxtəlif səviyyələr üçün (başlanğıc/orta/yüksək) tapşırıqlar."
        ),
    },
    {
        "title": "Niyə kibertəhlükəsizlik öyrənməliyəm?",
        "category": "Kibertəhlükəsizlik",
        "content": (
            "Kibertəhlükəsizlik bu gün demək olar ki, bütün rəqəmsal sistemlərin "
            "təhlükəsizliyi üçün kritik əhəmiyyət daşıyır. Bu sahədə bacarıqlar "
            "sistem inzibatçılığından tutmuş pentesting, DevSecOps və təhlükəsizlik "
            "analitikasına qədər geniş karyera imkanları açır."
        ),
    },
    {
        "title": "Yeni başlayanlar üçün tövsiyə",
        "category": "Kibertəhlükəsizlik",
        "content": (
            "Yeni başlayanlara şəbəkə əsasları (TCP/IP, HTTP), Linux komanda "
            "sətri və əsas veb texnologiyaları ilə tanış olmaq, sonra Xakker.org-dakı "
            "'beginner' səviyyəli lab və kurslardan başlamaq tövsiyə olunur."
        ),
    },
]


class Command(BaseCommand):
    help = "Seed a small starter set of ChatbotKnowledge entries for the AI Köməkçi."

    def handle(self, *args, **options):
        created, updated = 0, 0
        for entry in ENTRIES:
            obj, was_created = ChatbotKnowledge.objects.update_or_create(
                title=entry["title"],
                defaults={
                    "category": entry["category"],
                    "content": entry["content"],
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded chatbot knowledge: {created} created, {updated} updated."))
