# Studentu laika plānotājs tīmeklī

Python + Flask + SQLite lietotne ar HTML/CSS saskarni. Visa programma atveras pārlūkā. Tkinter, noVNC un virtuālā darbvirsma nav nepieciešami.

Saglabāts iepriekšējais `core.py` bez izmaiņām: tās pašas datubāzes tabulas, brīvā laika algoritms, notikumi, mācību uzdevumi, ieplānošana un demo dati. Iepriekšējo `data/planner.db` var izmantot arī šajā versijā.

## Palaišana Windows

1. Aizver iepriekšējo plānotāju. Izpako ZIP. Lai saglabātu datus, nokopē jaunās versijas failus iepriekšējā projekta mapē, saglabājot esošo `data` mapi. Jānokopē arī `templates` un `static` mapes.
2. Palaid `INSTALLET.bat` vienu reizi, lai uzstādītu bibliotēkas. Python 3.10 vai jaunāks nepieciešams tāpat kā iepriekš.
3. Palaid `PALAIST.bat`.
4. Pārlūkā atver **http://localhost:8000**. Melno servera logu atstāj atvērtu. Apturēt var ar Ctrl+C.

Alternatīvi projekta mapē:

```text
python -m pip install -r requirements.txt
python app.py
```

Iepriekš izmantotajam ceļam CMD komandas ir:

```bat
cd /d "C:\Users\liana\Downloads\studentu_laika_planotajs2\studentu_laika_planotajs"
python -m pip install -r requirements.txt
python app.py
```

Ja izpako citā mapē, pirmajā komandā izmanto jauno mapes ceļu.

## GitHub Codespaces

Pilni soļi failā **GITHUB_PALAISANA.md**. Īsumā: projekta saturu ievieto repozitorija saknē, atver Codespaces, sagaidi uzstādīšanu un izvēlies **PORTS → 8000 → Open in Browser**. Portam jāpaliek **Private**. Ja vide jau ir atvērta ar veco konfigurāciju, izmanto **Rebuild Container**. Šī versija neizmanto portu 6080.

GitHub Pages nevar darbināt šo Python/SQLite serveri. Codespaces saskarne ir pieejama, kamēr Codespace un serveris darbojas.

## Funkcijas

| Sadaļa | Funkcionalitāte |
|---|---|
| Kalendārs | Dienas/nedēļas saraksts; manuāla pievienošana un dzēšana; demo nedēļa; CSV eksports |
| Brīvais laiks | Dienas robežas; minimālais ilgums; brīvie intervāli; uzdevuma ievietošana intervāla sākumā |
| Mācību uzdevumi | Nosaukums, ilgums, termiņš, pabeigšana/atjaunošana un dzēšana |
| Savienojumi | Google Calendar lasīšana un atjaunošana; atvienošana; SQLite kopijas lejupielāde |

Notikumi un uzdevumi glabājas SQLite `events` un `tasks` tabulās. Notikumu pārklāšanās tiek ņemta vērā brīvā laika aprēķinā. Pabeigšana neatbrīvo ieplānoto laiku; to atbrīvo attiecīgā notikuma dzēšana, tāpat kā iepriekš. Atsevišķa ierakstu rediģēšana nav pievienota: kļūdainu lokālu ierakstu var dzēst un izveidot atkārtoti.

E-studijas un SMS/e-pasta paziņojumi paliek tikai aprakstītas, vēl neīstenotas iespējas. Netiek pievienoti vairāku lietotāju konti vai automātiska divvirzienu sinhronizācija.

## Google Calendar

Tā pati funkcionalitāte: izvēlētās dienas/nedēļas aizņemto notikumu imports no galvenā kalendāra, noturīga saglabāšana SQLite un brīvo intervālu pārrēķins. Manuālie/demo/mācību notikumi netiek pārrakstīti. Google notikumu imports aizstāj visu iepriekšējo Google kopiju; pārslēdzot periodu, atjauno importu vēlreiz. Neveiksmīgs imports iepriekšējos datus saglabā.

**Mainījies OAuth klienta veids.** Pārlūka versijai vajadzīgs **Web application** JSON un precīza atgriešanās adrese. Iepriekšējais Desktop app fails vairs neder. Programmas sadaļa **Savienojumi** parāda šo adresi un ļauj augšupielādēt jauno JSON. Detalizēti soļi ir **GOOGLE_SETUP.md**.

Pilnvaras glabājas tikai servera atmiņā, nevis pārlūka sīkdatnē vai datubāzē. Pēc servera restartēšanas jāpieslēdzas no jauna. Pieslēgšanās pieprasījums ir derīgs 10 minūtes; neaktīvas sesijas no atmiņas izņem pēc 12 stundām. Google pieslēgšanās notiek parastā pārlūkā, nevis attālinātā Firefox logā.

## Dati un ierobežojumi

`data/planner.db` ir saderīgs ar iepriekšējām versijām. Atjaunošanai: aizver programmu/serveri, saglabā pašreizējās datubāzes kopiju un ievieto atjaunojamo failu ar nosaukumu `planner.db` mapē `data`.

Codespace ir atsevišķs dators: esošo Windows datubāzi tajā var augšupielādēt tikai aizvērtai lietotnei. GitHub repozitorijā `data` un Google JSON nepublicē. Eksporti tagad lejupielādējas uz pārlūka lietotāja datoru. Pirms Codespace dzēšanas lejupielādē datubāzes kopiju.

Šis ir viena lietotāja prototips ar vienu datubāzi. Visi, kam būtu piekļuve serverim, redzētu tās pašas tabulas. Lokāli serveris klausās tikai `127.0.0.1`; Codespaces izmanto GitHub privātā porta piekļuvi. Publiskai vairāku lietotāju izvietošanai nepieciešama atsevišķa autorizācija un datu nodalīšana.

Codespaces/Linux vidē tiek izmantota `Europe/Riga` laika josla; Windows — sistēmas laika josla. Saglabāta iepriekšējā vietējā pulksteņa laika pieeja intervāliem, arī vasaras/ziemas laika pāreju naktīs. Google ārpus galvenā kalendāra esošie koplietotie kalendāri netiek ielādēti.

## Failu atrašanās vietas

- `app.py` — tīmekļa maršruti, formas, CSV un datubāzes lejupielāde, OAuth plūsmas vadība.
- `core.py` — nemainīta SQLite un plānošanas loģika.
- `google_calendar.py` — notikumu pārveide un API; Web OAuth palīgfunkcijas.
- `templates/index.html`, `templates/error.html` — pilni lapu šabloni.
- `static/style.css`, `static/app.js` — dizains un darbību apstiprinājumi.
- `.devcontainer/devcontainer.json`, `scripts/` — Codespaces konfigurācija un palaišana.
- `requirements.txt` — nepieciešamās bibliotēkas.
- `test_core.py`, `test_google.py`, `test_web.py` — automatizētie testi.

Visi pirmkoda faili ir iekļauti pilnībā.

## Pārbaude

Projekta mapē:

```text
python -m unittest discover -v
```

Testi pārbauda sākotnējo loģiku, Google importa datu apstrādi, tīmekļa formas, saglabāšanu, eksportu, plānošanu, CSRF, ievades attēlošanu un OAuth state/PKCE. Reālā Google konta autorizācija un pilna GitHub Codespaces konteinera izveide šeit nav pārbaudīta; tie ir jāpārbauda ar tavu Google projektu un Codespace.
