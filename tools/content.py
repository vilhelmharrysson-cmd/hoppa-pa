# Innehåll för turerna. Hållplatsnamn måste matcha OpenStreetMap exakt.
# reuse = befintlig ljudfil (relativt site/) när texten är oförändrad.

OLD = "old_tours.json"

TOURS = [
  {
    "id": "goteborg-11", "relation": 52448, "city": "Göteborg", "line": "11",
    "vehicle": "vagn", "vehicleLong": "spårvagn", "operator": "Västtrafik",
    "tab": "Spårvagn mot havet", "guide": "Johan", "voice": "ZXVV7HMmWnmhtavOdWNl",
    "speedKmh": 19, "dwellSec": 20,
    "from": "Drottningtorget", "to": "Saltholmen",
    "guided": {
      "Drottningtorget": {
        "story": "Välkommen ombord! Du kliver på vid Drottningtorget, mitt framför Centralstationen. Du sitter på en av spårvagnarna i Nordens största spårvägsnät. Göteborg fick hästspårvagnar 1879 och elektriska vagnar 1902, och staden valde att behålla spårvagnen när många andra svenska städer lade ner sin. Centralstationen invigdes 1858 och är en av landets äldsta stationsbyggnader som fortfarande används. Luta dig tillbaka. Vi åker längs älven, genom de gamla arbetarkvarteren och ut till havet.",
        "tips": [["Nordstan, inomhusgalleria", "2 min"], ["Lilla Bommen och Göteborgsoperan", "8 min"]]},
      "Brunnsparken": {"old": ("goteborg-11", "Brunnsparken"), "reuseStory": "audio/stop1.mp3", "reuseHop": "audio/hop1.mp3"},
      "Stenpiren": {
        "story": "Nu kör vi ner mot Göta älv och Stenpiren. Under 1800-talet och början av 1900-talet lämnade över en miljon svenskar landet för att söka ett nytt liv i Amerika, och de flesta reste via Göteborg. Många av dem gick ombord just här. I dag går färjan Älvsnabben härifrån över älven, och den ingår i samma biljett som spårvagnen. På andra sidan ser du Lindholmen och Eriksberg, där stadens stora varv en gång låg.",
        "tips": [["Färjan Älvsnabben över älven", "1 min"], ["Göteborgs stadsmuseum i Ostindiska huset", "7 min"]]},
      "Järntorget": {"old": ("goteborg-11", "Järntorget"), "reuseStory": "audio/stop4.mp3", "reuseHop": "audio/hop4.mp3"},
      "Stigbergstorget": {"old": ("goteborg-11", "Stigbergstorget"), "reuseStory": "audio/stop5.mp3", "reuseHop": "audio/hop5.mp3"},
      "Mariaplan": {"old": ("goteborg-11", "Mariaplan"), "reuseStory": "audio/stop6.mp3", "reuseHop": "audio/hop6.mp3"},
      "Kungssten": {
        "old": ("goteborg-11", "Älvsborgsplan"), "reuseStory": "audio/stop7.mp3",
        "tips": [["Klippans kulturreservat", "15 min"], ["Röda Sten konsthall under Älvsborgsbron", "20 min"]]},
      "Långedrag": {"old": ("goteborg-11", "Långedrag"), "reuseStory": "audio/stop8.mp3", "reuseHop": "audio/hop8.mp3"},
      "Saltholmen": {"old": ("goteborg-11", "Saltholmen"), "reuseStory": "audio/stop9.mp3", "reuseHop": "audio/hop9.mp3"},
    },
    "looks": [
      {"id": "feskekorka", "lat": 57.70125, "lon": 11.95706, "r": 220,
       "text": "Till vänster, vid kanalen, ligger Feskekôrka, stadens fiskhall från 1874. Den ser ut som en kyrka, och göteborgarna har kallat den fiskkyrkan sedan dess."},
      {"id": "masthuggskyrkan", "lat": 57.6976, "lon": 11.9409, "r": 260,
       "text": "Till vänster på berget ser du Masthuggskyrkan. Till höger skymtar hamnen och Göta älv.", "reuse": "audio/look5.mp3"},
      {"id": "alvsborgsbron", "lat": 57.6815, "lon": 11.9050, "r": 220,
       "text": "Till höger syns Älvsborgsbron, invigd 1966.", "reuse": "audio/look7.mp3"},
      {"id": "havet", "lat": 57.6748, "lon": 11.8842, "r": 250,
       "text": "Husen glesnar och villor tar över. Snart ser du havet.", "reuse": "audio/look8.mp3"},
    ],
  },
  {
    "id": "stockholm-54", "relation": 2354371, "city": "Stockholm", "line": "54",
    "vehicle": "buss", "vehicleLong": "buss", "operator": "SL",
    "tab": "Över Västerbron", "guide": "Tommy", "voice": "6eknYWL7D5Z4nRkDy15t",
    "speedKmh": 14, "dwellSec": 20,
    "from": "Fridhemsplan", "to": "Reimersholme",
    "guided": {
      "Fridhemsplan": {"old": ("stockholm-54", "Fridhemsplan"), "reuseStory": "audio/sthlm54/stop0.mp3", "reuseHop": "audio/sthlm54/hop0.mp3"},
      "Mariebergsgatan": {"old": ("stockholm-54", "Mariebergsgatan"), "reuseStory": "audio/sthlm54/stop1.mp3", "reuseHop": "audio/sthlm54/hop1.mp3"},
      "Högalidsgatan": {
        "story": "Nu är vi på Södermalm. Västerbron, som vi just åkte över, invigdes 1935 och är över sexhundra meter lång. Kyrkan med de två tornen här bredvid är Högalidskyrkan, invigd 1923. Den syns från långt håll och är ett landmärke för hela västra Söder.",
        "tips": [["Högalidskyrkan", "2 min"], ["Promenad tillbaka upp på Västerbron för utsikten", "8 min"]]},
      "Hornstull": {"old": ("stockholm-54", "Hornstull"), "reuseStory": "audio/sthlm54/stop3.mp3", "reuseHop": "audio/sthlm54/hop3.mp3"},
      "Bergsunds strand": {"old": ("stockholm-54", "Bergsunds strand"), "reuseStory": "audio/sthlm54/stop4.mp3", "reuseHop": "audio/sthlm54/hop4.mp3"},
      "Reimersholme": {"old": ("stockholm-54", "Reimersholme"), "reuseStory": "audio/sthlm54/stop5.mp3", "reuseHop": "audio/sthlm54/hop5.mp3"},
    },
    "looks": [
      {"id": "vasterbron", "lat": 59.3233, "lon": 18.0268, "r": 170,
       "text": "Vi kör över Västerbron. Titta åt vänster: där ligger Stadshuset, Riddarholmen och Gamla stan. Under oss, till höger, ligger Långholmen.", "reuse": "audio/sthlm54/look2.mp3"},
      {"id": "langholmen", "lat": 59.3177, "lon": 18.0280, "r": 120,
       "text": "Till höger, på andra sidan vattnet, ligger Långholmen.", "reuse": "audio/sthlm54/look4.mp3"},
    ],
  },
  {
    "id": "stockholm-66", "relation": 300241, "city": "Stockholm", "line": "66",
    "vehicle": "buss", "vehicleLong": "buss", "operator": "SL",
    "tab": "Tvärs över Söder", "guide": "Tommy", "voice": "6eknYWL7D5Z4nRkDy15t",
    "speedKmh": 13, "dwellSec": 20,
    "from": "Hornstull", "to": "Tengdahlsgatan",
    "guided": {
      "Hornstull": {"old": ("stockholm-66", "Hornstull"), "reuseStory": "audio/sthlm66/stop0.mp3", "reuseHop": "audio/sthlm66/hop0.mp3"},
      "Skinnarviken": {
        "story": "Uppe till vänster ligger Skinnarviksberget, den högsta naturliga punkten i Stockholms innerstad. Klättra upp så får du en vid utsikt över Riddarfjärden, Stadshuset och Kungsholmen. Namnet kommer från skinnarna, hantverkarna som beredde skinn och läder vid viken här förr i tiden.",
        "tips": [["Skinnarviksberget, utsikt över Riddarfjärden", "4 min, uppför"], ["Ivar Los park", "6 min"]]},
      "Södra station": {
        "story": "Vi närmar oss Södra station. Den stora halvcirkelformade byggnaden runt Fatbursparken kallas Bofills båge, efter den spanske arkitekten Ricardo Bofill. Den stod klar 1992. Där parken ligger i dag fanns förr Fatburssjön, en sjö som fylldes igen under 1800-talet när järnvägen kom.",
        "tips": [["Bofills båge och Fatbursparken", "3 min"], ["Medborgarplatsen", "8 min"]]},
      "Eriksdal": {"old": ("stockholm-66", "Eriksdal"), "reuseStory": "audio/sthlm66/stop1.mp3", "reuseHop": "audio/sthlm66/hop1.mp3"},
      "Skanstull": {"old": ("stockholm-66", "Skanstull"), "reuseStory": "audio/sthlm66/stop2.mp3", "reuseHop": "audio/sthlm66/hop2.mp3"},
      "Södermannagatan": {"old": ("stockholm-66", "Södermannagatan"), "reuseStory": "audio/sthlm66/stop3.mp3", "reuseHop": "audio/sthlm66/hop3.mp3"},
      "Klippgatan": {"old": ("stockholm-66", "Klippgatan"), "reuseStory": "audio/sthlm66/stop4.mp3", "reuseHop": "audio/sthlm66/hop4.mp3"},
      "Erstagatan": {"old": ("stockholm-66", "Erstagatan"), "reuseStory": "audio/sthlm66/stop5.mp3", "reuseHop": "audio/sthlm66/hop5.mp3"},
      "Tengdahlsgatan": {"old": ("stockholm-66", "Tengdahlsgatan"), "reuseStory": "audio/sthlm66/stop6.mp3", "reuseHop": "audio/sthlm66/hop6.mp3"},
    },
    "looks": [
      {"id": "arstaviken", "lat": 59.3080, "lon": 18.0680, "r": 160,
       "text": "Söderut glittrar Årstaviken.", "reuse": "audio/sthlm66/look1.mp3"},
      {"id": "sofiakyrka", "lat": 59.3122, "lon": 18.0858, "r": 160,
       "text": "Uppe på berget syns Sofia kyrka.", "reuse": "audio/sthlm66/look4.mp3"},
    ],
  },
]
