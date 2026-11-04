# Studentu laika plānotājs

Python + Flask tīmekļa lietotne, kas nolasa **publisku testa Google
Calendar** (iCalendar/ICS), saglabā notikumus **SQLite** datubāzē un
aprēķina brīvos laika intervālus.

## 1. Programmas palaišana

Lai palaistu programmu, izpildi šādus soļus:

**1. solis.** Atver termināli un iestati Google Calendar ICS URL,
ievadot šādu komandu:

``` bash
export GOOGLE_CALENDAR_ICS_URL="https://calendar.google.com/calendar/ical/f18f7c51b7992e46315566c127318ec363eb534c1ff999f937c17dc2e9efbbef0%40group.calendar.google.com/public/basic.ics"
```

**2. solis.** Palaid programmu, terminālī ievadot komandu:

``` bash
python app.py
```

**3. solis.** Atver programmu pārlūkprogrammā:

1.  Atver sadaļu **Ports**.
2.  Atrodi portu **8000**.
3.  Nospied **Open in Browser**.

Pēc šo darbību izpildes tīmekļa lietotne būs pieejama pārlūkprogrammā.
