# Studentu laika plānotājs

Python + Flask tīmekļa lietotne, kas nolasa **publisku testa Google Calendar** (iCalendar/ICS), saglabā notikumus **SQLite** datubāzē un aprēķina brīvos laika intervālus. Darbojas GitHub Codespaces (bez Tkinter).

## 1. Izveido testa kalendāru

1. Izveido **atsevišķu Google kontu** tikai testēšanai (paroli citiem nedod).
2. Atver https://calendar.google.com un izveido **atsevišķu testa kalendāru** ar izdomātiem notikumiem.
3. Google Calendar -> Settings -> izvēlies testa kalendāru -> **Access permissions for events** -> **Make available to public**. Apstiprini. **Svarīgi:** publiskie notikumi ir redzami jebkuram ar piekļuvi kalendāra saitei; nelieto reālus personas datus. Ja Google Workspace administrators aizliedz publiskošanu, šis variants neder.
4. Tajos pašos iestatījumos -> **Integrate calendar** -> nokopē **Public address in iCal format** (`https://calendar.google.com/calendar/ical/.../public/basic.ics`). **Neizmanto** "Secret address in iCal format".

Ja saite atgriež 404 vai nav pieejama, pārbaudi, vai kalendārs tiešām ir publisks un izmantota **public** ICS adrese.

## 2. Palaišana GitHub Codespaces

1. Ievieto šo projekta saturu GitHub repozitorijā.
2. GitHub -> **Code -> Codespaces -> Create codespace on main**.
3. Terminālī (pirmajā palaišanā bibliotēkas parasti jau instalētas automātiski):

   ```bash
   python -m pip install -r requirements.txt
   export GOOGLE_CALENDAR_ICS_URL='https://calendar.google.com/calendar/ical/REPLACE_ME/public/basic.ics'
   python app.py
   ```

4. Codespaces -> **Ports** -> 8000 -> **Open in Browser**. Ja vajag, pārbaudi, ka porta redzamība ir **Private**.
5. Lietotnē spied **Sinhronizēt kalendāru**, izvēlies datumu un spied **Aprēķināt**.

**Pasniedzējam:** viņš var palaist programmu savā Codespace ar šīm pašām komandām. Lai nebūtu jākopē ICS saite, repozitorija **Codespaces Secrets** var iestatīt `GOOGLE_CALENDAR_ICS_URL` (bet privātie lietotāja secrets automātiski nav koplietoti ar pasniedzēju), vai arī publiskā testa kalendāra ICS adresi var ierakstīt README, jo tā jau ir publiska. **Nepublicē testa Google konta paroli, `credentials.json`, `token.json` vai Google Calendar Secret iCal saiti.**

## 3. Palaišana lokāli

```bash
python -m pip install -r requirements.txt
# Linux/macOS:
export GOOGLE_CALENDAR_ICS_URL='https://calendar.google.com/calendar/ical/REPLACE_ME/public/basic.ics'
python app.py
```

Windows PowerShell:

```powershell
$env:GOOGLE_CALENDAR_ICS_URL='https://calendar.google.com/calendar/ical/REPLACE_ME/public/basic.ics'
python app.py
```

Atver http://localhost:8000.

## 4. Kā programma darbojas

- **google_calendar.py:** ar HTTPS nolasa publiskā Google Calendar ICS faila notikumus; apstrādā pamata atkārtošanās noteikumus (RRULE) un izņēmuma datumus (EXDATE).
- **db.py:** izveido lokālu SQLite datubāzi `planner.sqlite3`, sinhronizācijas laikā aizvieto iepriekšējos notikumus.
- **core.py:** nogriež aizņemtos intervālus izvēlētajā dienā, apvieno pārklājumus un aprēķina brīvos laikus.
- **app.py:** Flask HTTP serveris un tīmekļa interfeiss portā 8000.
- **templates/** un **static/**: lietotnes saskarne.

Laika josla: **Europe/Riga**. Sinhronizē notikumus no 90 dienām pagātnē līdz 365 dienām nākotnē. Programma saglabā datubāzi konkrētajā Codespace, nevis GitHub repozitorijā.

## 5. Zināmie ierobežojumi

- Šī versija lasa **publisku** kalendāru. Privātam kalendāram vajadzēs Google OAuth 2.0, kas Codespaces vidē prasa atsevišķu konfigurāciju.
- Atkārtotu notikumu atsevišķi pārvietotās instances (`RECURRENCE-ID`) šajā vienkāršotajā versijā netiek apstrādātas. Testēšanai izmanto parastus vai vienkārši atkārtotus notikumus.
- ICS sinhronizācija notiek pēc pogas nospiešanas, nevis reāllaikā. Google publiskā ICS plūsma var atjaunoties ar aizturi.
- Vienas dienas kalendāra laika intervāli tiek parādīti 24 stundu formātā. Dienās ar pāreju uz vasaras/ziemas laiku īpašos gadījumos jāveic papildu testēšana.
- Šis ir **studiju demonstrācijas projekts**, nevis produkcijas pakalpojums.

## 6. Testi

```bash
python -m unittest discover -s tests -v
```
