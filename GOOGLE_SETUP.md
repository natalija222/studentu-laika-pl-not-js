# Google Calendar pieslēgšana

Šī versija reāli nolasa galveno Google kalendāru un saglabā aizņemtos notikumus SQLite datubāzē. Google kalendārā tā neko nepievieno un nedzēš. Mācību uzdevumi paliek lokāli. Google konta pieslēgums katrā jaunā lietotnes sesijā jāapstiprina vēlreiz; pilnvaras netiek ierakstītas diskā.

## 1. Atjauno programmu

Aizver plānotāju. Izpako jauno ZIP. Nokopē visus tajā esošās `studentu_laika_planotajs` mapes failus savā iepriekšējā projekta mapē, apstiprinot koda failu aizstāšanu. Esošo `data` mapi nedzēs un nepārvieto. ZIP neietver datubāzi un nepārraksta tavus datus.

Tavs iepriekš norādītais ceļš:
`C:\Users\liana\Downloads\studentu_laika_planotajs\studentu_laika_planotajs`

## 2. Uzstādi Google bibliotēkas

Projekta mapē atver `INSTALLET_GOOGLE.bat`. Ja to neatver, komandu logā izpildi šīs komandas pa vienai:

```bat
cd /d "C:\Users\liana\Downloads\studentu_laika_planotajs\studentu_laika_planotajs"
python -m pip install -r requirements.txt
```

Pagaidi, līdz instalēšana beidzas bez kļūdas.

## 3. Izveido Google projektu

Atver https://console.cloud.google.com/ un pieslēdzies savam Google kontam.
Augšējā projektu izvēlnē izvēlies **New project**, ieraksti `Studentu laika planotajs` un izveido projektu. Pārbaudi, ka tas ir izvēlēts.

Atver **APIs & Services → Library**, atrodi **Google Calendar API** un spied **Enable**.

## 4. Sagatavo piekļuvi savam kontam

Atver **Google Auth platform → Branding → Get started**. Ievadi lietotnes nosaukumu, savu atbalsta un kontaktpersonas e-pastu. Personīgajam Gmail kontam izvēlies **External**. Pabeidz izveidi.

Sadaļā **Audience → Test users → Add users** pievieno to savu Google e-pastu, kura kalendāru vēlies izmantot. Atstāj lietotni testēšanas režīmā.

Sadaļā **Data Access → Add or Remove Scopes** pievieno:

```text
https://www.googleapis.com/auth/calendar.events.readonly
```

Saglabā. Šī atļauja paredzēta notikumu lasīšanai; kods izmanto tikai galveno kalendāru.

## 5. Lejupielādē lietotnes failu

Atver **Google Auth platform → Clients → Create client**. Pie **Application type** izvēlies **Desktop app**, norādi nosaukumu un spied **Create**. Lejupielādē klienta JSON failu. API atslēga vai Service account fails šeit neder.

Failu atstāj savā datorā. Tas nav jāsūta čatā. Šim lokālajam prototipam nav vajadzīgs publisks serveris.

## 6. Pieslēdz plānotājā

Palaid programmu:

```bat
python "C:\Users\liana\Downloads\studentu_laika_planotajs\studentu_laika_planotajs\app.py"
```

1. Augšā izvēlies datumu un dienas/nedēļas režīmu.
2. Atver **Savienojumi**.
3. Spied **1. Izvēlēties Google JSON** un izvēlies lejupielādēto failu. Lietotne nokopēs to kā `credentials.json` projekta mapē.
4. Spied **2. Savienot / atjaunot**.
5. Pārlūkā izvēlies savu Google testētāja kontu un apstiprini notikumu lasīšanu.
6. Atgriezies lietotnē. **Kalendārs** rāda importētos notikumus ar avotu **Google Calendar**; **Brīvais laiks** tos ņem vērā.

Ja Google rāda nepārbaudītas lietotnes brīdinājumu, pārliecinies, ka nosaukums un izstrādātāja e-pasts ir tieši tava tikko izveidotā projekta dati. Turpini tikai ar savu testa lietotni, ja Google piedāvā šo iespēju. Ja piekļuvi bloķē administratora politika, to jārisina ar konta administratoru.

## Darbības robežas

- Ielādējas tikai galvenais kalendārs, nevis visi koplietotie vai studiju abonētie kalendāri.
- Katru reizi aizstāj visu iepriekšējo lokālo Google importu ar izvēlētā perioda datiem. Citu nedēļu apskatei ielādē tās datus vēlreiz. Manuālie, demo un mācību notikumi paliek.
- Neveiksmīga ielāde saglabā iepriekšējos notikumus. Pārbaudi statusu sadaļā Savienojumi; vecs imports nenozīmē aktuālu Google grafiku.
- Atkārtojošās nodarbības tiek izvērstas pa datumiem. Visas dienas aizņemtie notikumi bloķē dienu. Atceltus, noraidītus un Google kā “Free” norādītus notikumus neimportē.
- Laiki tiek konvertēti uz datora sistēmas laika joslu. Lieto pareizu Windows laika joslu; pēc tās maiņas importē atkārtoti. Vasaras/ziemas pārejas nakts ilguma aprēķins saglabā sākotnējā prototipa vietējā pulksteņa laika pieeju.
- Ja iepriekš ielādēji demo grafiku, tas joprojām aizņem laiku. Dzēs nevajadzīgos demo notikumus kalendārā.
- Google notikumus labo pašā Google Calendar un pēc tam atkārto ielādi.
- **Atvienot** aizmirst šīs sesijas piekļuvi un dzēš lokālos Google notikumus. Lai atsauktu arī kontā piešķirto atļauju, atver https://myaccount.google.com/connections .
- Daloties ar projektu, neiekļauj `credentials.json` un personisko `data` mapi. Datubāzes rezerves kopija satur arī importēto notikumu nosaukumus un laikus.

## Biežākās kļūdas

- `ModuleNotFoundError`: izpildi bibliotēku instalēšanu 2. solī ar to pašu `python` komandu.
- `403 access_denied`: pārliecinies, ka izvēlētais e-pasts ir **Audience → Test users** un konta politika atļauj lietotni.
- `redirect_uri_mismatch`: izveido **Desktop app** klientu, nevis Web application.
- API kļūda 403: pārbaudi Calendar API ieslēgšanu tajā pašā projektā un lasīšanas atļauju.
- Pieslēgšanās nepabeigta: mēģini vēlreiz un apstiprini pārlūkā trīs minūšu laikā.
- Tukšs saraksts: pārbaudi izvēlēto datumu, kontu un vai notikumi ir tieši galvenajā kalendārā un atzīmēti kā aizņemti.

## Pārbaudes un avoti

28 automatizēti testi pārbauda sākotnējo loģiku, Google notikumu pārveidi, vairākas API lapas, importa atkārtošanu, dzēšanu un datu saglabāšanu kļūdas gadījumā. Reāla Google konta autorizācija un Windows grafiskais logs izstrādes vidē nav pārbaudīti; pirmais pilnais savienojuma tests jāveic tavā datorā.

Oficiālā Google dokumentācija:
- https://developers.google.com/workspace/calendar/api/quickstart/python
- https://developers.google.com/workspace/guides/configure-oauth-consent
- https://developers.google.com/workspace/calendar/api/auth
- https://developers.google.com/workspace/calendar/api/v3/reference/events/list
