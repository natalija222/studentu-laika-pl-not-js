# Google Calendar pieslēgšana pārlūka versijai

Notikumu nolasīšana un brīvā laika aprēķins ir saglabāts. Mainīta tikai autorizācijas plūsma: pārlūka/Codespaces versijai izmanto Google **Web application**, nevis veco **Desktop app** OAuth klientu. Esošo Google Cloud projektu var saglabāt.

## Ja projekts jau izveidots

1. Palaid jauno plānotāju un atver to pārlūkā.
2. Atver **Savienojumi → Sākotnējā Google iestatīšana**.
3. Nokopē laukā **Authorized redirect URIs** parādīto adresi. Lokāli tā ir `http://localhost:8000/google/callback`; Codespaces tā sākas ar tavas darba vides HTTPS adresi un beidzas ar `/google/callback`.
4. Atver https://console.cloud.google.com/ un izvēlies savu esošo projektu.
5. Atver **Google Auth platform → Clients → Create client**.
6. Izvēlies **Application type: Web application**. Nosauc, piemēram, `Studentu planotajs web`.
7. Sadaļā **Authorized redirect URIs** pievieno precīzi 3. solī nokopēto adresi un saglabā. JavaScript origins šai servera plūsmai nav jāaizpilda.
8. Lejupielādē klienta JSON failu.
9. Plānotājā tajā pašā sadaļā izvēlies failu un spied **Saglabāt JSON**.
10. Spied **Pieslēgties ar Google**, izvēlies kontu un apstiprini kalendāra notikumu lasīšanu.

Pēc veiksmīgas autorizācijas pārlūks atgriežas lietotnē, tiek importēti izvēlētā perioda notikumi un pārrēķināts brīvais laiks. Pieslēgšanās jāpabeidz 10 minūtēs. Ja atļauju neapstiprini, notikumi netiek mainīti.

## Ja Google projekts vēl nav sagatavots

Google Cloud izveido projektu un sadaļā **APIs & Services → Library** ieslēdz **Google Calendar API**.

**Google Auth platform → Branding** norādi lietotnes nosaukumu un savu kontaktinformāciju. Personīgajam Gmail kontam izvēlies **External**. Sadaļā **Audience → Test users** pievieno sava kalendāra e-pastu. Testēšanai atstāj testēšanas režīmu.

**Data Access → Add or Remove Scopes** pievieno:

```text
https://www.googleapis.com/auth/calendar.events.readonly
```

Tālāk izveido Web application klientu pēc iepriekšējiem soļiem.

## Lokāli un Codespaces

Vienam Web application klientam vari reģistrēt abas atgriešanās adreses. JSON lejupielādē pēc adrešu saglabāšanas. Lokāli atver lietotni ar `http://localhost:8000`, lai pieslēgšanās atgrieztos tajā pašā pārlūka sesijā.

Codespaces portu atstāj Private. Google atgriešanās ir pārlūka pāradresācija; pārlūkā jābūt piekļuvei tam pašam GitHub Codespace. Ja sesija pazūd vai parādās GitHub pieslēgšanās, atver lietotni jaunā cilnē caur PORTS un atkārto Google pieslēgšanos.

## Kļūdas

- **Vajadzīgs Web application JSON**: izveido jauno klientu; Desktop app faila pārsaukšana neko nemaina.
- **redirect_uri_mismatch**: Google klienta reģistrētajai adresei pilnīgi jāsakrīt ar programmā redzamo, ieskaitot protokolu, portu un `/google/callback`. Lejupielādē atjaunināto JSON.
- **access_denied**: pārbaudi testētāja e-pastu un konta administratora ierobežojumus.
- **403 API kļūda**: pārbaudi Calendar API ieslēgšanu tajā pašā projektā un piešķirto notikumu lasīšanu.
- **Sesija beigusies**: atvieno un pieslēdzies atkārtoti.
- **Tukšs imports**: pārbaudi datumu, kontu un vai notikums atrodas galvenajā kalendārā un ir atzīmēts kā aizņemts.

## Saglabātā uzvedība

Tiek nolasīts galvenais kalendārs izvēlētajam periodam. Atkārtotas nodarbības izvērš datumos, visas dienas notikumi bloķē dienu, bet atceltie, noraidītie un “Free” notikumi neaizņem laiku.

Atkārtots imports aizstāj iepriekšējos lokālos Google notikumus. Manuālie, demo un mācību ieraksti paliek. Neveiksmīga API atbilde datubāzi nemaina. Pārslēdzot periodu, atkārto importu.

Google kalendārā nekas netiek ierakstīts. Piekļuves pilnvaras saglabājas tikai servera atmiņā; tās nav sīkdatnēs vai datubāzes kopijā. Pēc servera restartēšanas jāpieslēdzas vēlreiz. Atvienošana izdzēš lokālo Google importu un aizmirst sesijas pilnvaras. Lai atsauktu atļauju arī Google kontā, izmanto https://myaccount.google.com/connections .

Failā `credentials.json` saglabājas Web klienta konfigurācija. To nepublicē GitHub un nesūti kopā ar projektu. Importētie notikumi ir datubāzē; tās rezerves kopija satur to nosaukumus un laikus.

Reāla autorizācija ar tavu kontu nav pārbaudīta šajā izstrādes vidē. OAuth stāvokļa parametra (`state`), PKCE un callback maršruta darbība pārbaudīta ar automatizētiem testiem un imitētām Google atbildēm.

Oficiālā dokumentācija:
- https://developers.google.com/identity/protocols/oauth2/web-server
- https://developers.google.com/workspace/guides/configure-oauth-consent
- https://developers.google.com/workspace/calendar/api/auth
