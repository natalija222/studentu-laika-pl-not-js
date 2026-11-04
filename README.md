# Studentu laika plānotājs

Python + Flask tīmekļa lietotne, kas nolasa **publisku testa Google
Calendar** (iCalendar/ICS), saglabā notikumus **SQLite** datubāzē un
aprēķina brīvos laika intervālus.

## 1. Programmas palaišana

Lai palaistu programmu Github codespace, jāizpilda šādi soļi:

**1. solis.** Github terminālī jāiestata Google Calendar ICS URL,
ievadot šādu komandu:

``` bash
export GOOGLE_CALENDAR_ICS_URL="https://calendar.google.com/calendar/ical/f18f7c51b7992e46315566c127318ec363eb534c1ff999f937c17dc2e9efbbef0%40group.calendar.google.com/public/basic.ics"
```

**2. solis.**  Github terminālī ievada šādu komandu, lai palaistu programmu:

``` bash
python app.py
```

**3. solis.** Lai atvērtu programmu pārlūkprogrammā:

1.  jāatver sadaļu **Ports**.
2.  jānospiež uz porta **8000**.
3.  jāizvēlas **Open in Browser**.

Pēc šo darbību izpildes tīmekļa lietotne būs pieejama pārlūkprogrammā.
