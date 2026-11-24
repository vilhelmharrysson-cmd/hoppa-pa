# Platsbibliotek för Stockholm. Hållplatsnamn som i SL:s GTFS (matchas utan hänsyn till
# skiftläge, accenter och skiljetecken). Endast text, inga röster ännu.
#   story     berättelse som spelas på väg in mot hållplatsen
#   asFirst   alternativ text när turen börjar här
#   variants  riktningsberoende text, väljs utifrån nästa hållplats (ifNext)

LINE_NAMES = {"7": "Spårväg City", "12": "Nockebybanan", "21": "Lidingöbanan", "30": "Tvärbanan",
              "31": "Tvärbanan", "80": "Pendelbåt", "82": "Djurgårdsfärjan", "84": "Pendelbåt", "89": "Pendelbåt"}

PLACES = {
  # --- Innerstaden ---------------------------------------------------------
  "Slussen": {
    "story": "Slussen är platsen där Mälaren möter Saltsjön och där Södermalm möter Gamla stan. Här har det funnits slussar sedan 1600-talet, och just nu byggs hela området om i ett av Stockholms största byggprojekt. Från kajerna har du utsikt mot Gamla stan, Skeppsholmen och Djurgården.",
    "tips": [["Gamla stan", "5 min"], ["Fotografiska vid Stadsgårdskajen", "8 min"], ["Utsikt från Katarinahissen", "4 min"]]},
  "Slottsbacken": {
    "story": "Uppför backen ligger Kungliga slottet, som stod klart 1754 efter att det gamla slottet Tre Kronor brann 1697. Slottet har över sexhundra rum, och vaktavlösningen på yttre borggården lockar besökare varje dag.",
    "tips": [["Kungliga slottet", "2 min"], ["Gamla stans gränder", "3 min"]]},
  "Riddarhustorget": {
    "story": "Den vackra byggnaden här är Riddarhuset från 1600-talet, där adeln förr samlades. Strax intill ligger Riddarholmen med Riddarholmskyrkan, där svenska kungar begravts i flera hundra år.",
    "tips": [["Riddarholmen och utsikten över Riddarfjärden", "4 min"], ["Gamla stan", "2 min"]]},
  "Kungsträdgården": {
    "story": "Kungsträdgården var från början kungens köksträdgård. I dag är den en av stadens mest omtyckta parker, och på våren blommar körsbärsträden här i rosa och vitt.",
    "tips": [["Kungsträdgården", "1 min"], ["Kungliga Operan", "4 min"]]},
  "Nybroplan": {
    "story": "Vid Nybroplan ligger Dramaten, Kungliga Dramatiska teatern, invigd 1908. Härifrån börjar Strandvägen, med sina pampiga sekelskifteshus längs vattnet, och från Nybrokajen går båtar ut i skärgården.",
    "tips": [["Strandvägen, promenad längs vattnet", "2 min"], ["Båtar från Nybrokajen", "2 min"]]},
  "Djurgårdsbron": {
    "story": "Över bron når vi Djurgården, som i flera hundra år var kungens jaktpark. I dag är ön en del av Kungliga nationalstadsparken, med museer, nöjesfält och stora grönområden.",
    "tips": [["Promenad längs Djurgårdsbrunnsviken", "3 min"]]},
  "Nordiska museet/Vasamuseet": {
    "story": "Här ligger två av Stockholms mest besökta museer. Det slottsliknande huset är Nordiska museet. Bakom det ligger Vasamuseet, med regalskeppet Vasa som sjönk på sin jungfrufärd 1628 och bärgades 1961.",
    "tips": [["Vasamuseet", "4 min"], ["Nordiska museet", "2 min"]]},
  "Liljevalchs/Gröna Lund": {
    "story": "Gröna Lund öppnade 1883 och är Sveriges äldsta nöjespark. Om sommaren hörs skriken från berg- och dalbanorna långt ut över vattnet. Mitt emot ligger konsthallen Liljevalchs.",
    "tips": [["Gröna Lund", "2 min"], ["Liljevalchs konsthall", "1 min"]]},
  "Skansen": {
    "story": "Skansen öppnade 1891 och är världens äldsta friluftsmuseum. Här finns gamla gårdar från hela Sverige, nordiska djur och en vid utsikt över Stockholm.",
    "tips": [["Skansen", "2 min"]]},
  "Waldemarsudde": {
    "story": "Waldemarsudde var konstnären prins Eugens hem. Han var son till kung Oscar II och en av sin tids främsta landskapsmålare. I dag är hans villa och trädgård ett konstmuseum vid vattnet.",
    "tips": [["Prins Eugens Waldemarsudde", "2 min"]]},
  "Stadshuset": {
    "story": "Stadshuset invigdes 1923 och är en av Stockholms symboler. Här hålls Nobelbanketten varje december i Blå hallen, och från tornet har du en vid utsikt över Riddarfjärden och Gamla stan.",
    "tips": [["Stadshuset och tornet", "2 min"], ["Promenad längs Norr Mälarstrand", "3 min"]]},
  "Sergels torg": {
    "story": "Sergels torg är Stockholms moderna centrum, med det svartvita mönstret som kallas Plattan och glasobelisken mitt i fontänen. Kulturhuset, med bibliotek och utställningar, ligger vid torget.",
    "tips": [["Kulturhuset", "1 min"], ["Drottninggatan, shopping", "2 min"]]},
  "Hötorget": {
    "story": "Vid Hötorget ligger Konserthuset, där Nobelpriset delas ut varje år. På torget hålls marknad, och inne i Hötorgshallen finns matstånd från hela världen.",
    "tips": [["Hötorgshallen", "1 min"], ["Konserthuset", "1 min"]]},
  "Stureplan": {
    "story": "Stureplan är Östermalms livliga mötesplats. Mitt på platsen står Svampen, ett väderskydd i betong från 1930-talet som blivit en klassisk plats att stämma träff vid.",
    "tips": [["Biblioteksgatan, butiker", "2 min"], ["Humlegården och Kungliga biblioteket", "5 min"]]},
  "Östermalmstorg": {
    "story": "Här ligger Östermalms saluhall från 1888, en av Europas vackraste saluhallar. Inne i den gamla tegelbyggnaden säljs fisk, ost och delikatesser.",
    "tips": [["Östermalms saluhall", "1 min"]]},
  "Odenplan": {
    "story": "Vid Odenplan ligger Gustav Vasa kyrka. Ett kort stycke bort, på Sveavägen, ligger Stadsbiblioteket, ritat av Gunnar Asplund och känt för sin runda låneshall.",
    "tips": [["Stadsbiblioteket", "5 min"], ["Vasaparken", "4 min"]]},
  "Medborgarplatsen": {
    "story": "Medborgarplatsen är Södermalms stora torg, med uteserveringar på somrarna och skridskobana om vintern. Härifrån når du Götgatan, Söders livliga huvudgata.",
    "tips": [["Götgatan", "1 min"], ["Björns trädgård", "1 min"]]},
  "Fridhemsplan": {
    "story": "Fridhemsplan är en av Kungsholmens stora knutpunkter, med tunnelbana, bussar och butiker. Kungsholmen kallades på 1500-talet Munklägret, efter munkarna som hade mark här.",
    "tips": [["S:t Eriksgatan, kaféer och butiker", "1 min"], ["Kronobergsparken", "8 min"]]},
  "Mariebergsgatan": {
    "story": "Vi är i Marieberg på Kungsholmen. Det höga tornet i närheten är DN-skrapan, där Dagens Nyheter flyttade in på 1960-talet. Strax intill ligger Rålambshovsparken, en av stadens populäraste sommarparker.",
    "tips": [["Rålambshovsparken", "3 min"], ["Smedsuddsbadet vid Mälaren", "10 min"]],
    "variants": [{"ifNext": ["Västerbroplan"], "story": "Vi är i Marieberg. Det höga tornet i närheten är DN-skrapan, där Dagens Nyheter flyttade in på 1960-talet. Strax intill ligger Rålambshovsparken. Håll nu utkik, för om en liten stund kör vi upp på Västerbron."}]},
  "Högalidsgatan": {
    "story": "Kyrkan med de två tornen här bredvid är Högalidskyrkan, invigd 1923. Den syns från långt håll och är ett landmärke för hela västra Söder.",
    "tips": [["Högalidskyrkan", "2 min"], ["Promenad upp på Västerbron för utsikten", "6 min"]],
    "variants": [{"ifNext": ["Hornstull"], "story": "Nu är vi på Södermalm. Västerbron, som vi just åkte över, invigdes 1935 och är över sexhundra meter lång. Kyrkan med de två tornen här bredvid är Högalidskyrkan, invigd 1923."},
                 {"ifNext": ["Västerbroplan"], "story": "Kyrkan med de två tornen här bredvid är Högalidskyrkan, invigd 1923. Håll utkik nu, för strax kör vi upp på Västerbron, med en av Stockholms bästa utsikter."}]},
  "Hornstull": {
    "story": "Hornstull har fått sitt namn efter tullen som låg här vid den gamla stadsgränsen. Förr var det här ett arbetarkvarter. I dag är det en av Söders mest levande platser, med restauranger längs Hornstulls strand och utsikt över vattnet.",
    "tips": [["Hornstulls strand", "2 min"], ["Tantolunden", "8 min"]]},
  "Bergsunds strand": {
    "story": "Längs Bergsunds strand låg förr varv och verkstäder. Mitt emot ligger Långholmen. Där fanns länge Stockholms centralfängelse, som stängdes 1975. I dag är fängelset hotell och vandrarhem, och ön har en populär badplats.",
    "tips": [["Långholmen och fängelsemuseet", "8 min"], ["Långholmens badplats", "12 min"]]},
  "Reimersholme": {
    "story": "Reimersholme är en liten ö som fått sitt namn efter Anders Reimers, som ägde den på 1700-talet. Här låg länge en brännvinsfabrik, och namnet Reimersholms levde vidare på flaskorna. I dag är ön ett lugnt bostadsområde med strandpromenad runt hela ön.",
    "tips": [["Promenaden runt ön", "20 min"]]},
  "Skinnarviken": {
    "story": "Här ligger Skinnarviksberget, den högsta naturliga punkten i Stockholms innerstad. Klättra upp så får du en vid utsikt över Riddarfjärden, Stadshuset och Kungsholmen. Namnet kommer från skinnarna som beredde skinn och läder vid viken förr i tiden.",
    "tips": [["Skinnarviksberget, utsikt", "4 min, uppför"], ["Ivar Los park", "6 min"]]},
  "Södra station": {
    "story": "Den stora halvcirkelformade byggnaden runt Fatbursparken kallas Bofills båge, efter den spanske arkitekten Ricardo Bofill. Den stod klar 1992. Där parken ligger i dag fanns förr Fatburssjön, som fylldes igen under 1800-talet när järnvägen kom.",
    "tips": [["Bofills båge och Fatbursparken", "3 min"], ["Medborgarplatsen", "8 min"]]},
  "Eriksdal": {
    "story": "Vi är vid Eriksdal, på Södermalms södra kant. Nedanför ligger Årstaviken, där roddare och kajakpaddlare tränar en stor del av året. Här ligger också Eriksdalsbadet, ett av Stockholms största badhus.",
    "tips": [["Eriksdalsbadet", "4 min"], ["Promenad längs Årstaviken", "3 min"]]},
  "Skanstull": {
    "story": "Skanstull har fått sitt namn efter en skans, en liten befästning, och tullen vid stadens södra infart. Härifrån går Skanstullsbron söderut, och på andra sidan vattnet syns den stora vita kupolen vid Globenområdet.",
    "tips": [["Götgatan, butiker och kaféer", "2 min"], ["Ringen, köpcentrum", "1 min"]]},
  "Södermannagatan": {
    "story": "Vi är i SoFo, området söder om Folkungagatan. Här finns små butiker, kaféer och barer, och i mitten ligger Nytorget, en av Söders mest omtyckta parker.",
    "tips": [["Nytorget", "4 min"], ["Små butiker i SoFo", "2 min"]]},
  "Klippgatan": {
    "story": "Vi är vid Vita bergen. På toppen står Sofia kyrka, invigd 1906 och uppkallad efter drottning Sofia. Runt berget ligger små röda trähus från 1700- och 1800-talet, en påminnelse om hur Söder såg ut innan stenstaden byggdes.",
    "tips": [["Vita bergen och Sofia kyrka", "3 min, uppför"]]},
  "Erstagatan": {
    "story": "Härifrån är det nära till Fåfängan, ett litet kafé uppe på en klippa med en av Stockholms bästa utsikter över inloppet, Djurgården och Gamla stan.",
    "tips": [["Fåfängan, kafé med utsikt", "7 min, uppför"], ["Fjällgatans utsiktspunkt", "12 min"]]},
  "Tengdahlsgatan": {
    "story": "Tengdahlsgatan ligger i Sofia, den östligaste delen av Södermalm. Härifrån kan du promenera genom Vita bergen och SoFo, eller ner mot vattnet vid Hammarby sjö.",
    "tips": [["Vita bergen", "8 min"], ["Mandelparken", "2 min"]]},
  "Kaknästornet": {
    "story": "Kaknästornet invigdes 1967 och är ett av Stockholms högsta torn. Från utsiktsvåningen ser du hela staden och långt ut i skärgården.",
    "tips": [["Kaknästornets utsikt", "2 min"], ["Promenad på Gärdet", "3 min"]]},
  # --- Spårvägar -------------------------------------------------------------
  "Globen": {
    "story": "Den vita kupolen är Avicii Arena, som tidigare hette Globen. Den invigdes 1989 och är världens största sfäriska byggnad. På utsidan kan du åka i glasgondolerna SkyView upp till toppen.",
    "tips": [["SkyView, gondolen upp på kupolen", "3 min"]]},
  "Luma": {
    "story": "Vi är i Hammarby sjöstad, en stadsdel som byggts från 1990-talet på gammal industrimark. Det stora funkishuset är Lumafabriken, där det förr tillverkades glödlampor.",
    "tips": [["Promenad längs Hammarby sjö", "2 min"], ["Lumaparken", "2 min"]]},
  "Ropsten": {
    "story": "Från Ropsten går Lidingöbanan över Lidingöbron ut till Lidingö. Bron öppnade 1925 och var länge den enda landförbindelsen till ön.",
    "tips": [["Utsikt mot Lidingö", "2 min"]]},
  "Alvik": {
    "story": "Alvik är en knutpunkt där Tvärbanan och Nockebybanan möter tunnelbanan. Härifrån når du Bromma med sina villakvarter och Mälarens stränder.",
    "tips": [["Alviks strand", "6 min"]]},
  # --- Båtar -----------------------------------------------------------------
  "Skeppsholmen": {
    "story": "Skeppsholmen var länge flottans ö. I dag ligger här Moderna museet och det gamla segelfartyget af Chapman, som är vandrarhem. Från stranden har du en av de finaste vyerna mot Gamla stan.",
    "tips": [["Moderna museet", "4 min"], ["af Chapman", "2 min"]]},
  "Allmänna gränd": {
    "story": "Allmänna gränd ligger på Djurgården, mitt emellan Gröna Lund och Vasamuseet. Härifrån når du både nöjesfält, museer och Skansen på några minuters promenad.",
    "tips": [["Gröna Lund", "2 min"], ["Vasamuseet", "6 min"], ["Skansen", "6 min"]]},
}

LOOKS = [
  {"id": "slottet", "lat": 59.3268, "lon": 18.0717, "r": 260, "text": "{side} ligger Kungliga slottet."},
  {"id": "stadshuset", "lat": 59.3275, "lon": 18.0543, "r": 320, "text": "{side} syns Stadshuset med sitt torn och de tre kronorna i toppen."},
  {"id": "riddarholmskyrkan", "lat": 59.3248, "lon": 18.0644, "r": 280, "text": "{side} syns Riddarholmskyrkan med sitt spetsiga gjutjärnstorn. Där ligger många av Sveriges kungar begravda."},
  {"id": "vasamuseet", "lat": 59.3280, "lon": 18.0914, "r": 220, "text": "{side} ser du Vasamuseets tak, med masterna som visar hur högt skeppet Vasa är."},
  {"id": "gronalund", "lat": 59.3233, "lon": 18.0966, "r": 260, "text": "{side} ligger Gröna Lund, Sveriges äldsta nöjespark."},
  {"id": "globen", "lat": 59.2936, "lon": 18.0832, "r": 380, "text": "{side} reser sig Avicii Arena, den stora vita kupolen som tidigare hette Globen."},
  {"id": "kaknastornet", "lat": 59.3349, "lon": 18.1269, "r": 450, "text": "{side} syns Kaknästornet, ett av Stockholms högsta torn."},
  {"id": "vasterbron", "lat": 59.3233, "lon": 18.0268, "r": 170, "text": "Vi kör över Västerbron, med en av Stockholms bästa utsikter över Riddarfjärden, Stadshuset och Gamla stan."},
]
