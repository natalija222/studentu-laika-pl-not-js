# GitHub Codespaces palaišana bez Tkinter

## Faili

Izpako ZIP un GitHub repozitorija saknē ievieto mapes `studentu_laika_planotajs` saturu. Saknē jābūt `app.py`, `requirements.txt`, `templates`, `static`, `scripts` un `.devcontainer`.

Ja atjaunini esošu repozitoriju, aizstāj piegādātos koda failus un mapes. Esošā `data` mape jāsaglabā tikai darba vidē. Vecais `.devcontainer/Dockerfile` vairs netiek izmantots; vari to izdzēst. Jaunā konfigurācija izmanto Python konteineru bez grafiskās darbvirsmas.

GitHub **Add file → Upload files** var izmantot koda pievienošanai. Pārbaudi, ka `.devcontainer/devcontainer.json` ir nonācis saknē. Ja tas trūkst, izveido to ar **Add file → Create new file** un kopē pilnu saturu no ZIP.

Neaugšupielādē GitHub repozitorijā `credentials.json`, `client_secret*.json`, `data/` vai `.venv/`. `.gitignore` nepasargā no manuālas failu augšupielādes mājaslapā.

## Palaišana

1. Repo lapā nospied **Code → Codespaces → Create codespace**.
2. Sagaidi konteinera izveidi un bibliotēku uzstādīšanu.
3. Serveris startēs automātiski. Apakšā atver **PORTS**.
4. Pie **8000 — Studentu laika plānotājs** nospied **Open in Browser**.
5. Atvērsies pati lietotne. noVNC paroles vai virtuālās darbvirsmas nav.

Portam jāpaliek **Private**: tas ļauj piekļūt caur tavu GitHub kontu.

## Ja Codespace jau bija atvērts

Pēc failu atjaunošanas nospied **Ctrl+Shift+P → Codespaces: Rebuild Container** (vai **Dev Containers: Rebuild Container**). Sagaidi pārbūvi. Vecā vide ar portu 6080 vairs nav vajadzīga.

Ja serveris nav palaists vai tu to apturēji, terminālī projekta saknē izpildi:

```bash
bash scripts/start_codespaces.sh
```

Ja nepieciešama manuāla uzstādīšana:

```bash
bash scripts/setup_codespaces.sh
bash scripts/start_codespaces.sh
```

Alternatīva bez palaišanas skriptiem:

```bash
python -m pip install -r requirements.txt
python app.py
```

Izvēlies vienu palaišanas veidu — nedarbini divus serverus uz tā paša 8000 porta. Ja parādās `Address already in use`, serveris, iespējams, jau darbojas: vispirms atver 8000 portu. Automātiskā starta žurnāls ir `data/codespaces.log`.

## Google pieslēgums

Tīmekļa versijai vajadzīgs Google **Web application** klients. Programmā atver **Savienojumi → Sākotnējā Google iestatīšana**. Tur norādīta tieši tava Codespace atgriešanās adrese. Kopē to Google klienta **Authorized redirect URIs**, lejupielādē Web application JSON un augšupielādē lietotnes formā. Tad spied **Pieslēgties ar Google**. Sīkāk: GOOGLE_SETUP.md.

Jaunā Codespace adrese var mainīties. Tad jauno atgriešanās adresi pievieno Google klientam un lejupielādē JSON vēlreiz. Ja izmanto savas vides domēnu, pirms startēšanas iestati `PLANNER_PUBLIC_URL` uz HTTPS sākumadresi bez ceļa; standarta Codespaces gadījumā adrese tiek noteikta automātiski.

## Dati

Saglabāšana joprojām notiek `data/planner.db`. Lai pārnestu Windows datus, apturi serveri un augšupielādē datubāzi šajā mapē. Esošos datus vispirms dublē. Datora un Codespaces datubāzes automātiski nesinhronizējas.

Lejupielādes (CSV un datubāzes kopija) notiek tieši pārlūkā. Pirms Codespace dzēšanas lejupielādē kopiju. Ja izveido pilnīgi jaunu Codespace, tajā būs atsevišķa datubāze.

Šī nav GitHub Pages statiska lapa. Python serverim jādarbojas Codespace vidē. Codespaces pieejamība un lietošanas limiti ir atkarīgi no tava GitHub konta.
