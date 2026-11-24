# Hoppa på

Guidad hop on hop off-tur med vanlig kollektivtrafik. Kliv på en spårvagn eller buss och få
berättelser om platserna du passerar, styrt av din position längs linjen.

**Prototyp.** Innehåller alla Göteborgs spårvagnslinjer (1–12, båda riktningar, text) med en
inläst tur på linje 11, samt SL-buss 54 och 66 i Stockholm.

## Så fungerar det

- **Positionsstyrt.** Varje linje är den verkliga linjedragningen från OpenStreetMap. Berättelsen
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
  tours.json            alla turer: linjer, hållplatser, berättelser, "titta ut"
  audio/                inlästa berättelser (ElevenLabs)
  sw.js, manifest.webmanifest, icons/
netlify/functions/
  vt.mjs                /api/vt – Västtrafik (Planera Resa v4, Störning v1), kräver nyckel
  sl.mjs                /api/sl – SL via Trafiklab (öppna API:er, ingen nyckel)
tools/                  källor och byggskript för turer och sidan
```

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

- Berättelser och "titta ut" för Göteborg: `tools/content_gbg.py` (platsbibliotek som alla linjer
  delar). Stockholm och linje 11 med röst: `tools/content.py` och `tools/build_all.py`.
- Sidans kod: `tools/head.css.html` och `tools/body.html`, sedan `python3 tools/make_index.py`.
- Byggskripten förväntar sig en arbetskatalog med `build/`, `site/` och `osm/` (OSM-relationer
  hämtas från api.openstreetmap.org).

## Data och licenser

- Linjedragning och hållplatser: © OpenStreetMaps bidragsgivare, ODbL. Kontrollerad mot
  Västtrafiks linjekarta (juni 2026).
- Realtid och störningar: Västtrafik och SL (via Trafiklab), enligt respektive villkor.
- Kontrollera linjedragning och fakta i berättelserna innan lansering.
