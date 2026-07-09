"""Seed the platform with realistic demo content for both the student app
and the admin panel: categories, tags, courses (+lessons+self-study
questions), rooms (+tasks+task questions), missions (+passes+exams), and
learning plans.

This is a fresh, correctly-encoded replacement seed path — `seed_all.py`
and `seed_data.py` in this same directory contain mojibake (double-encoded
UTF-8) in their Azerbaijani string literals and should not be run against
a real database until repaired.

Run:
    python manage.py seed_xakker_demo             # idempotent (upserts by slug)
    python manage.py seed_xakker_demo --reset      # wipes seeded content first
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from courses.choices import sync_choices
from courses.models import (
    Category,
    Course,
    Enrollment,
    LearningPlan,
    LearningPlanCourse,
    Lesson,
    LessonQuestion,
    LessonQuestionChoice,
    Mission,
    MissionDifficultyChoices,
    MissionExam,
    MissionExamChoice,
    MissionExamQuestion,
    MissionExamQuestionTypeChoices,
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
    {"name": "Veb Təhlükəsizliyi", "slug": "web", "icon": "🕸️", "color": "#3b82f6",
     "description": "Veb tətbiqlərində zəifliklərin aşkarlanması və istismarı."},
    {"name": "Şəbəkə Təhlükəsizliyi", "slug": "network", "icon": "🌐", "color": "#14b8a6",
     "description": "TCP/IP, firewall, IDS/IPS və protokol analizi."},
    {"name": "Sistem Təhlükəsizliyi", "slug": "system", "icon": "🧰", "color": "#8b5cf6",
     "description": "Linux/Windows mühitində privilege escalation və post-exploitation."},
    {"name": "Kriptoqrafiya", "slug": "crypto", "icon": "🔐", "color": "#22c55e",
     "description": "Şifrələmə, hash funksiyaları, sertifikatlar və kriptoanaliz."},
    {"name": "OSINT və Kəşfiyyat", "slug": "osint", "icon": "🔎", "color": "#f59e0b",
     "description": "Açıq mənbə kəşfiyyatı və passiv recon texnikaları."},
    {"name": "Hücum Təhlükəsizliyi", "slug": "offensive", "icon": "⚔️", "color": "#ff3b3b",
     "description": "Red team, pentesting və adversary simulyasiyası."},
]

TAGS = [
    "linux", "windows", "recon", "enumeration", "exploit", "privesc",
    "burp", "sqli", "xss", "ssrf", "lfi", "csrf", "nmap", "wireshark",
    "osint", "forensics", "crypto", "cloud", "docker", "active-directory",
    "malware", "api", "mobile", "social-engineering",
]

# ─── Courses ─────────────────────────────────────────────────────

COURSES_DATA = [
    {
        "slug": "web-security-fundamentals", "title": "Veb Təhlükəsizliyinin Əsasları",
        "category": "web", "icon": "🕸️",
        "description": "HTTP, HTML, JavaScript və veb tətbiqlərdəki əsas zəifliklərin ümumi mənzərəsi.",
        "lessons": [
            {"title": "HTTP Protokolu", "order": 1,
             "content": "HTTP sorğu/cavab silsiləsi, metodlar (GET/POST/PUT/DELETE), status kodları və header-lar.",
             "questions": [{"text": "Uğurlu sorğunun standart status kodu?", "choices": [("200", True), ("404", False), ("500", False), ("301", False)]}]},
            {"title": "SQL Injection", "order": 2,
             "content": "SQL injection zəifliyi input sanitizasiyasının olmamasından istifadə edir.\n\n```sql\n' OR 1=1 --\n```",
             "questions": [{"text": "SQL-də şərh (comment) başlatmaq üçün hansı simvol istifadə olunur?", "choices": [("--", True), ("//", False), ("#!", False), ("**", False)]}]},
            {"title": "XSS — Cross-Site Scripting", "order": 3,
             "content": "Stored, Reflected və DOM-based XSS növləri. Cookie oğurlanması riski.", "questions": []},
        ],
        "questions": [
            {"title": "XSS növləri", "type": "closed", "level": "beginner", "points": 25,
             "prompt": "Aşağıdakılardan hansı XSS növü DEYİL?",
             "choices": [("Reflected XSS", False), ("Stored XSS", False), ("DOM-based XSS", False), ("SQL XSS", True)]},
            {"title": "OWASP Top 10", "type": "closed", "level": "intermediate", "points": 30,
             "prompt": "OWASP Top 10 (2021) siyahısında SQL Injection hansı kateqoriyaya aiddir?",
             "choices": [("A01: Broken Access Control", False), ("A03: Injection", True), ("A05: Security Misconfiguration", False), ("A07: Auth Failures", False)]},
            {"title": "SQL Injection izahı", "type": "open", "level": "beginner", "points": 30,
             "prompt": "SQL Injection zəifliyini qısaca izah edin və qarşısını almaq üçün 2 üsul yazın."},
            {"title": "Port skanlama", "type": "terminal", "level": "beginner", "points": 50,
             "prompt": "Hədəf serverdə açıq portları tapın və HTTP xidmətini aşkarlayın.", "starter_code": "nmap -sV 10.10.10.1"},
            {"title": "CSRF nədir?", "type": "open", "level": "intermediate", "points": 30,
             "prompt": "CSRF (Cross-Site Request Forgery) hücumunu izah edin və SameSite cookie necə qarşısını alır?"},
        ],
    },
    {
        "slug": "network-security-101", "title": "Şəbəkə Təhlükəsizliyi 101",
        "category": "network", "icon": "🌐",
        "description": "TCP/IP, subnetlər, routing, firewall və şəbəkə protokollarının təhlükəsizlik aspektləri.",
        "lessons": [
            {"title": "TCP/IP Modeli", "order": 1, "content": "7 qatlı OSI modeli və 4 qatlı TCP/IP modeli. Hər qatın təhlükəsizlik rolu.", "questions": []},
            {"title": "Port Nömrələri və Protokollar", "order": 2, "content": "Ən çox istifadə olunan portlar: 22 (SSH), 80 (HTTP), 443 (HTTPS), 3306 (MySQL).", "questions": []},
        ],
        "questions": [
            {"title": "HTTP portu", "type": "closed", "level": "beginner", "points": 20,
             "prompt": "HTTP xidməti standart olaraq hansı portda işləyir?",
             "choices": [("21", False), ("22", False), ("80", True), ("443", False)]},
            {"title": "SSH portu", "type": "closed", "level": "beginner", "points": 20,
             "prompt": "SSH protokolu standart olaraq hansı portu istifadə edir?",
             "choices": [("21", False), ("22", True), ("23", False), ("25", False)]},
            {"title": "Nmap ilə port skanlama", "type": "terminal", "level": "beginner", "points": 40,
             "prompt": "Hədəf hostda bütün açıq portları və servis versiyalarını tapın.", "starter_code": "nmap -sV 10.10.11.1"},
            {"title": "DNS portu", "type": "closed", "level": "beginner", "points": 20,
             "prompt": "DNS sorğuları standart olaraq hansı portdan istifadə edir?",
             "choices": [("53", True), ("67", False), ("110", False), ("143", False)]},
            {"title": "Firewall funksiyası", "type": "open", "level": "beginner", "points": 25,
             "prompt": "Firewall-un əsas funksiyası nədir və stateful ilə stateless firewall arasında fərq nədir?"},
        ],
    },
    {
        "slug": "linux-privilege-escalation", "title": "Linux Sistemlərində Hücum",
        "category": "system", "icon": "🧰",
        "description": "SUID, cron job, kernel exploit və sudo konfiqurasiya səhvləri ilə root əldə etmək.",
        "lessons": [
            {"title": "SUID Binary-lər", "order": 1, "content": "SUID bit nədir? `find / -perm -4000` ilə tapılan faylların istismarı.", "questions": []},
            {"title": "Sudo Konfiqurasiya Səhvləri", "order": 2, "content": "`sudo -l` ilə icazələri yoxlayın. GTFOBins-dən privesc vektorları tapın.", "questions": []},
        ],
        "questions": [
            {"title": "SUID tapma", "type": "terminal", "level": "intermediate", "points": 55,
             "prompt": "Sistemdə SUID bit ilə işləyən bütün binary-ləri tapın.", "starter_code": "find / -perm -4000 -type f 2>/dev/null"},
            {"title": "Privesc üsulları", "type": "open", "level": "advanced", "points": 50,
             "prompt": "Linux-da privilege escalation üçün ən azı 3 üsul sadalayın və qısaca izah edin."},
            {"title": "Cron job təhlükəsi", "type": "open", "level": "intermediate", "points": 40,
             "prompt": "Root tərəfindən icra olunan, lakin yazıla bilən cron script-i necə privilege escalation üçün istismar etmək olar?"},
            {"title": "GTFOBins", "type": "closed", "level": "intermediate", "points": 30,
             "prompt": "GTFOBins saytı nə üçün istifadə olunur?",
             "choices": [("Zərərli proqram yükləmək üçün", False), ("Sudo/SUID icazəli binary-lərdən privesc vektorları tapmaq üçün", True), ("Şəbəkə skan etmək üçün", False), ("Şifrələri krak etmək üçün", False)]},
            {"title": "Kernel exploit riski", "type": "open", "level": "advanced", "points": 45,
             "prompt": "Köhnəlmiş kernel versiyası privilege escalation üçün nə üçün risklidir?"},
        ],
    },
    {
        "slug": "cryptography-basics", "title": "Kriptoqrafiyaya Giriş",
        "category": "crypto", "icon": "🔐",
        "description": "AES, RSA, hash funksiyaları, sertifikatlar və kriptoanalizə giriş.",
        "lessons": [
            {"title": "Simmetrik Şifrələmə", "order": 1, "content": "AES, DES, 3DES. Block vs stream cipher. CBC, GCM rejimləri.", "questions": []},
            {"title": "Hash Funksiyaları", "order": 2, "content": "MD5, SHA1, SHA256, bcrypt. Rainbow table və salt. Parol hashing.", "questions": []},
        ],
        "questions": [
            {"title": "Asimmetrik alqoritm", "type": "closed", "level": "intermediate", "points": 35,
             "prompt": "Aşağıdakılardan hansı asimmetrik şifrələmə alqoritmidir?",
             "choices": [("AES", False), ("DES", False), ("RSA", True), ("Blowfish", False)]},
            {"title": "Hash növü", "type": "closed", "level": "beginner", "points": 25,
             "prompt": "Parol hashing üçün hansı alqoritm tövsiyə edilir?",
             "choices": [("MD5", False), ("SHA1", False), ("bcrypt", True), ("SHA256", False)]},
            {"title": "Salt nədir?", "type": "open", "level": "beginner", "points": 30,
             "prompt": "Kriptoqrafiya kontekstində 'salt' nədir? Rainbow table hücumunun qarşısını necə alır?"},
            {"title": "Simmetrik vs asimmetrik", "type": "open", "level": "beginner", "points": 30,
             "prompt": "Simmetrik və asimmetrik şifrələmə arasındakı əsas fərq nədir?"},
            {"title": "Base64 kodlaşdırma", "type": "closed", "level": "beginner", "points": 20,
             "prompt": "Base64 kriptoqrafik şifrələmədir, yoxsa sadəcə kodlaşdırma formatıdır?",
             "choices": [("Şifrələmədir, açar tələb edir", False), ("Sadəcə kodlaşdırma formatıdır, təhlükəsizlik təmin etmir", True), ("Hash funksiyasıdır", False), ("Yalnız şəkil faylları üçündür", False)]},
        ],
    },
    {
        "slug": "osint-techniques", "title": "OSINT Texnikaları",
        "category": "osint", "icon": "🔎",
        "description": "Açıq mənbə kəşfiyyatı: whois, DNS, crt.sh, Google dork-ları və Shodan.",
        "lessons": [
            {"title": "DNS və Whois", "order": 1, "content": "`whois`, `dig`, `nslookup` ilə domen məlumatlarının toplanması.", "questions": []},
            {"title": "Google Dork-ları", "order": 2, "content": "site:, filetype:, inurl:, intitle: ilə hədəf haqqında məlumat toplamaq.", "questions": []},
        ],
        "questions": [
            {"title": "Subdomen kəşfi", "type": "closed", "level": "intermediate", "points": 30,
             "prompt": "Certificate transparency loglarından subdomen tapmaq üçün hansı xidmət istifadə edilir?",
             "choices": [("Shodan", False), ("crt.sh", True), ("VirusTotal", False), ("Censys", False)]},
            {"title": "Google Dork nədir?", "type": "open", "level": "beginner", "points": 25,
             "prompt": "'site:example.az filetype:pdf' Google dork-u nə edir?"},
            {"title": "Shodan nədir?", "type": "open", "level": "beginner", "points": 25,
             "prompt": "Shodan axtarış sistemi nəyə görə fərqlənir və OSINT-də necə istifadə olunur?"},
            {"title": "Metadata sızması", "type": "open", "level": "intermediate", "points": 35,
             "prompt": "Şəkil və sənəd fayllarındakı metadata (EXIF və s.) necə OSINT üçün faydalı ola bilər?"},
            {"title": "WHOIS sorğusu", "type": "closed", "level": "beginner", "points": 20,
             "prompt": "WHOIS sorğusu ilə adətən hansı məlumatı əldə etmək olar?",
             "choices": [("Server-in RAM həcmini", False), ("Domenin qeydiyyat sahibini və qeydiyyat tarixini", True), ("Verilənlər bazasının strukturunu", False), ("İstifadəçi parollarını", False)]},
        ],
    },
    {
        "slug": "advanced-pentesting", "title": "İrəliləmiş Pentest",
        "category": "offensive", "icon": "⚔️",
        "description": "Veb və şəbəkə üzrə irəliləmiş pentest texnikaları: SSRF, XXE, deserialization.",
        "lessons": [
            {"title": "SSRF İstismarı", "order": 1, "content": "Server-Side Request Forgery — server vasitəsilə daxili resurslara müraciət.", "questions": []},
            {"title": "XXE Injection", "order": 2, "content": "XML External Entity injection ilə faylların oxunması və SSRF.", "questions": []},
        ],
        "questions": [
            {"title": "SSRF hədəfi", "type": "closed", "level": "advanced", "points": 45,
             "prompt": "SSRF hücumunun əsas hədəfi nədir?",
             "choices": [("Klient brauzerini hədəf almaq", False), ("Serveri daxili resurslara sorğu göndərməyə məcbur etmək", True), ("SQL Injection etmək", False), ("XSS payload yeritmək", False)]},
            {"title": "XXE izahı", "type": "open", "level": "advanced", "points": 50,
             "prompt": "XML External Entity (XXE) injection nədir və qarşısını necə almaq olar?"},
            {"title": "Insecure deserialization", "type": "open", "level": "advanced", "points": 45,
             "prompt": "Insecure deserialization zəifliyi nədir və hansı təhlükələr yaradır?"},
            {"title": "SSRF müdafiəsi", "type": "open", "level": "advanced", "points": 40,
             "prompt": "SSRF hücumlarının qarşısını almaq üçün hansı üsullardan istifadə edilə bilər?"},
            {"title": "Blind SSRF", "type": "closed", "level": "advanced", "points": 40,
             "prompt": "Blind SSRF-i adi SSRF-dən fərqləndirən əsas xüsusiyyət nədir?",
             "choices": [("Cavab server tərəfindən heç vaxt göstərilmir", True), ("Yalnız GET metodu ilə işləyir", False), ("Yalnız daxili şəbəkədə mövcuddur", False), ("Şifrələnmiş trafik tələb edir", False)]},
        ],
    },
    {
        "slug": "api-security", "title": "API Təhlükəsizliyi",
        "category": "web", "icon": "🔌",
        "description": "REST/GraphQL API-lərdə autentifikasiya, autorizasiya və rate-limit zəiflikləri.",
        "lessons": [
            {"title": "API Autentifikasiyası", "order": 1, "content": "API açarları, OAuth2, JWT token-ları və onların düzgün saxlanması.", "questions": []},
            {"title": "Broken Object Level Authorization", "order": 2, "content": "İstifadəçi ID-ni dəyişərək başqasının məlumatına giriş (BOLA/IDOR).", "questions": []},
        ],
        "questions": [
            {"title": "IDOR nədir?", "type": "open", "level": "intermediate", "points": 35,
             "prompt": "Insecure Direct Object Reference (IDOR) zəifliyini nümunə ilə izah edin."},
            {"title": "JWT strukturu", "type": "closed", "level": "intermediate", "points": 30,
             "prompt": "JWT token neçə hissədən ibarətdir?",
             "choices": [("1", False), ("2", False), ("3", True), ("4", False)]},
            {"title": "Rate limiting", "type": "open", "level": "intermediate", "points": 30,
             "prompt": "API-lərdə rate limiting olmaması hansı hücumlara şərait yaradır?"},
            {"title": "API açarı saxlanması", "type": "closed", "level": "beginner", "points": 25,
             "prompt": "API açarını harada saxlamaq TÖVSİYƏ OLUNMUR?",
             "choices": [("Server tərəfli environment variable-da", False), ("Klient tərəfli JavaScript kodunda açıq şəkildə", True), ("Secret manager xidmətində", False), ("CI/CD-nin şifrələnmiş secrets bölməsində", False)]},
            {"title": "Mass assignment", "type": "open", "level": "advanced", "points": 40,
             "prompt": "Mass assignment zəifliyi API-lərdə necə yaranır?"},
        ],
    },
    {
        "slug": "cloud-security-fundamentals", "title": "Bulud Təhlükəsizliyi Əsasları",
        "category": "system", "icon": "☁️",
        "description": "AWS/Azure/GCP-də səhv konfiqurasiyalar, IAM zəiflikləri və S3 bucket sızmaları.",
        "lessons": [
            {"title": "IAM Əsasları", "order": 1, "content": "İdentity and Access Management: rollar, siyasətlər və ən az imtiyaz prinsipi.", "questions": []},
        ],
        "questions": [
            {"title": "S3 bucket sızması", "type": "open", "level": "intermediate", "points": 35,
             "prompt": "Public S3 bucket-lərin yaratdığı riskləri izah edin."},
            {"title": "Least privilege", "type": "open", "level": "beginner", "points": 25,
             "prompt": "IAM-də 'ən az imtiyaz' (least privilege) prinsipi nə deməkdir?"},
            {"title": "Metadata servisi hücumu", "type": "open", "level": "advanced", "points": 45,
             "prompt": "Bulud instansının metadata servisinə (169.254.169.254) SSRF vasitəsilə giriş hansı təhlükə yaradır?"},
            {"title": "Şəxsi açar sızması", "type": "closed", "level": "intermediate", "points": 30,
             "prompt": "AWS access key/secret key-i GitHub-da açıq repo-ya push etsəniz, ən düzgün ilk addım nədir?",
             "choices": [("Heç nə etmək, kim görəcək", False), ("Açarı dərhal deaktiv edib yenisini yaratmaq", True), ("Yalnız commit-i silmək", False), ("Repo-nu private etmək kifayətdir", False)]},
            {"title": "Şəbəkə seqmentasiyası", "type": "open", "level": "intermediate", "points": 30,
             "prompt": "Bulud mühitində şəbəkə seqmentasiyası (VPC/subnet ayrımı) niyə vacibdir?"},
        ],
    },
    {
        "slug": "malware-analysis-basics", "title": "Zərərli Proqram Analizinə Giriş",
        "category": "system", "icon": "🦠",
        "description": "Statik və dinamik analiz üsulları ilə zərərli proqramların davranışının araşdırılması.",
        "lessons": [
            {"title": "Statik Analiz", "order": 1, "content": "Fayl strukturunun, string-lərin və imzaların icra etmədən araşdırılması.", "questions": []},
        ],
        "questions": [
            {"title": "Sandbox nədir?", "type": "open", "level": "beginner", "points": 25,
             "prompt": "Zərərli proqram analizində sandbox mühiti nə üçün istifadə olunur?"},
            {"title": "Statik vs dinamik analiz", "type": "open", "level": "beginner", "points": 30,
             "prompt": "Statik və dinamik malware analizi arasındakı fərq nədir?"},
            {"title": "Hash ilə identifikasiya", "type": "closed", "level": "beginner", "points": 25,
             "prompt": "Bir faylın məlum zərərli proqram olub-olmadığını yoxlamaq üçün ən çox hansı üsul istifadə olunur?",
             "choices": [("Fayl adına baxmaq", False), ("Fayl hash-ini (MD5/SHA256) VirusTotal-da axtarmaq", True), ("Fayl ölçüsünə baxmaq", False), ("Yalnız yaradılma tarixinə baxmaq", False)]},
            {"title": "Persistence mexanizmi", "type": "open", "level": "intermediate", "points": 35,
             "prompt": "Zərərli proqramların sistemdə 'persistence' (davamlılıq) qurmaq üçün istifadə etdiyi 2 üsul yazın."},
            {"title": "Packer nədir?", "type": "open", "level": "advanced", "points": 40,
             "prompt": "Malware müəllifləri niyə 'packer' (sıxıcı) istifadə edir və bu, analizi necə çətinləşdirir?"},
        ],
    },
    {
        "slug": "active-directory-attacks", "title": "Active Directory Hücumları",
        "category": "offensive", "icon": "🏰",
        "description": "Kerberoasting, pass-the-hash və AD mühitində lateral movement texnikaları.",
        "lessons": [
            {"title": "Kerberos Əsasları", "order": 1, "content": "TGT, TGS və Kerberoasting hücumunun məntiqi.", "questions": []},
        ],
        "questions": [
            {"title": "Pass-the-hash", "type": "open", "level": "advanced", "points": 45,
             "prompt": "Pass-the-hash hücumu necə işləyir?"},
            {"title": "Kerberoasting", "type": "open", "level": "advanced", "points": 45,
             "prompt": "Kerberoasting hücumu necə işləyir və hansı hesablar daha çox risk altındadır?"},
            {"title": "Golden Ticket", "type": "closed", "level": "advanced", "points": 40,
             "prompt": "Golden Ticket hücumu üçün hücumçuya nə lazımdır?",
             "choices": [("Yalnız istifadəçi parolu", False), ("krbtgt hesabının hash-i", True), ("Yalnız DNS girişi", False), ("Firewall log faylı", False)]},
            {"title": "Lateral movement", "type": "open", "level": "intermediate", "points": 35,
             "prompt": "AD mühitində 'lateral movement' nə deməkdir və bunu necə aşkarlamaq olar?"},
            {"title": "Domain Admin risk", "type": "open", "level": "intermediate", "points": 30,
             "prompt": "Nə üçün gündəlik iş üçün Domain Admin hesabından istifadə etmək təhlükəlidir?"},
        ],
    },
    {
        "slug": "mobile-app-security", "title": "Mobil Tətbiq Təhlükəsizliyi",
        "category": "system", "icon": "📱",
        "description": "Android/iOS tətbiqlərində insecure storage, reverse engineering və API zəiflikləri.",
        "lessons": [
            {"title": "APK Reverse Engineering", "order": 1, "content": "APK faylının açılması, dekompilyasiya və statik analiz.", "questions": []},
        ],
        "questions": [
            {"title": "Insecure Storage", "type": "open", "level": "intermediate", "points": 30,
             "prompt": "Mobil tətbiqlərdə 'insecure data storage' zəifliyinə nümunə verin."},
            {"title": "Root/Jailbreak aşkarlama", "type": "open", "level": "intermediate", "points": 30,
             "prompt": "Mobil tətbiqlər niyə cihazın root/jailbreak olub-olmadığını yoxlayır?"},
            {"title": "Sertifikat pinning", "type": "closed", "level": "advanced", "points": 40,
             "prompt": "Certificate pinning-in əsas məqsədi nədir?",
             "choices": [("Tətbiqi sürətləndirmək", False), ("MITM proxy (məs. Burp) ilə trafikin oxunmasının qarşısını almaq", True), ("Batareya istifadəsini azaltmaq", False), ("Fayl ölçüsünü kiçiltmək", False)]},
            {"title": "Hardcoded sirlər", "type": "open", "level": "intermediate", "points": 35,
             "prompt": "APK/IPA daxilində hardcoded API açarı və ya şifrə tapmaq üçün hansı üsullardan istifadə edilə bilər?"},
            {"title": "Deep link zəifliyi", "type": "open", "level": "advanced", "points": 40,
             "prompt": "Mobil tətbiqlərdə deep link/URL scheme zəiflikləri necə istismar oluna bilər?"},
        ],
    },
    {
        "slug": "social-engineering", "title": "Sosial Mühəndislik Taktikaları",
        "category": "offensive", "icon": "🎭",
        "description": "Phishing, pretexting və insan amilini hədəf alan hücum texnikaları.",
        "lessons": [
            {"title": "Phishing Növləri", "order": 1, "content": "Spear phishing, whaling və vishing arasındakı fərqlər.", "questions": []},
        ],
        "questions": [
            {"title": "Phishing əlaməti", "type": "open", "level": "beginner", "points": 20,
             "prompt": "Bir e-poçtun phishing olduğunu göstərən 3 əlamət sadalayın."},
            {"title": "Pretexting", "type": "open", "level": "beginner", "points": 25,
             "prompt": "Pretexting nədir və real həyatda necə tətbiq olunur?"},
            {"title": "Vishing", "type": "closed", "level": "beginner", "points": 20,
             "prompt": "Vishing termini nəyi ifadə edir?",
             "choices": [("Video vasitəsilə phishing", False), ("Telefon zəngi vasitəsilə phishing", True), ("SMS vasitəsilə phishing", False), ("E-poçt vasitəsilə phishing", False)]},
            {"title": "Tailgating", "type": "open", "level": "beginner", "points": 25,
             "prompt": "Fiziki təhlükəsizlikdə 'tailgating' sosial mühəndislik texnikası nədir?"},
            {"title": "Müdafiə strategiyası", "type": "open", "level": "intermediate", "points": 35,
             "prompt": "Təşkilatlar işçiləri sosial mühəndislik hücumlarından qorumaq üçün hansı tədbirləri görməlidir?"},
        ],
    },
]

# ─── Rooms (labs) ────────────────────────────────────────────────

ROOMS_DATA = [
    {"course_slug": "web-security-fundamentals", "title": "SQL Injection Laboratoriyası",
     "summary": "Zəif filtrlənmiş login formunda SQL injection texnikalarını tətbiq edin.",
     "level": "intermediate", "minutes": 60, "points": 300, "icon": "💉", "color": "#3b82f6", "env": "docker",
     "tags": ["sqli", "web", "burp"],
     "tasks": [{"title": "Login bypass", "content": "# SQL Injection ilə Login Bypass\n\nPayload: `admin' --`",
                "points": 40, "questions": [
                    {"prompt": "Login bypass üçün ən sadə payload nədir?", "kind": "text", "answer": "admin' --"},
                    {"prompt": "Verilənlər bazasının versiyasını çıxarmaq üçün istifadə edilən SQL funksiyası (MySQL)?", "kind": "text", "answer": "version()"},
                    {"prompt": "UNION-based SQLi-də sütun sayını təyin etmək üçün hansı açar söz istifadə olunur?", "kind": "text", "answer": "ORDER BY"},
                    {"prompt": "SQL injection-un qarşısını almaq üçün ən effektiv üsul hansıdır?", "kind": "choice", "points": 20,
                     "choices": [("Parametrized query (prepared statements)", True), ("Input-u yalnız frontend-də yoxlamaq", False), ("Xəta mesajlarını göstərmək", False), ("Cədvəl adlarını dəyişmək", False)]},
                ]}]},
    {"course_slug": "web-security-fundamentals", "title": "XSS Arena",
     "summary": "Reflected, Stored və DOM XSS vektorlarını praktik araşdırın.",
     "level": "intermediate", "minutes": 50, "points": 250, "icon": "⚡", "color": "#f59e0b", "env": "docker",
     "tags": ["xss", "web", "burp"],
     "tasks": [{"title": "Reflected XSS tapma", "content": "# Reflected XSS\n\n`<script>alert(document.cookie)</script>`",
                "points": 35, "questions": [
                    {"prompt": "Cookie oğurlamaq üçün XSS payload-ı nədən istifadə edir?", "kind": "text", "answer": "document.cookie"},
                    {"prompt": "XSS-in qarşısını almaq üçün istifadəçi girişini render edərkən nə etmək lazımdır?", "kind": "text", "answer": "output encoding"},
                    {"prompt": "Stored XSS payload-ı harada saxlanılır?", "kind": "choice", "points": 20,
                     "choices": [("Verilənlər bazasında", True), ("Yalnız brauzer keşində", False), ("DNS serverində", False), ("Yalnız URL-də", False)]},
                    {"prompt": "Content-Security-Policy header-i hansı hücuma qarşı qoruma verir?", "kind": "text", "answer": "XSS"},
                ]}]},
    {"course_slug": "network-security-101", "title": "Şəbəkə Kəşfiyyatı Labı",
     "summary": "Korporativ şəbəkədə host discovery və servis enumerasiyası.",
     "level": "intermediate", "minutes": 90, "points": 400, "icon": "📡", "color": "#14b8a6", "env": "docker",
     "tags": ["network", "nmap", "enumeration"],
     "tasks": [{"title": "Şəbəkə kəşfi", "content": "# Şəbəkə Xəritələməsi\n\n```bash\nnmap -sn 10.10.10.0/24\n```",
                "points": 50, "questions": [
                    {"prompt": "Subnet üzrə host discovery üçün nmap bayrağı?", "kind": "text", "answer": "-sn"},
                    {"prompt": "Nmap-da servis versiyasını aşkarlamaq üçün bayraq?", "kind": "text", "answer": "-sV"},
                    {"prompt": "Nmap-da default skript skanlaması üçün bayraq?", "kind": "text", "answer": "-sC"},
                    {"prompt": "TCP SYN skanı hansı bayraqla işə salınır?", "kind": "text", "answer": "-sS"},
                ]}]},
    {"course_slug": "linux-privilege-escalation", "title": "Linux Privesc Labı",
     "summary": "SUID, sudo və cron job üzərindən privilege escalation.",
     "level": "advanced", "minutes": 80, "points": 500, "icon": "🧰", "color": "#8b5cf6", "env": "linux",
     "tags": ["privesc", "linux", "exploit"],
     "tasks": [{"title": "SUID istismarı", "content": "# SUID Binary İstismarı\n\n```bash\nfind / -perm -u=s -type f 2>/dev/null\n```",
                "points": 60, "questions": [
                    {"prompt": "SUID bit olan `find` binary-si ilə shell almaq üçün komanda?", "kind": "text", "answer": "find . -exec /bin/bash -p \\;"},
                    {"prompt": "Cari istifadəçinin sudo icazələrini göstərən komanda?", "kind": "text", "answer": "sudo -l"},
                    {"prompt": "GTFOBins-ə görə SUID `vim` binary-si ilə root shell almaq üçün istifadə olunan yol?", "kind": "text", "answer": "vim -c ':!/bin/sh'"},
                    {"prompt": "root tərəfindən icra olunan cron job-ları görmək üçün adətən yoxlanılan fayl?", "kind": "text", "answer": "/etc/crontab"},
                ]}]},
    {"course_slug": "linux-privilege-escalation", "title": "Windows Privesc Labı",
     "summary": "Token manipulation və xidmət hijacking ilə privilege escalation.",
     "level": "advanced", "minutes": 100, "points": 600, "icon": "🪟", "color": "#6b7280", "env": "windows",
     "tags": ["privesc", "windows", "active-directory"],
     "tasks": [{"title": "Token manipulation", "content": "# Windows Token Manipulation\n\n`whoami /priv` ilə mövcud tokenləri yoxlayın.",
                "points": 70, "questions": [
                    {"prompt": "SeImpersonatePrivilege token-ini istismar edən exploit ailəsi hansıdır?", "kind": "choice", "points": 20,
                     "choices": [("Potato exploits", True), ("Buffer overflow", False), ("Kernel panic", False), ("SUID bypass", False)]},
                    {"prompt": "Cari istifadəçinin token imtiyazlarını göstərən komanda?", "kind": "text", "answer": "whoami /priv"},
                    {"prompt": "Windows-da lokal admin hesabları göstərən komanda?", "kind": "text", "answer": "net localgroup administrators"},
                    {"prompt": "winPEAS aləti nə üçün istifadə olunur?", "kind": "choice", "points": 20,
                     "choices": [("Windows privesc vektorlarını avtomatik axtarmaq", True), ("Şəbəkə trafikini şifrələmək", False), ("Fayl sıxma", False), ("Backup yaratmaq", False)]},
                ]}]},
    {"course_slug": "cryptography-basics", "title": "Kriptoqrafiya Seyfi",
     "summary": "Şifrələmə bypass, hash kracking və açar çıxarma.",
     "level": "advanced", "minutes": 75, "points": 450, "icon": "🔐", "color": "#22c55e", "env": "docker",
     "tags": ["crypto"],
     "tasks": [{"title": "Hash Kracking", "content": "# Hash Kracking\n\n```bash\nhashcat -m 0 -a 0 hash.txt rockyou.txt\n```",
                "points": 50, "questions": [
                    {"prompt": "MD5 üçün hashcat modul ID-si?", "kind": "numeric", "answer": "0"},
                    {"prompt": "SHA256 üçün hashcat modul ID-si?", "kind": "numeric", "answer": "1400"},
                    {"prompt": "hashcat-da wordlist ilə brute-force rejimini göstərən bayraq (-a)?", "kind": "numeric", "answer": "0"},
                    {"prompt": "John the Ripper-də ən məşhur wordlist faylının adı?", "kind": "text", "answer": "rockyou.txt"},
                ]}]},
    {"course_slug": "osint-techniques", "title": "OSINT Dərinləşdirilmiş",
     "summary": "Real hədəf haqqında tam məlumat profili qurmaq.",
     "level": "beginner", "minutes": 60, "points": 200, "icon": "🕵️", "color": "#f59e0b", "env": "web",
     "tags": ["osint", "recon"],
     "tasks": [{"title": "Domen kəşfi", "content": "# Domen Kəşfi\n\ncrt.sh, VirusTotal və Shodan ilə subdomen xəritəsi çıxarın.",
                "points": 40, "questions": [
                    {"prompt": "Shodan-da aktiv veb serverləri tapan filter?", "kind": "text", "answer": "port:80"},
                    {"prompt": "SSL sertifikat şəffaflığı loglarını axtaran sayt?", "kind": "text", "answer": "crt.sh"},
                    {"prompt": "IP və port əsaslı cihaz axtarışı üçün istifadə olunan xidmət?", "kind": "text", "answer": "Shodan"},
                    {"prompt": "Domenin qeydiyyat məlumatlarını göstərən komanda?", "kind": "text", "answer": "whois"},
                ]}]},
    {"course_slug": "api-security", "title": "API Fuzzing Labı",
     "summary": "REST API endpoint-lərində IDOR və broken auth zəifliklərini tapın.",
     "level": "intermediate", "minutes": 55, "points": 320, "icon": "🔌", "color": "#3b82f6", "env": "docker",
     "tags": ["api", "web"],
     "tasks": [{"title": "IDOR tapma", "content": "# IDOR\n\nİstifadəçi ID-ni dəyişərək başqa hesaba giriş cəhdi edin.",
                "points": 45, "questions": [
                    {"prompt": "IDOR-un açılımı nədir?", "kind": "text", "answer": "Insecure Direct Object Reference"},
                    {"prompt": "Fərqli istifadəçi ID-ləri ilə sürətli sınaq etmək üçün Burp Suite-in hansı modulu istifadə olunur?", "kind": "text", "answer": "Intruder"},
                    {"prompt": "API sənədləşməsi üçün ən çox istifadə olunan format/alət?", "kind": "text", "answer": "Swagger"},
                    {"prompt": "BOLA zəifliyinin açılımı nədir?", "kind": "text", "answer": "Broken Object Level Authorization"},
                ]}]},
    {"course_slug": "cloud-security-fundamentals", "title": "Bulud Konfiqurasiya Səhvləri",
     "summary": "Public S3 bucket və səhv IAM siyasətlərini aşkarlayın.",
     "level": "intermediate", "minutes": 65, "points": 350, "icon": "☁️", "color": "#6cb3ff", "env": "cloud",
     "tags": ["cloud"],
     "tasks": [{"title": "Public bucket tapma", "content": "# S3 Bucket Enumerasiyası\n\nAçıq bucket-ləri tapıb məzmununu siyahılayın.",
                "points": 40, "questions": [
                    {"prompt": "AWS-də obyekt saxlama xidmətinin adı?", "kind": "text", "answer": "S3"},
                    {"prompt": "AWS-də bucket icazələrini idarə edən siyasət növü?", "kind": "text", "answer": "IAM policy"},
                    {"prompt": "AWS instansının metadata servisinin standart IP ünvanı?", "kind": "text", "answer": "169.254.169.254"},
                    {"prompt": "Açıq S3 bucket-lərini toplu axtarmaq üçün istifadə olunan alət nümunəsi?", "kind": "text", "answer": "S3Scanner"},
                ]}]},
    {"course_slug": "malware-analysis-basics", "title": "Zərərli Proqram Triyaj Labı",
     "summary": "Naməlum bir nümunəni statik üsullarla təhlükəsiz analiz edin.",
     "level": "intermediate", "minutes": 70, "points": 380, "icon": "🦠", "color": "#ff7a8a", "env": "docker",
     "tags": ["malware", "forensics"],
     "tasks": [{"title": "String analizi", "content": "# Statik String Analizi\n\n```bash\nstrings sample.bin | less\n```",
                "points": 40, "questions": [
                    {"prompt": "Bir fayldakı oxuna bilən mətnləri çıxaran Linux komandası?", "kind": "text", "answer": "strings"},
                    {"prompt": "PE fayl formatının Windows-dakı adı?", "kind": "text", "answer": "Portable Executable"},
                    {"prompt": "Faylın hash dəyərini onlayn yoxlamaq üçün istifadə olunan məşhur platforma?", "kind": "text", "answer": "VirusTotal"},
                    {"prompt": "Statik analiz zamanı icra olunmayan mühiti necə adlandırırlar (təhlükəsiz analiz üçün)?", "kind": "text", "answer": "sandbox"},
                ]}]},
    {"course_slug": "active-directory-attacks", "title": "Active Directory Hücum Labı",
     "summary": "Kerberoasting və pass-the-hash texnikalarını praktik tətbiq edin.",
     "level": "advanced", "minutes": 90, "points": 550, "icon": "🏰", "color": "#c084fc", "env": "windows",
     "tags": ["active-directory", "windows"],
     "tasks": [{"title": "Kerberoasting", "content": "# Kerberoasting\n\nService account-ların TGS bilet hash-larını çıxarıb offline krak edin.",
                "points": 65, "questions": [
                    {"prompt": "Kerberos-da xidmət bileti hansı adla tanınır?", "kind": "text", "answer": "TGS"},
                    {"prompt": "Kerberoasting üçün istifadə olunan məşhur alət?", "kind": "text", "answer": "Rubeus"},
                    {"prompt": "Service account-ların TGS bileti hansı hash formatında çıxarılır (krakla üçün)?", "kind": "text", "answer": "krb5tgs"},
                    {"prompt": "AD-də DCSync hücumu nəyə imkan verir?", "kind": "choice", "points": 20,
                     "choices": [("Bütün domendəki parol hash-larını əldə etmək", True), ("Yalnız printer siyahısını görmək", False), ("Yalnız GPO-ları oxumaq", False), ("Şəbəkə sürətini artırmaq", False)]},
                ]}]},
    {"course_slug": "mobile-app-security", "title": "Mobil Tətbiq Pentest Labı",
     "summary": "Android APK-nı dekompilyasiya edərək gizli sirləri tapın.",
     "level": "intermediate", "minutes": 60, "points": 300, "icon": "📱", "color": "#39d353", "env": "docker",
     "tags": ["mobile"],
     "tasks": [{"title": "APK analiz", "content": "# APK Dekompilyasiyası\n\n```bash\napktool d app.apk\n```",
                "points": 45, "questions": [
                    {"prompt": "APK faylını dekompilyasiya edən əsas alət?", "kind": "text", "answer": "apktool"},
                    {"prompt": "APK-nı dekompilyasiya edib Java koduna çevirən alət?", "kind": "text", "answer": "jadx"},
                    {"prompt": "Android tətbiqinin manifest faylının adı?", "kind": "text", "answer": "AndroidManifest.xml"},
                    {"prompt": "Runtime-da tətbiqi analiz etmək üçün istifadə olunan Frida kimi alət kateqoriyası necə adlanır?", "kind": "text", "answer": "dynamic instrumentation"},
                ]}]},
]

# ─── Missions ────────────────────────────────────────────────────

MISSIONS_DATA = [
    {"slug": "sql-injection-101", "title": "SQL Injection 101", "difficulty": "easy", "icon": "💉", "color": "#3b82f6",
     "xp": 500, "hours": 2, "short_desc": "Manual və avtomatik SQL injection texnikalarını mənimsəyin.",
     "desc": "Bu missiyada SQL injection zəifliklərinin nə olduğunu öyrənəcək, in-band, blind və time-based SQLi tiplərini araşdıracaqsınız.",
     "passes": [{"title": "SQL Injection Nədir?", "order": 1, "minutes": 15,
                 "content": "<h2>SQL Injection nədir?</h2><p>İstifadəçi girişinin düzgün filtrlənmədiyi hallarda zərərli SQL kodunun icra edilməsidir.</p>"},
                {"title": "Union-based SQLi", "order": 2, "minutes": 20,
                 "content": "<h2>UNION-based SQLi</h2><p>UNION açar sözü ilə əlavə cədvəldən məlumat çıxarmaq mümkündür.</p>"}],
     "exam": {"title": "SQLi Yekun Sınaq", "passing": 70, "time": 20, "max_attempts": 3, "xp": 100,
              "questions": [
                  {"text": "SQL injection ilə login bypass üçün klassik payload?", "choices": [("' OR 1=1 --", True), ("<script>alert(1)</script>", False), ("../../../etc/passwd", False), ("${7*7}", False)]},
                  {"text": "Blind SQL injection-da hücumçu nəticəni necə görür?", "choices": [("Vaxt gecikməsi və ya true/false davranışı ilə", True), ("Birbaşa ekranda görür", False), ("Yalnız error mesajı ilə", False), ("Heç vaxt görə bilmir", False)]},
                  {"text": "SQLMap alətinin əsas funksiyası nədir?", "choices": [("SQL injection-u avtomatik aşkarlamaq və istismar etmək", True), ("Şəbəkə skan etmək", False), ("XSS tapmaq", False), ("Fayl şifrələmək", False)]},
                  {"text": "Prepared statement (parametrized query) SQL injection-u necə önləyir?", "choices": [("İstifadəçi girişini kod kimi deyil, məlumat kimi işləyir", True), ("Sorğunu şifrələyir", False), ("Cədvəl adlarını gizlədir", False), ("Yalnız GET metodunu bloklayır", False)]},
              ]}},
    {"slug": "xss-mastery", "title": "XSS Mastery", "difficulty": "medium", "icon": "⚡", "color": "#f59e0b",
     "xp": 750, "hours": 3, "short_desc": "Reflected, Stored və DOM-based XSS texnikalarını mənimsəyin.",
     "desc": "XSS müasir veb tətbiqlərinin ən çox rast gəlinən zəifliklərindən biridir. Bu missiyada bütün XSS növlərini öyrənəcəksiniz.",
     "passes": [{"title": "XSS Növləri", "order": 1, "minutes": 15,
                 "content": "<h2>XSS Növləri</h2><ul><li>Reflected XSS</li><li>Stored XSS</li><li>DOM-based XSS</li></ul>"}],
     "exam": {"title": "XSS Yekun Sınaq", "passing": 70, "time": 15, "max_attempts": 3, "xp": 75,
              "questions": [
                  {"text": "Stored XSS reflected-dan nə ilə fərqlənir?", "choices": [("Heç bir fərq yoxdur", False), ("Server tərəfdə saxlanılır, daimi təhlükədir", True), ("Yalnız admin görə bilər", False), ("DOM-da işləyir", False)]},
                  {"text": "DOM-based XSS harada icra olunur?", "choices": [("Yalnız klient tərəfdə, JavaScript vasitəsilə", True), ("Yalnız serverdə", False), ("Verilənlər bazasında", False), ("DNS serverində", False)]},
                  {"text": "HttpOnly cookie atributu nəyə qarşı qoruma verir?", "choices": [("JavaScript vasitəsilə cookie oxunmasına", True), ("SQL injection-a", False), ("DDoS hücumuna", False), ("Brute-force-a", False)]},
                  {"text": "XSS payload-ını test etmək üçün ən sadə 'proof of concept' skripti?", "choices": [("<script>alert(1)</script>", True), ("SELECT * FROM users", False), ("ping -c 4 target", False), ("' OR 1=1", False)]},
              ]}},
    {"slug": "network-pentest-basics", "title": "Şəbəkə Pentestinə Giriş", "difficulty": "easy", "icon": "📡", "color": "#14b8a6",
     "xp": 400, "hours": 2, "short_desc": "Port scanning, servis enumerasiyası və aktiv recon.",
     "desc": "Şəbəkə pentestinin əsasları: nmap ilə şəbəkə kəşfi, servis versiya aşkarlanması və ilk recon addımları.",
     "passes": [{"title": "Nmap ilə Port Scanning", "order": 1, "minutes": 20,
                 "content": "<h2>Nmap</h2><p>Nmap ən çox istifadə olunan port scanner-dir.</p>"}],
     "exam": {"title": "Şəbəkə Pentest Sınağı", "passing": 65, "time": 15, "max_attempts": 3, "xp": 60,
              "questions": [
                  {"text": "Nmap-da ən sürətli lakin ən az detallı skan növü?", "choices": [("SYN scan (-sS)", True), ("Version scan (-sV)", False), ("Script scan (-sC)", False), ("UDP scan (-sU)", False)]},
                  {"text": "Bir portun 'filtered' statusu nə deməkdir?", "choices": [("Firewall paketi süzür, cavab gəlmir", True), ("Port açıqdır", False), ("Port bağlıdır və cavab verir", False), ("Xidmət dayandırılıb", False)]},
                  {"text": "Passiv recon aktiv recon-dan nə ilə fərqlənir?", "choices": [("Hədəflə birbaşa əlaqə qurulmur", True), ("Daha sürətlidir", False), ("Yalnız port skan edir", False), ("Fərq yoxdur", False)]},
              ]}},
    {"slug": "linux-privilege-escalation-mission", "title": "Linux Privilege Escalation", "difficulty": "hard", "icon": "🧰", "color": "#8b5cf6",
     "xp": 1200, "hours": 4, "short_desc": "SUID, cron və kernel exploit ilə root əldə edin.",
     "desc": "Linux mühitində privilege escalation texnikalarının ümumi baxışı: SUID binary-lər, sudo konfiqurasiya səhvləri, cron job-lar.",
     "passes": [{"title": "SUID Binary İstismarı", "order": 1, "minutes": 25,
                 "content": "<h2>SUID Binary-lər</h2><p>SUID bit ilə işləyən binary-lər root səlahiyyəti ilə icra edilir.</p>"},
                {"title": "Sudo Konfiqurasiya Səhvləri", "order": 2, "minutes": 20,
                 "content": "<h2>Sudo İcazələri</h2><p><code>sudo -l</code> ilə mövcud icazələri yoxlayın.</p>"}],
     "exam": {"title": "Linux Privesc Sınaq", "passing": 75, "time": 25, "max_attempts": 3, "xp": 200,
              "questions": [
                  {"text": "SUID binary-ləri tapmaq üçün hansı find komandası istifadə edilir?", "choices": [("find / -suid", False), ("find / -perm -4000 -type f", True), ("find / -u=s", False), ("ls -la /bin", False)]},
                  {"text": "Yazıla bilən /etc/passwd faylı hansı hücuma şərait yaradır?", "choices": [("Yeni root istifadəçi əlavə etməyə", True), ("Yalnız oxuma icazəsi almağa", False), ("Şəbəkəni kəsməyə", False), ("Heç bir təhlükə yoxdur", False)]},
                  {"text": "LinPEAS aləti nə üçün istifadə olunur?", "choices": [("Linux privesc vektorlarını avtomatik axtarmaq", True), ("Şəbəkə trafikini izləmək", False), ("Fayl sıxmaq", False), ("Backup yaratmaq", False)]},
                  {"text": "Capabilities (məs. cap_setuid) SUID-dən nə ilə fərqlənir?", "choices": [("Bütün fayl əvəzinə yalnız müəyyən əməliyyatlara icazə verir", True), ("Heç bir fərq yoxdur", False), ("Yalnız Windows-da mövcuddur", False), ("Şəbəkə səviyyəsində işləyir", False)]},
              ]}},
    {"slug": "crypto-ctf", "title": "Kriptoqrafiya CTF", "difficulty": "medium", "icon": "🔐", "color": "#22c55e",
     "xp": 600, "hours": 2, "short_desc": "Base64, XOR, Caesar cipher və müasir kriptoqrafiya çətinlikləri.",
     "desc": "CTF üslubunda kriptoqrafiya tapşırıqları: şifrələnmiş mətnləri deşifrə etmək, hash-ləri krak etmək.",
     "passes": [{"title": "Klassik Şifrələr", "order": 1, "minutes": 20,
                 "content": "<h2>Klassik Şifrələr</h2><p>Caesar, ROT13, Vigenère. CyberChef ilə sınaqdan keçirin.</p>"}],
     "exam": {"title": "Kriptoqrafiya CTF Sınağı", "passing": 70, "time": 20, "max_attempts": 3, "xp": 70,
              "questions": [
                  {"text": "ROT13 şifrəsi nə qədər 'shift' istifadə edir?", "choices": [("13", True), ("26", False), ("7", False), ("3", False)]},
                  {"text": "XOR şifrələməsinin əsas zəifliyi nədir (açar təkrarlanarsa)?", "choices": [("Açar uzunluğu təkrarlanan mətn nümunələri ilə tapıla bilər", True), ("Heç bir zəifliyi yoxdur", False), ("Yalnız rəqəmlərlə işləyir", False), ("Şifrələmə mümkün deyil", False)]},
                  {"text": "Base64 kodlaşdırılmış mətnin sonunda tez-tez hansı simvol görünür?", "choices": [("=", True), ("#", False), ("%", False), ("&", False)]},
              ]}},
    {"slug": "osint-recon", "title": "OSINT Kəşfiyyatı", "difficulty": "easy", "icon": "🔎", "color": "#f59e0b",
     "xp": 350, "hours": 1, "short_desc": "Passiv məlumat toplama və hədəf profili qurmaq.",
     "desc": "OSINT texnikaları: whois, DNS, Google dork-ları, crt.sh və Shodan ilə hədəf haqqında tam profil qurmaq.",
     "passes": [{"title": "Passiv Recon Alətləri", "order": 1, "minutes": 20,
                 "content": "<h2>Passiv Recon</h2><ul><li>whois</li><li>dig/nslookup</li><li>crt.sh</li><li>Shodan</li></ul>"}],
     "exam": {"title": "OSINT Sınağı", "passing": 65, "time": 15, "max_attempts": 3, "xp": 50,
              "questions": [
                  {"text": "Google-da 'site:' operatoru nəyi məhdudlaşdırır?", "choices": [("Axtarışı müəyyən domenlə", True), ("Yalnız şəkilləri", False), ("Yalnız tarixi", False), ("Fayl ölçüsünü", False)]},
                  {"text": "crt.sh vasitəsilə nə tapılır?", "choices": [("SSL sertifikatları vasitəsilə subdomenlər", True), ("Şəbəkə portları", False), ("Parol hash-ları", False), ("Fiziki ünvanlar", False)]},
                  {"text": "OSINT-də 'passiv' recon nəyi nəzərdə tutur?", "choices": [("Hədəflə birbaşa əlaqə qurmadan məlumat toplamaq", True), ("Hədəfə birbaşa hücum etmək", False), ("Yalnız telefon zəngi etmək", False), ("Fiziki müşahidə", False)]},
              ]}},
    {"slug": "burp-suite-pro", "title": "Burp Suite Pro", "difficulty": "medium", "icon": "🎯", "color": "#ff7a8a",
     "xp": 900, "hours": 3, "short_desc": "Proxy, Repeater, Intruder və Scanner ilə peşəkar veb pentest.",
     "desc": "Burp Suite Community və Professional fərqini öyrənin, proxy quraşdırın, Repeater ilə manual test edin.",
     "passes": [{"title": "Proxy Qurulumu", "order": 1, "minutes": 15,
                 "content": "<h2>Burp Proxy</h2><p>Brauzer → Burp → Hədəf. Intercept On/Off. Sertifikat yükləmək.</p>"}],
     "exam": {"title": "Burp Suite Sınağı", "passing": 65, "time": 15, "max_attempts": 3, "xp": 60,
              "questions": [
                  {"text": "Burp Suite-də bir sorğunu tutub yenidən dəyişdirərək göndərmək üçün hansı modul istifadə olunur?", "choices": [("Repeater", True), ("Intruder", False), ("Decoder", False), ("Sequencer", False)]},
                  {"text": "Burp-un Intruder modulu əsasən nə üçün istifadə olunur?", "choices": [("Avtomatlaşdırılmış payload fuzzing", True), ("Trafiki şifrələmək", False), ("Şəbəkə xəritələmək", False), ("Fayl bərpası", False)]},
                  {"text": "Burp Suite-də HTTPS trafikini oxumaq üçün nə lazımdır?", "choices": [("Burp-un CA sertifikatını brauzerə quraşdırmaq", True), ("VPN qoşulmaq", False), ("Firewall-u söndürmək", False), ("Heç nə, avtomatik işləyir", False)]},
              ]}},
    {"slug": "csrf-attack-defense", "title": "CSRF Hücum və Müdafiə", "difficulty": "medium", "icon": "🔁", "color": "#6b7280",
     "xp": 550, "hours": 2, "short_desc": "CSRF token bypass və SameSite cookie qorunması.",
     "desc": "CSRF hücumlarının mexanizmi, token-based müdafiə və SameSite cookie atributlarının tədqiqi.",
     "passes": [{"title": "CSRF Mexanizmi", "order": 1, "minutes": 20,
                 "content": "<h2>CSRF Necə İşləyir?</h2><p>Zərərli sayt istifadəçinin brauzerindəki cookie-dən istifadə edərək hədəf sayta sorğu göndərir.</p>"}],
     "exam": {"title": "CSRF Sınağı", "passing": 65, "time": 15, "max_attempts": 3, "xp": 55,
              "questions": [
                  {"text": "CSRF hücumu üçün əsas şərt nədir?", "choices": [("Qurbanın hədəf saytda aktiv sessiyasının olması", True), ("Qurbanın admin olması", False), ("HTTPS istifadə edilməməsi", False), ("Firewall-un olmaması", False)]},
                  {"text": "CSRF token-in məqsədi nədir?", "choices": [("Hər sorğunun həqiqətən istifadəçi tərəfindən göndərildiyini təsdiqləmək", True), ("Sorğunu şifrələmək", False), ("Sessiyanı uzatmaq", False), ("Cookie-ni silmək", False)]},
                  {"text": "SameSite=Strict cookie atributu nəyi bloklayır?", "choices": [("Cookie-nin başqa saytdan göndərilən sorğularla göndərilməsini", True), ("Bütün cookie-ləri", False), ("Yalnız GET sorğularını", False), ("Heç nəyi", False)]},
              ]}},
    {"slug": "api-security-101", "title": "API Təhlükəsizliyi 101", "difficulty": "medium", "icon": "🔌", "color": "#3b82f6",
     "xp": 650, "hours": 2, "short_desc": "IDOR, broken auth və rate-limit zəifliklərini tapın.",
     "desc": "Müasir REST/GraphQL API-lərdə ən çox rast gəlinən təhlükəsizlik zəiflikləri və onların istismarı.",
     "passes": [{"title": "IDOR Tapma", "order": 1, "minutes": 20,
                 "content": "<h2>IDOR</h2><p>Obyekt ID-lərini dəyişərək icazəsiz girişi sınayın.</p>"}],
     "exam": {"title": "API Sınaq", "passing": 70, "time": 15, "max_attempts": 3, "xp": 80,
              "questions": [
                  {"text": "IDOR-un açılımı nədir?", "choices": [("Insecure Direct Object Reference", True), ("Internal Data Object Request", False), ("Invalid Domain Object Reference", False), ("Indirect Data Origin Request", False)]},
                  {"text": "REST API-də autentifikasiya üçün ən çox istifadə olunan üsul?", "choices": [("JWT/OAuth2 token", True), ("Yalnız IP whitelist", False), ("Yalnız CAPTCHA", False), ("Heç biri lazım deyil", False)]},
                  {"text": "API-də 'excessive data exposure' zəifliyi nə deməkdir?", "choices": [("Server lazım olandan çox məlumat qaytarır", True), ("Server heç bir məlumat qaytarmır", False), ("Yalnız şəkil sızır", False), ("Yalnız log fayl sızır", False)]},
                  {"text": "GraphQL API-lərdə hansı spesifik risk daha çox rast gəlinir?", "choices": [("Mürəkkəb/dərin sorğular ilə DoS (query depth)", True), ("Yalnız SQL injection", False), ("Yalnız CSRF", False), ("Heç bir fərqli risk yoxdur", False)]},
              ]}},
    {"slug": "active-directory-attacks-mission", "title": "Active Directory Hücumları", "difficulty": "hard", "icon": "🏰", "color": "#c084fc",
     "xp": 1100, "hours": 4, "short_desc": "Kerberoasting və pass-the-hash ilə AD mühitini ələ keçirin.",
     "desc": "Active Directory mühitində kəşfiyyatdan tam domain compromise-ə qədər hücum zənciri.",
     "passes": [{"title": "Kerberos Əsasları", "order": 1, "minutes": 25,
                 "content": "<h2>Kerberos</h2><p>TGT, TGS və Kerberoasting hücumunun məntiqi.</p>"}],
     "exam": {"title": "Active Directory Sınağı", "passing": 70, "time": 20, "max_attempts": 3, "xp": 90,
              "questions": [
                  {"text": "Kerberoasting hansı hesab növünü hədəf alır?", "choices": [("Service account-ları (SPN-i olan hesablar)", True), ("Yalnız qonaq hesabları", False), ("Yalnız kompüter hesabları", False), ("Yalnız qrup hesabları", False)]},
                  {"text": "Pass-the-hash hücumunda nə istifadə olunur?", "choices": [("Parolun özü deyil, NTLM hash-i", True), ("Yalnız Kerberos bileti", False), ("Yalnız e-poçt ünvanı", False), ("Yalnız IP ünvanı", False)]},
                  {"text": "Golden Ticket hücumu hansı hesabın hash-inə əsaslanır?", "choices": [("krbtgt", True), ("Administrator", False), ("Guest", False), ("Domain User", False)]},
              ]}},
    {"slug": "cloud-misconfigurations", "title": "Bulud Konfiqurasiya Səhvləri", "difficulty": "medium", "icon": "☁️", "color": "#6cb3ff",
     "xp": 700, "hours": 3, "short_desc": "AWS/Azure/GCP-də ən çox rast gəlinən konfiqurasiya səhvləri.",
     "desc": "Public bucket-lər, açıq IAM siyasətləri və metadata servisi sızmaları üzərindən bulud mühitinin öyrənilməsi.",
     "passes": [{"title": "S3 Bucket Enumerasiyası", "order": 1, "minutes": 20,
                 "content": "<h2>Public Bucket-lər</h2><p>Açıq S3 bucket-ləri necə tapmaq və məzmununu oxumaq.</p>"}],
     "exam": {"title": "Bulud Təhlükəsizlik Sınağı", "passing": 65, "time": 15, "max_attempts": 3, "xp": 65,
              "questions": [
                  {"text": "Public S3 bucket-in ən böyük riski nədir?", "choices": [("Həssas məlumatların hər kəsə açıq olması", True), ("Yalnız yavaşlıq", False), ("Yalnız yüksək xərc", False), ("Heç bir risk yoxdur", False)]},
                  {"text": "Bulud instansının metadata servisinə SSRF vasitəsilə giriş nəyə səbəb ola bilər?", "choices": [("Müvəqqəti IAM credential-ların oğurlanmasına", True), ("Yalnız CPU yükünün artmasına", False), ("Yalnız şəbəkə gecikməsinə", False), ("Heç bir nəticəyə", False)]},
                  {"text": "IAM-də 'ən az imtiyaz' prinsipi nə deməkdir?", "choices": [("İstifadəçiyə yalnız lazım olan minimal icazələri vermək", True), ("Bütün istifadəçilərə admin icazəsi vermək", False), ("Heç kimə icazə verməmək", False), ("Yalnız root istifadəçiyə icazə vermək", False)]},
              ]}},
    {"slug": "social-engineering-tactics", "title": "Sosial Mühəndislik Taktikaları", "difficulty": "easy", "icon": "🎭", "color": "#ff7a8a",
     "xp": 450, "hours": 2, "short_desc": "Phishing, pretexting və insan amilini hədəf alan hücumlar.",
     "desc": "İnsan psixologiyasından istifadə edən hücum vektorları və onlara qarşı müdafiə strategiyaları.",
     "passes": [{"title": "Phishing Növləri", "order": 1, "minutes": 15,
                 "content": "<h2>Phishing</h2><p>Spear phishing, whaling və vishing arasındakı fərqlər.</p>"}],
     "exam": {"title": "Sosial Mühəndislik Sınağı", "passing": 60, "time": 15, "max_attempts": 3, "xp": 50,
              "questions": [
                  {"text": "Spear phishing adi phishing-dən nə ilə fərqlənir?", "choices": [("Konkret şəxsə/təşkilata hədəflənmiş və fərdiləşdirilmişdir", True), ("Yalnız telefonla edilir", False), ("Yalnız SMS ilə edilir", False), ("Fərq yoxdur", False)]},
                  {"text": "Whaling hücumu kimi hədəf alır?", "choices": [("Yüksək vəzifəli rəhbərləri (CEO, CFO və s.)", True), ("Yalnız yeni işçiləri", False), ("Yalnız tələbələri", False), ("Yalnız IT işçilərini", False)]},
                  {"text": "Sosial mühəndislik hücumlarına qarşı ən effektiv müdafiə nədir?", "choices": [("Davamlı təhlükəsizlik maarifləndirməsi (awareness training)", True), ("Yalnız firewall qurmaq", False), ("Yalnız antivirus", False), ("İnternetə çıxışı bağlamaq", False)]},
              ]}},
]

# ─── Learning Plans ──────────────────────────────────────────────

PLANS_DATA = [
    {"slug": "bug-bounty-hunter", "title": "Bug Bounty Hunter",
     "summary": "Veb zəifliklərini tapmaq üçün tam marşrut.",
     "description": "Bu öyrənmə yolu sizi Bug Bounty proqramlarında iştiraka hazırlayır: əsas veb zəiflikləri, Burp Suite və real lab təcrübəsi.",
     "level": "intermediate", "hours": 30, "icon": "🎯", "featured": True,
     "course_slugs": ["web-security-fundamentals", "advanced-pentesting", "api-security"]},
    {"slug": "penetration-tester", "title": "Penetration Tester",
     "summary": "Sıfırdan peşəkar pentester-ə: şəbəkə, veb, sistem.",
     "description": "Tamşamilli pentest marşrutu: şəbəkə kəşfindən exploitation və post-exploit-ə qədər.",
     "level": "advanced", "hours": 60, "icon": "🏴", "featured": True,
     "course_slugs": ["network-security-101", "linux-privilege-escalation", "advanced-pentesting"]},
    {"slug": "crypto-expert", "title": "Kriptoqrafiya Mütəxəssisi",
     "summary": "Şifrələmə, hash və kriptoanaliz üzrə dərin bilik.",
     "description": "Klassik və müasir kriptoqrafiya üzrə dərin bilik: hash kracking, kriptoanaliz və asimmetrik kriptoqrafiya.",
     "level": "intermediate", "hours": 25, "icon": "🔐", "featured": False,
     "course_slugs": ["cryptography-basics"]},
    {"slug": "osint-specialist", "title": "OSINT Mütəxəssisi",
     "summary": "Passiv kəşfiyyat və hədəf profili qurmaq.",
     "description": "OSINT texnikalarını mənimsəyin və real hədəflər haqqında tam məlumat profili qurmağı öyrənin.",
     "level": "beginner", "hours": 15, "icon": "🔎", "featured": False,
     "course_slugs": ["osint-techniques"]},
    {"slug": "red-team-specialist", "title": "Red Team Specialist",
     "summary": "Advanced persistent threat simulyasiyası və AD compromise.",
     "description": "Red team əməliyyatlarında iştirak: sosial mühəndislik, exploitation, lateral movement.",
     "level": "advanced", "hours": 80, "icon": "🚩", "featured": True,
     "course_slugs": ["advanced-pentesting", "active-directory-attacks", "social-engineering"]},
    {"slug": "api-security-engineer", "title": "API Təhlükəsizlik Mühəndisi",
     "summary": "Müasir API-ləri hücumlardan qorumaq üçün tam bilik bazası.",
     "description": "REST/GraphQL API-lərin təhlükəsizliyi: autentifikasiya, autorizasiya və rate-limiting strategiyaları.",
     "level": "intermediate", "hours": 20, "icon": "🔌", "featured": False,
     "course_slugs": ["api-security", "web-security-fundamentals"]},
    {"slug": "cloud-security-engineer", "title": "Bulud Təhlükəsizlik Mühəndisi",
     "summary": "AWS/Azure/GCP mühitlərini konfiqurasiya səhvlərindən qorumaq.",
     "description": "Bulud infrastrukturunun təhlükəsizliyi: IAM, şəbəkə seqmentasiyası və monitorinq.",
     "level": "intermediate", "hours": 22, "icon": "☁️", "featured": False,
     "course_slugs": ["cloud-security-fundamentals"]},
    {"slug": "malware-analyst", "title": "Zərərli Proqram Analitiki",
     "summary": "Statik və dinamik analiz üsulları ilə zərərli proqramları araşdırmaq.",
     "description": "Malware analizinin əsasları: sandbox mühitləri, statik analiz və davranış izləməsi.",
     "level": "advanced", "hours": 35, "icon": "🦠", "featured": False,
     "course_slugs": ["malware-analysis-basics", "linux-privilege-escalation"]},
]


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

def ensure_tags():
    result = {}
    for name in TAGS:
        tag, _ = RoomTag.objects.get_or_create(slug=name, defaults={"name": name.replace("-", " ").title()})
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
        course, _ = Course.objects.update_or_create(
            slug=cd["slug"],
            defaults={
                "title": cd["title"], "description": cd["description"],
                "category": categories.get(cd["category"]), "icon": cd["icon"], "is_published": True,
            },
        )
        courses_by_slug[cd["slug"]] = course

        for ld in cd.get("lessons", []):
            lesson, _ = Lesson.objects.update_or_create(
                course=course, order=ld["order"],
                defaults={"title": ld["title"], "content": ld["content"]},
            )
            for qi, lq in enumerate(ld.get("questions", []), start=1):
                lesson_q, _ = LessonQuestion.objects.update_or_create(
                    lesson=lesson, order=qi, defaults={"text": lq["text"], "points": 10},
                )
                sync_choices(
                    lesson_q, options=[(chr(65 + i), text) for i, (text, _) in enumerate(lq["choices"])],
                    correct_letter=next(chr(65 + i) for i, (_, correct) in enumerate(lq["choices"]) if correct),
                    choice_model=LessonQuestionChoice, text_field="text",
                )

        for i, qd in enumerate(cd.get("questions", []), start=1):
            q, _ = Question.objects.update_or_create(
                course=course, title=qd["title"],
                defaults={
                    "prompt": qd["prompt"], "question_type": qd["type"], "level": qd["level"],
                    "points": qd["points"], "starter_code": qd.get("starter_code", ""),
                    "order": i,
                },
            )
            if qd["type"] == "closed" and qd.get("choices"):
                letters = ["A", "B", "C", "D", "E"]
                options = [(letters[i], text) for i, (text, _) in enumerate(qd["choices"])]
                correct = next(letters[i] for i, (_, ok) in enumerate(qd["choices"]) if ok)
                sync_choices(q, options=options, correct_letter=correct, choice_model=QuestionChoice, text_field="text")

    return courses_by_slug


def seed_rooms(courses_by_slug, tags):
    for rd in ROOMS_DATA:
        course = courses_by_slug.get(rd["course_slug"])
        if not course:
            continue
        room, _ = Room.objects.update_or_create(
            slug=slugify(rd["title"]),
            defaults={
                "course": course, "title": rd["title"], "summary": rd["summary"],
                "description": rd.get("description", rd["summary"]), "level": rd["level"],
                "estimated_minutes": rd["minutes"], "points": rd["points"], "icon": rd["icon"],
                "cover_color": rd["color"], "env": rd.get("env", "docker"), "is_published": True, "order": 0,
            },
        )
        room.tags.set([tags[t] for t in rd.get("tags", []) if t in tags])

        for ti, td in enumerate(rd.get("tasks", []), start=1):
            task, _ = Task.objects.update_or_create(
                room=room, slug=slugify(td["title"]),
                defaults={"title": td["title"], "content": td["content"], "order": ti, "points": td["points"]},
            )
            for qi, qd in enumerate(td.get("questions", []), start=1):
                kind_map = {"text": TaskAnswerKind.TEXT, "numeric": TaskAnswerKind.NUMERIC, "choice": TaskAnswerKind.CHOICE}
                kind = kind_map.get(qd.get("kind", "text"), TaskAnswerKind.TEXT)
                tq, _ = TaskQuestion.objects.update_or_create(
                    task=task, order=qi,
                    defaults={
                        "prompt": qd["prompt"], "kind": kind, "answer": str(qd.get("answer", "")),
                        "points": qd.get("points", 15),
                    },
                )
                if kind == TaskAnswerKind.CHOICE and qd.get("choices"):
                    letters = ["A", "B", "C", "D", "E"]
                    options = [(letters[i], text) for i, (text, _) in enumerate(qd["choices"])]
                    correct = next(letters[i] for i, (_, ok) in enumerate(qd["choices"]) if ok)
                    sync_choices(tq, options=options, correct_letter=correct, choice_model=TaskQuestionChoice, text_field="text")


def seed_missions():
    diff_map = {
        "easy": MissionDifficultyChoices.EASY, "medium": MissionDifficultyChoices.MEDIUM,
        "hard": MissionDifficultyChoices.HARD, "expert": MissionDifficultyChoices.EXPERT,
    }
    for i, md in enumerate(MISSIONS_DATA, start=1):
        mission, _ = Mission.objects.update_or_create(
            slug=md["slug"],
            defaults={
                "title": md["title"], "description": md["desc"], "short_description": md["short_desc"],
                "difficulty": diff_map.get(md["difficulty"], MissionDifficultyChoices.MEDIUM),
                "cover_color": md["color"], "icon": md["icon"], "estimated_hours": md["hours"],
                "xp_reward": md["xp"], "order": i, "is_published": True,
            },
        )

        for pd in md.get("passes", []):
            MissionPass.objects.update_or_create(
                mission=mission, order=pd["order"],
                defaults={"title": pd["title"], "content": pd["content"], "estimated_minutes": pd["minutes"], "is_published": True},
            )

        ed = md.get("exam")
        if ed:
            exam, _ = MissionExam.objects.update_or_create(
                mission=mission,
                defaults={
                    "title": ed["title"], "passing_score": ed["passing"], "time_limit_minutes": ed["time"],
                    "max_attempts": ed["max_attempts"], "xp_reward": ed["xp"], "is_published": True,
                },
            )
            for qi, qd in enumerate(ed.get("questions", []), start=1):
                eq, _ = MissionExamQuestion.objects.update_or_create(
                    exam=exam, order=qi,
                    defaults={"question_text": qd["text"], "question_type": MissionExamQuestionTypeChoices.CLOSED},
                )
                letters = ["A", "B", "C", "D", "E"]
                options = [(letters[i], text) for i, (text, _) in enumerate(qd["choices"])]
                correct = next(letters[i] for i, (_, ok) in enumerate(qd["choices"]) if ok)
                sync_choices(eq, options=options, correct_letter=correct, choice_model=MissionExamChoice, text_field="choice_text")
        elif hasattr(mission, "mission_exam"):
            mission.mission_exam.delete()


def seed_plans(courses_by_slug):
    for pd in PLANS_DATA:
        plan, _ = LearningPlan.objects.update_or_create(
            slug=pd["slug"],
            defaults={
                "title": pd["title"], "summary": pd["summary"], "description": pd["description"],
                "level": pd["level"], "estimated_hours": pd["hours"], "icon": pd["icon"],
                "is_featured": pd["featured"], "is_published": True,
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
    LessonQuestionChoice.objects.all().delete()
    LessonQuestion.objects.all().delete()
    Lesson.objects.all().delete()
    LearningPlanCourse.objects.all().delete()
    LearningPlan.objects.all().delete()
    Enrollment.objects.all().delete()
    Course.objects.all().delete()
    Category.objects.all().delete()


# ═══════════════════════════════════════════════════════════════
#  COMMAND
# ═══════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = "Xakker üçün demo məzmun seed-i (kurslar, laboratoriyalar, missiyalar, planlar)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Seed-dən əvvəl bütün kontenti sil.")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts.get("reset"):
            self.stdout.write(self.style.WARNING("Məzmun silinir..."))
            wipe_content()

        self.stdout.write("Kateqoriyalar və teqlər...")
        cats = ensure_categories()
        tags = ensure_tags()

        self.stdout.write("Kurslar, dərslər və sərbəst tədris sualları...")
        courses = seed_courses(cats)

        self.stdout.write("Lab otaqları və tapşırıqlar...")
        seed_rooms(courses, tags)

        self.stdout.write("Missiyalar...")
        seed_missions()

        self.stdout.write("Öyrənmə yolları...")
        seed_plans(courses)

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Seed tamamlandı:\n"
            f"  {Category.objects.count()} kateqoriya\n"
            f"  {RoomTag.objects.count()} teq\n"
            f"  {Course.objects.count()} kurs\n"
            f"  {Lesson.objects.count()} dərs\n"
            f"  {Question.objects.count()} sərbəst tədris sualı\n"
            f"  {Room.objects.count()} lab otağı\n"
            f"  {Task.objects.count()} task\n"
            f"  {TaskQuestion.objects.count()} task sualı\n"
            f"  {Mission.objects.count()} missiya\n"
            f"  {MissionPass.objects.count()} missiya mərhələsi\n"
            f"  {MissionExam.objects.count()} imtahan\n"
            f"  {LearningPlan.objects.count()} öyrənmə yolu"
        ))
