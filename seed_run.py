import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from django.utils.text import slugify
from courses.models import (
    Category, Course, Lesson, Question, QuestionChoice,
    Room, RoomTag, Task, TaskQuestion, TaskQuestionChoice,
    Mission, MissionPass, MissionExam, MissionExamQuestion, MissionExamChoice,
    LearningPlan, LearningPlanCourse,
    MissionDifficultyChoices, TaskAnswerKind,
)

@transaction.atomic
def seed():
    # ── Tags ──────────────────────────────────────────────────────────
    tag_names = [
        'linux','windows','recon','enumeration','exploit','privesc',
        'burp','sqli','xss','ssrf','lfi','csrf','nmap','wireshark',
        'osint','crypto','docker','active-directory','reverse',
        'forensics','malware','network','web',
    ]
    tags = {}
    for n in tag_names:
        t, _ = RoomTag.objects.get_or_create(slug=n, defaults={'name': n.replace('-',' ').title()})
        tags[n] = t
    print('Tags OK')

    # ── Categories ────────────────────────────────────────────────────
    cats_data = [
        ('Web Tehlukesizliyi',  'web',      'Web', '#3b82f6'),
        ('Sebeke Tehlukesizliyi','network', 'Net', '#14b8a6'),
        ('Sistem Tehlukesizliyi','system',  'Sys', '#8b5cf6'),
        ('Kriptoqrafiya',        'crypto',  'Kri', '#22c55e'),
        ('OSINT ve Kesf',        'osint',   'OSI', '#f59e0b'),
        ('Offensive Security',   'offensive','Off', '#ff3b3b'),
    ]
    cats = {}
    for name, slug, icon, color in cats_data:
        c, _ = Category.objects.update_or_create(
            slug=slug,
            defaults={'name': name, 'icon': icon, 'color': color, 'description': name},
        )
        cats[slug] = c
    print('Categories OK')

    # ── Courses ───────────────────────────────────────────────────────
    courses_input = [
        {
            'slug': 'web-security-fundamentals',
            'title': 'Web Tehlukesizliyi Esaslari',
            'cat': 'web', 'icon': 'Web',
            'desc': 'HTTP, HTML, JavaScript, DOM ve web zeifliklerinin umumi menzerese.',
            'lessons': [
                (1, 'HTTP Protokolu', 'HTTP sorgu/cavab sikli, metodlar GET/POST/PUT/DELETE, status kodlar ve headerlar.'),
                (2, 'SQL Injection', 'SQL injection zeifliyi input sanitizasiyasinin ustunluyunden istifade edir.'),
                (3, 'XSS - Cross Site Scripting', 'Stored, Reflected ve DOM-based XSS novleri. Cookie ogurlanmasi.'),
                (4, 'CSRF Hucumlari', 'Cross-Site Request Forgery - istifadecinin adina arzuolunmaz sorgu gondermek.'),
            ],
            'questions': [
                {'title': 'XSS novleri', 'type': 'closed', 'level': 'beginner', 'points': 25,
                 'prompt': 'Asagidakilardan hansi XSS novu deyil?',
                 'choices': [('Reflected XSS', False), ('Stored XSS', False), ('DOM-based XSS', False), ('SQL XSS', True)]},
                {'title': 'OWASP Top 10', 'type': 'closed', 'level': 'intermediate', 'points': 30,
                 'prompt': 'OWASP Top 10-da SQLi hansi kategoriyaya aiddir (2021)?',
                 'choices': [('A01: Broken Access Control', False), ('A03: Injection', True), ('A05: Security Misconfiguration', False), ('A07: Auth Failures', False)]},
                {'title': 'HTTP metodlari', 'type': 'closed', 'level': 'beginner', 'points': 20,
                 'prompt': 'Servere melumat gondermek ucun hansi HTTP metodu istifade edilir?',
                 'choices': [('GET', False), ('POST', True), ('DELETE', False), ('HEAD', False)]},
                {'title': 'SQL Injection izahi', 'type': 'open', 'level': 'beginner', 'points': 30,
                 'prompt': 'SQL Injection zeifligini qisaca izah edin ve iki qoruma usulu yazin.'},
                {'title': 'CSRF token', 'type': 'open', 'level': 'intermediate', 'points': 35,
                 'prompt': 'CSRF token nedir ve nece qorunma temin edir? Adimlarla izah edin.'},
                {'title': 'Port skanlama', 'type': 'terminal', 'level': 'beginner', 'points': 50,
                 'prompt': 'Hedef serverde aciq portlari tapın ve HTTP xidmetini askarlayin.',
                 'starter': 'nmap -sV 10.10.10.1'},
                {'title': 'Directory brute-force', 'type': 'terminal', 'level': 'intermediate', 'points': 60,
                 'prompt': 'Gobuster ile hedef web serverde gizli direktoriyalari tapin.',
                 'starter': 'gobuster dir -u http://target.local'},
            ],
        },
        {
            'slug': 'network-security-101',
            'title': 'Sebeke Tehlukesizliyi 101',
            'cat': 'network', 'icon': 'Net',
            'desc': 'TCP/IP, subnets, routing, firewall ve network protokollarinin tehlukesizlik aspektleri.',
            'lessons': [
                (1, 'TCP/IP Modeli', '7 qatli OSI modeli ve 4 qatli TCP/IP modeli. Her qatin tehlukesizlik uzre rolu.'),
                (2, 'Port Nomreleri ve Protokollar', 'Cox istifade olunan portlar: 22 SSH, 80 HTTP, 443 HTTPS, 3306 MySQL, 21 FTP.'),
                (3, 'Firewall ve IDS/IPS', 'Stateful/stateless firewall ferqi. IDS vs IPS. Snort ve Suricata.'),
            ],
            'questions': [
                {'title': 'HTTP portu', 'type': 'closed', 'level': 'beginner', 'points': 20,
                 'prompt': 'HTTP xidmeti standart olaraq hansi portda isleyir?',
                 'choices': [('21', False), ('22', False), ('80', True), ('443', False)]},
                {'title': 'SSH portu', 'type': 'closed', 'level': 'beginner', 'points': 20,
                 'prompt': 'SSH protokolu standart olaraq hansi portu istifade edir?',
                 'choices': [('21', False), ('22', True), ('23', False), ('25', False)]},
                {'title': 'Nmap port scan', 'type': 'terminal', 'level': 'beginner', 'points': 40,
                 'prompt': 'Hedef hostda butun aciq portlari ve servis versiyalarini tapin.',
                 'starter': 'nmap -sV 10.10.11.1'},
                {'title': 'Firewall ferqi', 'type': 'open', 'level': 'intermediate', 'points': 35,
                 'prompt': 'Stateful ve stateless firewall arasindaki esus ferqi izah edin. Hansini ne vaxt secmeli?'},
            ],
        },
        {
            'slug': 'linux-privilege-escalation',
            'title': 'Linux Privilege Escalation',
            'cat': 'system', 'icon': 'Sys',
            'desc': 'SUID, cron job, kernel exploit ve sudo misconfig ile root almaq.',
            'lessons': [
                (1, 'SUID Binary-lar', 'SUID bit nedir? find / -perm -4000 ile tapilan fayllari nece istifade etmeli.'),
                (2, 'Sudo Misconfigurations', 'sudo -l ile icazeleri yoxla. GTFOBins-den privesc vektorlari tap.'),
                (3, 'Cron Job Exploitation', 'crontab -l ve /etc/cron* qovluqlari. Yazila bilen script ile code injection.'),
            ],
            'questions': [
                {'title': 'SUID tapma', 'type': 'terminal', 'level': 'intermediate', 'points': 55,
                 'prompt': 'Sistemde SUID bit ile isleyen butun binary-lari tapin.',
                 'starter': 'find / -perm -4000 -type f 2>/dev/null'},
                {'title': 'Sudo icazeleri', 'type': 'terminal', 'level': 'beginner', 'points': 35,
                 'prompt': 'Cari istifadecinin hansi sudo icazeleri oldugunu tapin.',
                 'starter': 'sudo -l'},
                {'title': 'Privesc usullari', 'type': 'open', 'level': 'advanced', 'points': 50,
                 'prompt': 'Linux-da privilege escalation ucun en az 4 usul sadalayın ve her birini qisaca izah edin.'},
            ],
        },
        {
            'slug': 'cryptography-basics',
            'title': 'Kriptoqrafiya Esaslari',
            'cat': 'crypto', 'icon': 'Kri',
            'desc': 'AES, RSA, hash funksiyalari, sertifikatlar ve kriptoanalize giris.',
            'lessons': [
                (1, 'Simmetrik Sifrelemler', 'AES, DES, 3DES. Block vs stream cipher. CBC, GCM rejimleri.'),
                (2, 'Asimmetrik Sifrelemler', 'RSA, ECDSA. Public/private acar cutu. Reqemsal imza.'),
                (3, 'Hash Funksiyalari', 'MD5, SHA1, SHA256, bcrypt. Rainbow table ve salt. Password hashing.'),
            ],
            'questions': [
                {'title': 'Asimmetrik alqoritm', 'type': 'closed', 'level': 'intermediate', 'points': 35,
                 'prompt': 'Asagidakilardan hansi asimmetrik sifrelemedir?',
                 'choices': [('AES', False), ('DES', False), ('RSA', True), ('Blowfish', False)]},
                {'title': 'Base64 decode', 'type': 'terminal', 'level': 'beginner', 'points': 40,
                 'prompt': 'Asagidaki Base64 metni desifre edin: eGtyezEybWVuNHRpb259',
                 'starter': "echo 'eGtyezEybWVuNHRpb259' | base64 -d"},
                {'title': 'Hash novu', 'type': 'closed', 'level': 'beginner', 'points': 25,
                 'prompt': 'Password hashing ucun hansi alqoritm tovsiye edilir?',
                 'choices': [('MD5', False), ('SHA1', False), ('bcrypt', True), ('SHA256', False)]},
                {'title': 'Salt nedir?', 'type': 'open', 'level': 'beginner', 'points': 30,
                 'prompt': 'Kriptoqrafiya kontekstinde salt nedir? Rainbow table hucumunun qarsisini nece alir?'},
            ],
        },
        {
            'slug': 'osint-techniques',
            'title': 'OSINT Kesf Texnikalari',
            'cat': 'osint', 'icon': 'OSI',
            'desc': 'Aciq menbe kesfi: whois, DNS, crt.sh, Google dorks ve Shodan.',
            'lessons': [
                (1, 'DNS ve Whois', 'whois, dig, nslookup ile domain melumatlarini toplamaq.'),
                (2, 'Certificate Transparency', 'crt.sh ile subdomain discovery. SSL sertifikat tarixcesi.'),
                (3, 'Google Dorks', 'site:, filetype:, inurl:, intitle: ile hedef haqqinda melumat toplamaq.'),
            ],
            'questions': [
                {'title': 'Google Dork', 'type': 'open', 'level': 'beginner', 'points': 25,
                 'prompt': 'site:example.az filetype:pdf Google dork-u ne edir? Ustunlugu ve catismazligi nedir?'},
                {'title': 'Subdomain kesfi', 'type': 'closed', 'level': 'intermediate', 'points': 30,
                 'prompt': 'Certificate transparency loglarindan subdomain tapmaq ucun hansi xidmet istifade edilir?',
                 'choices': [('Shodan', False), ('crt.sh', True), ('VirusTotal', False), ('Censys', False)]},
                {'title': 'WHOIS sorgusu', 'type': 'terminal', 'level': 'beginner', 'points': 30,
                 'prompt': 'Cari sisteme kim kimi login oldugunu tapın.',
                 'starter': 'whoami'},
            ],
        },
        {
            'slug': 'advanced-pentesting',
            'title': 'Advanced Pentesting',
            'cat': 'offensive', 'icon': 'Off',
            'desc': 'Web ve network uzre irelilemis pentest texnikalari.',
            'lessons': [
                (1, 'SSRF Exploitasiyasi', 'Server-Side Request Forgery - server vasitesile daxili resurslara muraciet.'),
                (2, 'XXE Injection', 'XML External Entity injection ile fayllari oxumaq ve SSRF.'),
                (3, 'Deserialization', 'Insecure deserialization ile RCE. Java, PHP, Python gadget chains.'),
            ],
            'questions': [
                {'title': 'SSRF hedifi', 'type': 'closed', 'level': 'advanced', 'points': 45,
                 'prompt': 'SSRF hucumunun esus hedifi nedir?',
                 'choices': [
                     ('Client brauzeri hedef almaq', False),
                     ('Serveri daxili resurslara sorgu gondermeye mecburetmek', True),
                     ('SQLi etmek', False), ('XSS payload yeritmek', False)]},
                {'title': 'XXE izahi', 'type': 'open', 'level': 'advanced', 'points': 50,
                 'prompt': 'XML External Entity injection nedir? Hansi hallarda bas verir ve nece qarsisini almaq olar?'},
                {'title': 'Curl ile SSRF', 'type': 'terminal', 'level': 'advanced', 'points': 70,
                 'prompt': 'Hedef serverin daxili metadata servisine sorgu gonderin.',
                 'starter': 'curl http://169.254.169.254/latest/meta-data/'},
            ],
        },
    ]

    courses = {}
    for cd in courses_input:
        course, _ = Course.objects.update_or_create(
            slug=cd['slug'],
            defaults={'title': cd['title'], 'description': cd['desc'],
                      'category': cats.get(cd['cat']), 'icon': cd['icon'], 'is_published': True},
        )
        courses[cd['slug']] = course
        for order, title, content in cd['lessons']:
            Lesson.objects.update_or_create(course=course, order=order,
                defaults={'title': title, 'content': content})
        for i, qd in enumerate(cd['questions'], 1):
            q, _ = Question.objects.update_or_create(
                course=course, title=qd['title'],
                defaults={'prompt': qd['prompt'], 'question_type': qd['type'],
                          'level': qd['level'], 'points': qd['points'],
                          'starter_code': qd.get('starter', ''), 'order': i},
            )
            q.choices.all().delete()
            for ci, (text, correct) in enumerate(qd.get('choices', []), 1):
                QuestionChoice.objects.create(question=q, text=text, is_correct=correct, order=ci)
    print('Courses OK')

    # ── Rooms ─────────────────────────────────────────────────────────
    rooms_input = [
        {
            'course': 'web-security-fundamentals',
            'title': 'SQL Injection Lab',
            'summary': 'DVWA benzeri muhitde SQL injection texnikalarini ogren.',
            'level': 'intermediate', 'minutes': 60, 'points': 300,
            'icon': 'Inj', 'color': '#3b82f6', 'env': 'docker',
            'tags': ['sqli', 'web', 'burp'],
            'tasks': [
                {'title': 'Login bypass', 'content': '# SQL Injection\n\nLogin bypass ucun: admin\' --', 'points': 40,
                 'questions': [
                     {'prompt': 'Login bypass ucun en sade payload?', 'kind': 'text', 'answer': "admin' --"},
                     {'prompt': 'SQL-da comment baslatmaq ucun hansi simvol?', 'kind': 'text', 'answer': '--'},
                 ]},
                {'title': 'UNION extraction', 'content': '# UNION SELECT\n\nSutun sayini mueyyen et ve users cedvelini oxu.', 'points': 50,
                 'questions': [
                     {'prompt': 'Sutun sayini mueyyen etmek ucun hansi SQL acur soz?', 'kind': 'text', 'answer': 'ORDER BY'},
                 ]},
            ],
        },
        {
            'course': 'web-security-fundamentals',
            'title': 'XSS Arena',
            'summary': 'Reflected, Stored ve DOM XSS vektorlarini praktik arasdır.',
            'level': 'intermediate', 'minutes': 50, 'points': 250,
            'icon': 'XSS', 'color': '#f59e0b', 'env': 'docker',
            'tags': ['xss', 'web', 'burp'],
            'tasks': [
                {'title': 'Reflected XSS tapma', 'content': '# Reflected XSS\n\ndocument.cookie ile cookie ogurlamaq.', 'points': 35,
                 'questions': [
                     {'prompt': 'Cookie ogurlamaq ucun XSS payload-i neden istifade edir?', 'kind': 'text', 'answer': 'document.cookie'},
                 ]},
                {'title': 'Stored XSS', 'content': '# Stored XSS\n\nComment sahesine payload yeritmek.', 'points': 40,
                 'questions': [
                     {'prompt': 'Stored ve Reflected XSS arasındaki esus ferq?', 'kind': 'choice', 'points': 15,
                      'choices': [('Hec bir ferq yoxdur', False), ('Stored server-de saxlanılır, daimi tehlukedir', True), ('Reflected daha tehlukeligdir', False), ('DOM-based daha sadedir', False)]},
                 ]},
            ],
        },
        {
            'course': 'network-security-101',
            'title': 'Corp Network Lab',
            'summary': 'Korporativ sebeke kesfi ve lateral movement.',
            'level': 'intermediate', 'minutes': 90, 'points': 400,
            'icon': 'Net', 'color': '#14b8a6', 'env': 'vpn',
            'tags': ['network', 'nmap', 'enumeration'],
            'tasks': [
                {'title': 'Sebeke kesfi', 'content': '# Sebeke Haritasi\n\nnmap ile aktiv hostlari tap: nmap -sn 10.10.10.0/24', 'points': 50,
                 'questions': [
                     {'prompt': 'Subnet uzre host discovery ucun nmap bayraği?', 'kind': 'text', 'answer': '-sn'},
                     {'prompt': '10.10.10.0/24 subnet-de nece host mumkundur?', 'kind': 'numeric', 'answer': '254'},
                 ]},
            ],
        },
        {
            'course': 'linux-privilege-escalation',
            'title': 'Linux Privesc Lab',
            'summary': 'SUID, sudo ve cron job uzrunde privilege escalation.',
            'level': 'advanced', 'minutes': 80, 'points': 500,
            'icon': 'Prv', 'color': '#8b5cf6', 'env': 'linux',
            'tags': ['privesc', 'linux', 'exploit'],
            'tasks': [
                {'title': 'SUID Exploitation', 'content': '# SUID Binary Exploitation\n\nSUID bit olan fayllari tap.', 'points': 60,
                 'questions': [
                     {'prompt': 'SUID binary-lari tapmaq ucun hansi find komandasindan istifade edilir?', 'kind': 'text', 'answer': 'find / -perm -4000 -type f'},
                 ]},
            ],
        },
        {
            'course': 'linux-privilege-escalation',
            'title': 'Windows Privesc Lab',
            'summary': 'Token manipulation, service hijacking ve registry-based privesc.',
            'level': 'advanced', 'minutes': 100, 'points': 600,
            'icon': 'Win', 'color': '#6b7280', 'env': 'windows',
            'tags': ['privesc', 'windows'],
            'tasks': [
                {'title': 'Token manipulation', 'content': '# Windows Token Manipulation\n\nSeImpersonatePrivilege ile privesc.', 'points': 70,
                 'questions': [
                     {'prompt': 'SeImpersonatePrivilege tokenini istismar etmek ucun exploit ailesi?', 'kind': 'choice', 'points': 20,
                      'choices': [('Potato exploits', True), ('Buffer overflow', False), ('Kernel panic', False), ('SUID bypass', False)]},
                 ]},
            ],
        },
        {
            'course': 'cryptography-basics',
            'title': 'Crypto Vault',
            'summary': 'Sifrelemme bypass, hash kracking ve acar ciharma.',
            'level': 'advanced', 'minutes': 75, 'points': 450,
            'icon': 'Cry', 'color': '#22c55e', 'env': 'docker',
            'tags': ['crypto', 'reverse'],
            'tasks': [
                {'title': 'Hash Cracking', 'content': '# Hash Cracking\n\nhashcat -m 0 -a 0 hash.txt rockyou.txt', 'points': 50,
                 'questions': [
                     {'prompt': 'MD5 hashcat module ID?', 'kind': 'numeric', 'answer': '0'},
                     {'prompt': 'Rockyou.txt nedir?', 'kind': 'choice', 'points': 15,
                      'choices': [('Bir hash aleti', False), ('Wordlist - parol siyahisi', True), ('Exploit framework', False), ('VPN konfiqurasiyasi', False)]},
                 ]},
            ],
        },
        {
            'course': 'osint-techniques',
            'title': 'OSINT Deep Dive',
            'summary': 'Real hedef haqqinda tam melumat profili qurmaq.',
            'level': 'beginner', 'minutes': 60, 'points': 200,
            'icon': 'Eye', 'color': '#f59e0b', 'env': 'browser',
            'tags': ['osint', 'recon'],
            'tasks': [
                {'title': 'Domain recon', 'content': '# Domain Kesfi\n\ncrt.sh, VirusTotal ve Shodan ile tam subdomain xeritesi cikar.', 'points': 40,
                 'questions': [
                     {'prompt': 'Shodan-da hansi filter aktiv web serverleri tapir?', 'kind': 'text', 'answer': 'port:80'},
                 ]},
            ],
        },
    ]

    for rd in rooms_input:
        course = courses.get(rd['course'])
        if not course:
            continue
        room, _ = Room.objects.update_or_create(
            slug=slugify(rd['title']),
            defaults={'course': course, 'title': rd['title'], 'summary': rd['summary'],
                      'description': rd['summary'], 'level': rd['level'],
                      'estimated_minutes': rd['minutes'], 'points': rd['points'],
                      'icon': rd['icon'], 'cover_color': rd['color'],
                      'env': rd['env'], 'is_published': True, 'order': 0},
        )
        room.tags.set([tags[t] for t in rd['tags'] if t in tags])
        for ti, td in enumerate(rd['tasks'], 1):
            task, _ = Task.objects.update_or_create(
                room=room, slug=slugify(td['title']),
                defaults={'title': td['title'], 'content': td['content'],
                          'order': ti, 'points': td['points']},
            )
            task.questions.all().delete()
            for qi, qd in enumerate(td['questions'], 1):
                kind_map = {'text': TaskAnswerKind.TEXT, 'numeric': TaskAnswerKind.NUMERIC, 'choice': TaskAnswerKind.CHOICE}
                kind = kind_map.get(qd.get('kind', 'text'), TaskAnswerKind.TEXT)
                tq = TaskQuestion.objects.create(
                    task=task, prompt=qd['prompt'], kind=kind,
                    answer=str(qd.get('answer', '')), hint=qd.get('hint', ''),
                    explanation=qd.get('explanation', ''), points=qd.get('points', 15), order=qi,
                )
                for ci, (text, correct) in enumerate(qd.get('choices', []), 1):
                    TaskQuestionChoice.objects.create(question=tq, text=text, is_correct=correct, order=ci)
    print('Rooms OK')

    # ── Missions ──────────────────────────────────────────────────────
    diff_map = {
        'easy': MissionDifficultyChoices.EASY,
        'medium': MissionDifficultyChoices.MEDIUM,
        'hard': MissionDifficultyChoices.HARD,
        'expert': MissionDifficultyChoices.EXPERT,
    }

    missions_input = [
        {
            'slug': 'sql-injection-101', 'title': 'SQL Injection 101',
            'diff': 'easy', 'icon': 'Inj', 'color': '#3b82f6', 'xp': 500, 'hours': 2,
            'short': 'Manual ve avtomatik SQL injection texnikalarini meninse.',
            'desc': 'Bu missiyada SQL injection zeifliklerini oyrenerek, Burp Suite ile praktik test edeceksiniz.',
            'passes': [
                {'title': 'SQL Injection Nedir?', 'order': 1, 'minutes': 15,
                 'content': '<h2>SQL Injection nedir?</h2><p>SQL injection, istifadeci girisinin duzgun filtrlenmediyi hallarda bedniiyyetli SQL kodunun verilene bazasina yeridilib icra edilmesidir.</p><pre><code>SELECT * FROM users WHERE username=\'admin\'--\';</code></pre>'},
                {'title': 'Union-based SQLi', 'order': 2, 'minutes': 20,
                 'content': '<h2>UNION-based SQLi</h2><p>UNION acar sozu ile elave cedvelden melumat ciхarmaq mumkundur.</p>'},
                {'title': 'Blind SQLi ve sqlmap', 'order': 3, 'minutes': 25,
                 'content': '<h2>Blind SQL Injection</h2><p>Cavabin birbasas gorunmediyi hallarda Boolean ve ya time-based usullar istifade edilir.</p>'},
            ],
            'exam': {
                'title': 'SQLi Yekun Sinaq', 'passing': 70, 'time': 20, 'max_attempts': 3, 'xp': 100,
                'questions': [
                    {'text': "SQL injection ile login bypass ucun klassik payload?", 'type': 'closed', 'order': 1,
                     'choices': [("' OR 1=1 --", True), ('<script>alert(1)</script>', False), ('../../../etc/passwd', False), ('${7*7}', False)]},
                ],
            },
        },
        {
            'slug': 'xss-mastery', 'title': 'XSS Mastery',
            'diff': 'medium', 'icon': 'XSS', 'color': '#f59e0b', 'xp': 750, 'hours': 3,
            'short': 'Reflected, Stored ve DOM-based XSS texnikalarini meninse.',
            'desc': 'XSS muasir web tetbiqlerinin en cox rast gelinene zeifliklerinden biridir.',
            'passes': [
                {'title': 'XSS Novleri', 'order': 1, 'minutes': 15,
                 'content': '<h2>XSS Novleri</h2><ul><li><strong>Reflected XSS</strong>: Server cavabinda birbasas eks olunur</li><li><strong>Stored XSS</strong>: Verilene bazasinda saxlanilir</li><li><strong>DOM-based XSS</strong>: Client tereffde bas verir</li></ul>'},
                {'title': 'Cookie Theft ve Session Hijack', 'order': 2, 'minutes': 20,
                 'content': '<h2>Cookie Theft</h2><p>document.location ile cookie ogurlamaq.</p>'},
            ],
            'exam': {
                'title': 'XSS Sinaq', 'passing': 70, 'time': 15, 'max_attempts': 3, 'xp': 75,
                'questions': [
                    {'text': 'Stored XSS Reflected-dan neyile ferlenir?', 'type': 'closed', 'order': 1,
                     'choices': [('Hec bir ferq yoxdur', False), ('Server terfde saxlanilir, daimi tehlukedir', True), ('Yalniz admin gore biler', False), ('DOM-da isleyir', False)]},
                ],
            },
        },
        {
            'slug': 'network-pentest-basics', 'title': 'Network Pentest Esaslari',
            'diff': 'easy', 'icon': 'Net', 'color': '#14b8a6', 'xp': 400, 'hours': 2,
            'short': 'Port scanning, service enumeration ve aktiv recon.',
            'desc': 'Network pentestinin esaslari: nmap ile sebeke kesfi, servis versiya askarlama.',
            'passes': [
                {'title': 'Nmap ile Port Scanning', 'order': 1, 'minutes': 20,
                 'content': '<h2>Nmap</h2><p>Nmap dunyanin en cox istifade olunan port scanner-idir.</p><pre><code>nmap -sV -sC -p- target.lab</code></pre>'},
                {'title': 'Service Enumeration', 'order': 2, 'minutes': 20,
                 'content': '<h2>Servis Enumeration</h2><p>Aciq portlardaki servisleri derinlemesine arasdır.</p>'},
            ],
            'exam': None,
        },
        {
            'slug': 'linux-privesc-mission', 'title': 'Linux Privilege Escalation',
            'diff': 'hard', 'icon': 'Prv', 'color': '#8b5cf6', 'xp': 1200, 'hours': 4,
            'short': 'SUID, cron ve kernel exploit ile root almaq.',
            'desc': 'Linux muhitinde privilege escalation texnikalarinin umumi bakisi.',
            'passes': [
                {'title': 'SUID Binary Exploitation', 'order': 1, 'minutes': 25,
                 'content': '<h2>SUID Binary-lar</h2><p>SUID bit ile isleyen binary-lar root selahhiyyeti ile icra edilir.</p><pre><code>find / -perm -u=s -type f 2>/dev/null</code></pre>'},
                {'title': 'Sudo Misconfigurations', 'order': 2, 'minutes': 20,
                 'content': '<h2>Sudo Icazeleri</h2><pre><code>sudo -l</code></pre>'},
                {'title': 'Cron Job Exploitation', 'order': 3, 'minutes': 25,
                 'content': '<h2>Cron Job Exploitation</h2><p>Root cron job yazila bilen script-i isleirdirse, ona reverse shell elave et.</p>'},
            ],
            'exam': {
                'title': 'Linux Privesc Sinaq', 'passing': 75, 'time': 25, 'max_attempts': 3, 'xp': 200,
                'questions': [
                    {'text': 'SUID binary-lari tapmaq ucun hansi find komandasindan istifade edilir?', 'type': 'closed', 'order': 1,
                     'choices': [('find / -suid', False), ('find / -perm -4000 -type f', True), ('find / -u=s', False), ('ls -la /bin', False)]},
                    {'text': 'sudo -l komandasinin meqsedi nedir?', 'type': 'closed', 'order': 2,
                     'choices': [('Root olaraq login olmaq', False), ('Mevcud sudo icazeleri siyahilamaq', True), ('Parolu sifirlamaq', False), ('Butun xidmetleri gostermek', False)]},
                ],
            },
        },
        {
            'slug': 'crypto-ctf', 'title': 'Kriptoqrafiya CTF',
            'diff': 'medium', 'icon': 'Cry', 'color': '#22c55e', 'xp': 600, 'hours': 2,
            'short': 'Base64, XOR, Caesar cipher ve muasir kriptoqrafiya.',
            'desc': 'CTF uslubu kriptoqrafiya tapsiriqlari.',
            'passes': [
                {'title': 'Klassik Sifreler', 'order': 1, 'minutes': 20,
                 'content': '<h2>Klassik Sifreler</h2><p>Caesar, ROT13, Vigenere. CyberChef ile sinaqdan kecir.</p>'},
                {'title': 'Base64 ve Hex', 'order': 2, 'minutes': 15,
                 'content': '<h2>Encoding vs Encryption</h2><p>Base64 sifreleme deyil - sadece encoding-dir.</p>'},
            ],
            'exam': None,
        },
        {
            'slug': 'osint-recon', 'title': 'OSINT Kesf',
            'diff': 'easy', 'icon': 'Eye', 'color': '#f59e0b', 'xp': 350, 'hours': 1,
            'short': 'Passiv melumat toplama ve hedef profili qurmaq.',
            'desc': 'OSINT texnikalari: whois, DNS, Google dorks, crt.sh ve Shodan.',
            'passes': [
                {'title': 'Passive Recon Aletleri', 'order': 1, 'minutes': 20,
                 'content': '<h2>Passive Recon</h2><ul><li>whois - domain qeydiyyati</li><li>dig/nslookup - DNS sorgulari</li><li>crt.sh - sertifikat seffafliq loglari</li><li>Shodan - internet-bagli cihazlar</li></ul>'},
            ],
            'exam': None,
        },
        {
            'slug': 'burp-suite-pro', 'title': 'Burp Suite Pro',
            'diff': 'medium', 'icon': 'Brp', 'color': '#ff7a8a', 'xp': 900, 'hours': 3,
            'short': 'Proxy, Repeater, Intruder ve Scanner ile professional web pentest.',
            'desc': 'Burp Suite CE ve Professional ferqini ogren, proxy-e intercept qur.',
            'passes': [
                {'title': 'Proxy qurulumu', 'order': 1, 'minutes': 15,
                 'content': '<h2>Burp Proxy</h2><p>Brauzer - Burp - Hedef. Intercept On/Off. Sertifikat yuklemek.</p>'},
                {'title': 'Repeater ve Intruder', 'order': 2, 'minutes': 25,
                 'content': '<h2>Repeater</h2><p>Sorğulari tekrarla ve deyis. Intruder ile parametrε wordlist gonder.</p>'},
            ],
            'exam': None,
        },
        {
            'slug': 'csrf-attack-defense', 'title': 'CSRF Hucum ve Mudafie',
            'diff': 'medium', 'icon': 'Csr', 'color': '#6b7280', 'xp': 550, 'hours': 2,
            'short': 'CSRF token bypass ve SameSite cookie qorunmasi.',
            'desc': 'CSRF hucumlarinin mexanizmi ve token-based mudafie.',
            'passes': [
                {'title': 'CSRF Mexanizmi', 'order': 1, 'minutes': 20,
                 'content': '<h2>CSRF Nece Isleyir?</h2><p>Bedniiyyetli sayt istifadecinin cookie-sinden istifade ederek hedef sayta sorgu gonderir.</p>'},
            ],
            'exam': None,
        },
    ]

    for i, md in enumerate(missions_input, 1):
        mission, _ = Mission.objects.update_or_create(
            slug=md['slug'],
            defaults={'title': md['title'], 'description': md['desc'],
                      'short_description': md['short'], 'difficulty': diff_map[md['diff']],
                      'cover_color': md['color'], 'icon': md['icon'],
                      'estimated_hours': md['hours'], 'xp_reward': md['xp'],
                      'order': i, 'is_published': True},
        )
        for pd in md['passes']:
            MissionPass.objects.update_or_create(
                mission=mission, order=pd['order'],
                defaults={'title': pd['title'], 'content': pd['content'],
                          'estimated_minutes': pd['minutes'], 'is_published': True},
            )
        ed = md.get('exam')
        if ed:
            exam, _ = MissionExam.objects.update_or_create(
                mission=mission,
                defaults={'title': ed['title'], 'passing_score': ed['passing'],
                          'time_limit_minutes': ed['time'], 'max_attempts': ed['max_attempts'],
                          'xp_reward': ed['xp'], 'is_published': True},
            )
            exam.questions.all().delete()
            for qd in ed['questions']:
                eq = MissionExamQuestion.objects.create(
                    exam=exam, question_text=qd['text'],
                    question_type=qd['type'], order=qd['order'],
                )
                for ci, (text, correct) in enumerate(qd.get('choices', []), 1):
                    MissionExamChoice.objects.create(question=eq, choice_text=text, is_correct=correct, order=ci)
    print('Missions OK')

    # ── Learning Plans ────────────────────────────────────────────────
    plans_input = [
        {'slug': 'bug-bounty-hunter', 'title': 'Bug Bounty Hunter',
         'summary': 'Web zeifliklerini tapmaq ucun tam marsrut.',
         'desc': 'Bug Bounty programlarinda istirak etmeye hazirlanmaq ucun tam yol.',
         'level': 'intermediate', 'hours': 30, 'icon': 'Bbh', 'featured': True,
         'courses': ['web-security-fundamentals', 'advanced-pentesting']},
        {'slug': 'penetration-tester', 'title': 'Penetration Tester',
         'summary': 'Sifirdan professional pentester-e. Network, web, system.',
         'desc': 'Tamshamilli pentest marsrutu: sebeke kesfindin exploitation-a qeder.',
         'level': 'advanced', 'hours': 60, 'icon': 'Pen', 'featured': True,
         'courses': ['network-security-101', 'linux-privilege-escalation', 'advanced-pentesting']},
        {'slug': 'crypto-expert', 'title': 'Kriptoqrafiya Mutexessisi',
         'summary': 'Sifreleme, hash, steqanoqrafiya ve kriptoanaliz.',
         'desc': 'Klassik ve muasir kriptoqrafiya uzre derin bilik.',
         'level': 'intermediate', 'hours': 25, 'icon': 'Cry', 'featured': False,
         'courses': ['cryptography-basics']},
        {'slug': 'osint-specialist', 'title': 'OSINT Mutexessisi',
         'summary': 'Passiv kesf ve hedef profili qurmaq.',
         'desc': 'OSINT texnikalarini meninse ve real hederler haqqinda profil qur.',
         'level': 'beginner', 'hours': 15, 'icon': 'Eye', 'featured': False,
         'courses': ['osint-techniques']},
        {'slug': 'red-team-specialist', 'title': 'Red Team Specialist',
         'summary': 'Advanced persistent threat simulyasiyasi ve zero-day kesfi.',
         'desc': 'Red team emiyyatlarinda istirak: sosial muhendislik, exploitation, lateral movement.',
         'level': 'advanced', 'hours': 80, 'icon': 'Red', 'featured': True,
         'courses': ['advanced-pentesting', 'linux-privilege-escalation', 'network-security-101']},
    ]

    for pd in plans_input:
        plan, _ = LearningPlan.objects.update_or_create(
            slug=pd['slug'],
            defaults={'title': pd['title'], 'summary': pd['summary'], 'description': pd['desc'],
                      'level': pd['level'], 'estimated_hours': pd['hours'],
                      'icon': pd['icon'], 'is_featured': pd['featured'], 'is_published': True},
        )
        LearningPlanCourse.objects.filter(plan=plan).delete()
        for idx, cs in enumerate(pd['courses'], 1):
            if cs in courses:
                LearningPlanCourse.objects.create(plan=plan, course=courses[cs], order=idx)
    print('Plans OK')

    # ── Summary ───────────────────────────────────────────────────────
    print(f'\nSeed tamamlandi:')
    print(f'  {Course.objects.count()} kurs')
    print(f'  {Lesson.objects.count()} ders')
    print(f'  {Question.objects.count()} oyrenmə sualı')
    print(f'  {Room.objects.count()} lab otagi')
    print(f'  {Task.objects.count()} task')
    print(f'  {TaskQuestion.objects.count()} task suali')
    print(f'  {Mission.objects.count()} missiya')
    print(f'  {MissionPass.objects.count()} missiya merhele')
    print(f'  {LearningPlan.objects.count()} oyrenmə yolu')

seed()
