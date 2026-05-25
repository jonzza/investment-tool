# News Investor MVP

Hakee uutisia RSS-syötteistä, seuloo ne Claude Haikulla, analysoi tärkeimmät
Sonnetilla ja kirjoittaa päivittäisen markkinakatsauksen suomeksi.

## Asennus

1. **Kloonaa projekti omaan kansioon** (tai luo manuaalisesti).

2. **Luo virtuaaliympäristö ja asenna riippuvuudet:**

   ```bash
   cd news-investor-mvp
   python -m venv venv
   source venv/bin/activate      # macOS/Linux
   # venv\Scripts\activate       # Windows
   pip install -r requirements.txt
   ```

3. **Luo `.env`-tiedosto** (kopioi `.env.example` malliksi):

   ```bash
   cp .env.example .env
   ```

   Hae API-avain osoitteesta https://console.anthropic.com/ ja
   liitä se `.env`-tiedostoon:

   ```
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

   Aseta konsolissa myös kuukausittainen käyttökatto (Spending limits) -
   esim. 30 USD/kk - turvaverkoksi.

## Ajaminen

```bash
python main.py
```

Yhden ajon kesto on tyypillisesti 2-5 minuuttia. Lopputulos tallennetaan
`reports/YYYY-MM-DD.md`-tiedostoon ja tulostetaan myös konsoliin.

## Komponenttien testaus erikseen

Jokaista vaihetta voi ajaa erikseen kehityksen aikana:

```bash
python fetcher.py        # Hae RSS, tulosta 5 ensimmäistä
python screener.py       # Hae + seuloo 10 artikkelia
python analyzer.py       # Hae + seuloo + analysoi
```

## Konfigurointi

Säädä `config.py`-tiedostossa:
- `RSS_FEEDS` - mitä uutislähteitä käytetään
- `SIGNIFICANCE_THRESHOLD` - kuinka korkea pistemäärä vaaditaan syväanalyysiin (oletus 7)
- `MAX_ANALYSES` - maksimi syväanalyysejä per ajo (kustannuskatto, oletus 20)
- `MODEL_SCREENING` / `MODEL_ANALYSIS` - käytetyt Claude-mallit

## Kustannusarvio

Karkea arvio per ajo:
- Vaihe 1 (Haiku-seulonta ~100 uutista): ~$0.05-0.15
- Vaihe 2 (Sonnet-syväanalyysi 10-20 uutista): ~$0.20-0.50
- Vaihe 3 (Sonnet-synteesi): ~$0.05-0.15

**Yhteensä ~$0.30-0.80/ajo, eli 10-25€/kk** yhdellä päivittäisellä ajolla.

## Tunnetut rajoitukset (MVP)

- Ei tietokantaa - ei muista mitä eilen näytti, voi näyttää saman uutisen uudelleen
- Ei sähköpostia - raportti vain tiedostoon
- Käyttää vain RSS-syötteiden tarjoamaa lyhyttä ingressitekstiä, ei hae koko artikkelia
- Ei pörssikursseja eikä tulosraportteja
- Ei prompt cachingia

Nämä tulevat seuraavissa vaiheissa.

## Tietoturva

- `.env` ei mene Gitiin (`.gitignore` huolehtii)
- API-avaimet ovat henkilökohtaisia - älä jaa eteenpäin
- Aseta käyttökatto Anthropicin konsolissa
