from django.core.management.base import BaseCommand

from ctf.models import CtfMissionStatusChoices, Mission, MissionCategory, MissionTag, Writeup

CATEGORIES = [
    {"name": "Veb", "slug": "web"},
    {"name": "Kriptoqrafiya", "slug": "crypto"},
    {"name": "Şəbəkə", "slug": "network"},
    {"name": "Tərs Mühəndislik", "slug": "reverse"},
]

TAGS = [
    {"name": "SQLi", "slug": "sqli"},
    {"name": "XSS", "slug": "xss"},
    {"name": "Base64", "slug": "base64"},
    {"name": "Nmap", "slug": "nmap"},
    {"name": "Binary", "slug": "binary"},
]

MISSIONS = [
    {
        "title": "SQL İnyeksiyası ilə Giriş",
        "slug": "sql-injection-giris",
        "difficulty": "easy",
        "category": "web",
        "tags": ["sqli"],
        "short_description": "Zəif login formasında SQL inyeksiyası tapıb admin panelinə giriş əldə edin.",
        "description": (
            "Hədəf sayt sadə istifadəçi adı/şifrə forması istifadə edir. Backend sorğuları "
            "düzgün təmizlənmir. Login formasında SQL inyeksiyası tətbiq edərək autentifikasiyanı "
            "keçin və admin panelindəki flag-i tapın."
        ),
        "connection_info": "Hədəf: http://target.xakker.local:8081/login — VPN tələb olunmur (demo mühit).",
        "points": 100,
        "estimated_time": 20,
        "flag": "xkr{sql1_1nj3ct10n_bypa55}",
        "writeup": (
            "## Həll\n\n"
            "Login formasının `username` sahəsinə `' OR '1'='1' -- ` daxil edərək "
            "autentifikasiya yoxlamasını keçmək mümkündür. Admin panelinə daxil olduqdan "
            "sonra flag `/admin/dashboard` səhifəsində görünür."
        ),
        "is_locked_by_default": True,
    },
    {
        "title": "Base64 Şifrələnmiş Mesaj",
        "slug": "base64-sifrelenmis-mesaj",
        "difficulty": "easy",
        "category": "crypto",
        "tags": ["base64"],
        "short_description": "Tutulan trafikdə tapılan şifrələnmiş mesajı deşifrə edin.",
        "description": (
            "Şəbəkə trafikinin analizi zamanı Base64 formatında kodlanmış bir mesaj tapılıb. "
            "Mesajı deşifrə edərək daxilindəki flag-i tapın."
        ),
        "connection_info": "Fayl: capture.pcap (tapşırıq faylları admin panelindən əlavə olunacaq).",
        "points": 50,
        "estimated_time": 10,
        "flag": "xkr{b4s3_64_1s_n0t_3ncrypt10n}",
        "writeup": (
            "## Həll\n\n"
            "`echo '<base64-string>' | base64 -d` əmri ilə mesaj asanlıqla deşifrə olunur. "
            "Base64 şifrələmə deyil, sadəcə kodlaşdırmadır."
        ),
        "is_locked_by_default": False,
    },
    {
        "title": "Nmap ilə Port Skan",
        "slug": "nmap-ile-port-skan",
        "difficulty": "medium",
        "category": "network",
        "tags": ["nmap"],
        "short_description": "Hədəf serverdə açıq portları tapıb səhv konfiqurasiya olunmuş servisi istismar edin.",
        "description": (
            "Hədəf serverdə bir neçə port açıqdır, onlardan biri köhnə versiyalı və zəif "
            "konfiqurasiya olunmuş FTP servisidir. Anonim girişlə serverə daxil olub flag "
            "faylını tapın."
        ),
        "connection_info": "Hədəf: target-network.xakker.local (VPN konfiqurasiyası admin panelindən yüklənəcək).",
        "points": 150,
        "estimated_time": 35,
        "flag": "xkr{4n0nym0us_ftp_1s_d4ng3r0us}",
        "writeup": (
            "## Həll\n\n"
            "`nmap -sV -p- target-network.xakker.local` ilə port 21-də FTP aşkarlanır. "
            "`ftp target-network.xakker.local` ilə anonim istifadəçi adı (`anonymous`) və "
            "boş şifrə ilə giriş mümkündür. `flag.txt` faylı kök qovluqdadır."
        ),
        "is_locked_by_default": True,
    },
    {
        "title": "Sadə Tərs Mühəndislik",
        "slug": "sade-ters-muhendislik",
        "difficulty": "hard",
        "category": "reverse",
        "tags": ["binary"],
        "short_description": "Verilmiş binar faylı analiz edərək düzgün flag-i tapın.",
        "description": (
            "Verilmiş ELF binar faylı istifadəçidən flag daxil etməsini tələb edir və "
            "düzgün/yanlış olduğunu yoxlayır. Binarı analiz edərək (statik və ya dinamik) "
            "düzgün flag-i çıxarın."
        ),
        "connection_info": "Fayl: check_flag.elf (tapşırıq faylları admin panelindən əlavə olunacaq).",
        "points": 250,
        "estimated_time": 60,
        "flag": "xkr{r3v3rs3_3ng1n33r1ng_m4st3r}",
        "writeup": (
            "## Həll\n\n"
            "`strings check_flag.elf` ilə sadə müqayisə görünmür, çünki flag XOR ilə "
            "kodlanıb. `objdump -d` ilə müqayisə funksiyasını tapıb XOR açarını çıxarmaq "
            "və flag-i bərpa etmək mümkündür."
        ),
        "is_locked_by_default": True,
    },
]


class Command(BaseCommand):
    help = "Seed a few published demo CTF missions (AZ content), idempotent."

    def handle(self, *args, **options):
        cat_map = {}
        for cat in CATEGORIES:
            obj, _ = MissionCategory.objects.get_or_create(slug=cat["slug"], defaults={"name": cat["name"]})
            cat_map[cat["slug"]] = obj

        tag_map = {}
        for tag in TAGS:
            obj, _ = MissionTag.objects.get_or_create(slug=tag["slug"], defaults={"name": tag["name"]})
            tag_map[tag["slug"]] = obj

        created, updated = 0, 0
        for data in MISSIONS:
            mission, was_created = Mission.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "title": data["title"],
                    "difficulty": data["difficulty"],
                    "category": cat_map[data["category"]],
                    "short_description": data["short_description"],
                    "description": data["description"],
                    "connection_info": data["connection_info"],
                    "points": data["points"],
                    "estimated_time": data["estimated_time"],
                    "status": CtfMissionStatusChoices.PUBLISHED,
                },
            )
            if was_created:
                mission.set_flag(data["flag"])
                mission.save(update_fields=["flag_hash"])
                mission.tags.set([tag_map[slug] for slug in data["tags"]])
                created += 1
            else:
                updated += 1

            Writeup.objects.get_or_create(
                mission=mission,
                defaults={
                    "content": data["writeup"],
                    "is_locked_by_default": data["is_locked_by_default"],
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded CTF missions: {created} created, {updated} already existed."
        ))
