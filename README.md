# Studentu laika plānotājs ar Google Calendar

Python/Tkinter lietotne ar SQLite datubāzi. Pilns pirmkods un instrukcija ir iekļauti. Galvenās sadaļas: Kalendārs, Brīvais laiks, Mācību uzdevumi, Savienojumi.

## Sāc šeit

Google pieslēguma uzstādīšana soli pa solim ir failā **GOOGLE_SETUP.md**. Tā ietver bibliotēku instalēšanu, sava Google Cloud projekta izveidi un OAuth Desktop app JSON faila izvēli lietotnē.

Nepieciešams Python 3.10 vai jaunāks ar Tkinter. Windows vidē palaid `INSTALLET_GOOGLE.bat` vienu reizi, pēc tam `PALAIST.bat`. Alternatīvi projekta mapes terminālī:

```text
python -m pip install -r requirements.txt
python app.py
```

Bez Google bibliotēkām manuālās funkcijas turpina darboties; pieslēgšanās poga paskaidro, kas jāinstalē.

## Kas darbojas

- Google OAuth pieslēgšanās pārlūkā un galvenā kalendāra aizņemto notikumu nolasīšana izvēlētajai dienai/nedēļai.
- Notikumu saglabāšana SQLite, manuāla pievienošana un dzēšana, demo nedēļas ielāde, CSV eksports.
- Brīvo intervālu aprēķins, apvienojot pārklājošos notikumus un filtrējot pēc ilguma.
- Mācību uzdevumi ar ilgumu, termiņu un pabeigšanas statusu; uzdevuma ieplānošana brīvajā intervālā.
- Datubāzes rezerves kopija.

Google imports ir vienvirziena. Mācību plānus Google kalendārā neieraksta. Imports aizstāj iepriekšējā perioda Google kopiju; pārslēdzot periodu, ielādē datus vēlreiz. Manuālie un demo ieraksti paliek. Sesijas piekļuve glabājas tikai atmiņā, tāpēc pēc lietotnes aizvēršanas jāpieslēdzas vēlreiz.

E-studiju savienojums, SMS/e-pasta paziņojumi, vairāku lietotāju autorizācija, mobilā saskarne un kalendāra grafiskais režģis vēl nav īstenoti. Notikumu labošana lokāli notiek ar dzēšanu un pievienošanu; Google notikumus maina Google Calendar un importē no jauna.

## Dati un faili

Dati automātiski saglabājas `data/planner.db` blakus kodam. Atjauninot programmu, šo mapi saglabā. Izplatītajā ZIP personisku datu un Google konfigurācijas nav.

| Fails | Saturs |
|---|---|
| app.py | Pilna grafiskā saskarne, fona ielāde un CSV eksports |
| core.py | SQLite datubāze un intervālu algoritms |
| google_calendar.py | OAuth un Google API notikumu nolasīšana |
| test_core.py | 20 sākotnējie algoritma un datubāzes testi |
| test_google.py | 8 Google datu apstrādes/importa testi |
| requirements.txt | Google savienojuma bibliotēkas |
| PALAIST.bat | Windows palaišana ar python |
| INSTALLET_GOOGLE.bat | Google bibliotēku uzstādīšana |
| GOOGLE_SETUP.md | Pieslēgšanas instrukcija un kļūdu skaidrojumi |

## Īsa demonstrācija

1. Izvēlies nākotnes datumu un ielādē savu Google kalendāru vai demo nedēļu.
2. Pievieno mācību uzdevumu ar 60 minūšu ilgumu un nākotnes termiņu.
3. Sadaļā Brīvais laiks atrodi vismaz 60 minūšu intervālu.
4. Izvēlies uzdevumu un intervālu, tad spied Ieplānot izvēlētajā laikā.
5. Kalendārā pārbaudi jauno ierakstu; brīvā laika sarakstā šis laiks vairs nav pieejams.
6. Pēc aizvēršanas un atkārtotas atvēršanas izvēlies to pašu datumu: ieraksti ir saglabāti.

## Pārbaudes

```text
python -m unittest -v
```

28 automatizētie testi ir izturēti. Tie pārbauda intervālus, noturīgu glabāšanu, konfliktus, termiņus, laika joslu pārveidi, API lapošanu un importa aizstāšanu. Reāla lietotāja OAuth pieslēgšanās un Windows grafiskais logs šajā izstrādes vidē nav pārbaudīti.

Algoritms izmanto vietējā pulksteņa laiku; detalizēti laika joslas un pārējo ierobežojumu skaidrojumi ir GOOGLE_SETUP.md. Sistēma paredzēta lokālam viena lietotāja kursa prototipam.
