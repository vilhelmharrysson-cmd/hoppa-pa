# Hoppa på

Guidad hop on hop off-tur med vanlig kollektivtrafik. Kliv på en spårvagn eller buss och få
berättelser om platserna du passerar, styrt av din position längs linjen.

**Prototyp.** Alla spårvagns-, buss- och båtlinjer i Göteborg (Västtrafik) och Stockholm (SL,
inklusive Spårväg City, Tvärbanan, Lidingöbanan och Nockebybanan), i båda riktningar. Berättelserna
är text; inlästa turer finns för spårvagn 11 i Göteborg och buss 54 och 66 i Stockholm.

## Så fungerar det

- **Positionsstyrt.** Varje linje följer den verkliga linjedragningen ur trafikbolagens tidtabellsdata. Berättelsen
  om en hållplats startar så långt innan att den är klar ungefär vid ankomst. "Titta ut" spelas när
  du är inom en radie från sevärdheten.
- **Simulera eller åk på riktigt.** "Simulera" kör en låtsasvagn längs linjen. "Min position"
  använder telefonens GPS.
- **Realtid.** Nästa avgång, trafikstörningar och "hitta hit" (resa till linjen) hämtas från
  Västtrafik och SL via appens egen server.
- **Offline.** Sidan, turdata och ljud som spelats sparas i telefonen.

## Struktur

```
public/                 webbappen (publiceras som den är)
  index.html            appen (genereras av tools/make_index.py)
  data/index.json       alla turer (linjeväljaren)
  data/tours/*.json     en fil per tur: linjeform, hållplatser, berättelser, "titta ut"
  audio/                inlästa berättelser (ElevenLabs)
  sw.js, manifest.webmanifest, icons/
netlify/functions/
  vt.mjs                /api/vt – Västtrafik (Planera Resa v4, Störning v1), kräver nyckel
  sl.mjs                /api/sl – SL via Trafiklab (öppna API:er, ingen nyckel)
tools/                  källor och byggskript för turer och sidan
```

## Linjedata (uppdateras varje natt)

`.github/workflows/data.yml` hämtar SL:s och Västtrafiks tidtabellsdata (GTFS Regional från
Trafiklab) varje natt och bygger om `public/data/` med `tools/gtfs_build.py`. Ändrade linjer och
planerade omledningar kommer då med automatiskt.

Kräver en hemlighet i GitHub: **Settings → Secrets and variables → Actions → New repository secret**
- Name: `TRAFIKLAB_KEY`
- Secret: nyckeln för **GTFS Regional Static** från ditt projekt på trafiklab.se

Kör första gången via **Actions → Uppdatera linjer → Run workflow**.

## Publicera på Netlify

1. Logga in på [netlify.com](https://www.netlify.com) med GitHub.
2. **Add new site → Import an existing project → GitHub →** välj `hoppa-pa` och den gren som ska
   publiceras. Inställningarna läses från `netlify.toml`, så inget behöver fyllas i.
3. **Site configuration → Environment variables → Add a variable:**
   - Key: `VT_AUTH_KEY`
   - Value: Västtrafiks **Autentiseringsnyckel** för applikationen (developer.vasttrafik.se →
     din applikation). Markera den som hemlig.
4. Publicera om (Deploys → Trigger deploy). Klart.

Applikationen i Västtrafiks utvecklarportal ska prenumerera på **Planera Resa v4** och
**Störning v1**.

## Ändra innehåll

- Berättelser och "titta ut": `tools/places_gbg.json` (Göteborg) och `tools/content_sthlm.py`
  (Stockholm). Varje plats används automatiskt av alla linjer som passerar den.
- Inlästa turer: `tools/voiced.json` (ljud i `public/audio/`).
- Sidans kod: `tools/head.css.html` och `tools/body.html`, sedan `python3 tools/make_index.py`.
- `tools/build*.py` och `tools/osmlib.py` är de äldre byggskripten som utgick från OpenStreetMap
  (används för de inlästa turerna).

## Data och licenser

- Linjer, hållplatser och linjeformer: Västtrafik och SL via Trafiklab (GTFS Regional).
- De inlästa turerna bygger på © OpenStreetMaps bidragsgivare, ODbL.
- Realtid och störningar: Västtrafik och SL (via Trafiklab), enligt respektive villkor.
- Kontrollera linjedragning och fakta i berättelserna innan lansering.
