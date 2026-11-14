# AutoMarket.al — Faza 1

Django 5 · HTML/CSS/JS · SQLite (dev) / PostgreSQL (prod) · shqip + anglisht (/sq/, /en/)

## Nisja lokale
```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py compilemessages
python manage.py seed_brands
python manage.py createsuperuser
python manage.py runserver
```
Hap http://127.0.0.1:8000/ → ridrejtohet te /sq/. Admin: /sq/admin/ · Statistika: /sq/admin/stats/
Teste: `python manage.py test`

## Cilësime kryesore
- Admin → "Site settings": publikim menjëherë ose pas miratimit.
- Admin → Cars: miratim/refuzim, VIP (veprime masive). Admin → Dealerships: "Verified" vendoset vetëm këtu.

## Prodhim
Variabla mjedisi: `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS=automarket.al,www.automarket.al`,
`DJANGO_CSRF_TRUSTED_ORIGINS=https://automarket.al`, `DB_ENGINE=postgres`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`,
`DJANGO_MEDIA_ROOT=/var/www/automarket/media`, email SMTP (`DJANGO_EMAIL_BACKEND`, etj.).
```
python manage.py migrate && python manage.py collectstatic --noinput && python manage.py compilemessages
gunicorn config.wsgi:application --bind 127.0.0.1:8000
```
Nginx para gunicorn: HTTPS me Let's Encrypt (certbot), dhe shërbe `/media/` direkt nga `DJANGO_MEDIA_ROOT`
(Django nuk i shërben media-t kur DEBUG=0). Dërgo header `X-Forwarded-Proto: https`.

## Faza 2 (shtuar)
Vetë-regjistrim autosallonesh (`/dealerships/new/`, pa mundësi vetë-verifikimi), reklama partnerësh (Admin → Partner ads, aktivizim manual), plane abonimi (Admin → Dealer subscriptions, aktivizim manual), skadim VIP: `python manage.py expire_vip` (vendose në cron çdo ditë).

## Çfarë mungon
Pagesat VIP/abonimet/reklamat (vetëm struktura; nuk ka pagesa të simuluara), përkthim automatik i përshkrimeve,
rikuperimi i fjalëkalimit kërkon SMTP real në prodhim.


## Siguria — çfarë është e mbrojtur
- **Autentikim:** fjalëkalimet ruhen me hash të Django (PBKDF2), me validim të fortësisë; rikuperim fjalëkalimi me token; dalja vetëm me POST.
- **Mbrojtje nga forca brute:** hyrja bllokohet pas 5 dështimeve (IP+emër) ose 20 (IP) brenda 15 minutash; regjistrimi (10/orë/IP), raportimet (10/orë/IP) dhe emailet e rikuperimit (5/orë/IP) kufizohen.
- **Autorizim:** përdoruesit modifikojnë/fshijnë vetëm njoftimet dhe fotot e veta; autosalloni vetëm nga anëtarët; shenja "e verifikuar" vetëm nga admini; panelet e statistikave vetëm për staff.
- **Formularë:** CSRF kudo; validim në backend; kufij gjatësie; max 10 njoftime/ditë/përdorues; max 3 autosalone/përdorues.
- **Foto:** kontrollohet përmbajtja reale (jo vetëm shtesa), vetëm JPG/PNG/WebP, max 5 MB secila, max 12 për njoftim. **Çdo foto ri-kodohet në WebP: fshihen metadatat EXIF (përfshirë vendndodhjen GPS), korrigjohet rrotullimi dhe zvogëlohet në max 2000px.**
- **Content-Security-Policy:** vetëm skriptet nga domeni ynë ekzekutohen (asnjë skript inline ose i jashtëm), faqja nuk mund të vendoset në iframe, dhe kamera/mikrofoni/vendndodhja janë të çaktivizuara. Një test kontrollon që asnjë faqe nuk ka kod inline. Admini përjashtohet (ka kodin e vet). Nëse më vonë i shërben fotot nga një CDN/S3, shto domenin te `img-src` në `apps/core/middleware.py`.
- **Konfigurim:** DEBUG është OFF si parazgjedhje (aktivizohet vetëm nga `manage.py` për zhvillim lokal); në prodhim aplikacioni nuk niset pa `DJANGO_SECRET_KEY`; HTTPS, HSTS, cookie të sigurta kur DEBUG=0.

## Lista para publikimit online (obligative)
1. `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY` i gjatë e rastësor (`python -c "import secrets;print(secrets.token_urlsafe(60))"`), `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`.
2. Ekzekuto `DJANGO_DEBUG=0 python manage.py collectstatic --noinput` (me DEBUG=0 shprehimisht).
3. PostgreSQL në vend të SQLite; backup të rregullt të databazës dhe të `media/`.
4. Nginx para gunicorn me HTTPS (Let's Encrypt), `client_max_body_size 64m;`, dhe `X-Forwarded-For`/`X-Forwarded-Proto`; vendos `DJANGO_BEHIND_PROXY=1`.
5. Ndrysho adresën e adminit (`DJANGO_ADMIN_URL`), përdor fjalëkalim të fortë për superuser-in.
6. Me disa procese gunicorn vendos `REDIS_URL` (pa të, limitet e tentativave numërohen veç për çdo proces).
7. Ekzekuto `python manage.py check --deploy` — duhet të mbetet vetëm paralajmërimi W021 (HSTS preload). Është opsional: aktivizoje me `DJANGO_HSTS_PRELOAD=1` vetëm kur je i sigurt që i gjithë domeni do të mbetet HTTPS përgjithmonë, sepse është e vështirë ta zhbësh.

## Çfarë NUK është mbuluar ende
Verifikim i emailit gjatë regjistrimit, CAPTCHA, autentikim me dy hapa për adminin, skanim antivirus i skedarëve, ruajtje e fotove në S3/CDN, monitorim dhe alarme. Para se të pranosh përdorues realë, rekomandohet një rishikim i pavarur sigurie.

## Publikimi në GitHub
```
git init
git add .
git status        # kontrollo që nuk shfaqen db.sqlite3, media/, .venv, .env
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/EMRI-YT/automarket.git
git push -u origin main
```
Para se ta bësh repozitorin publik: zgjidh një licencë (pa licencë, kodi mbetet "të gjitha të drejtat e rezervuara"), kontrollo që nuk ke vënë asnjë fjalëkalim a çelës në kod, dhe në GitHub aktivizo Settings → Code security (Dependabot alerts, secret scanning).
