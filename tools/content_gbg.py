# Göteborgs spårvagnslinjer: linjer (OSM-relation, riktning enligt Västtrafiks linjeförteckning
# juni 2026) och ett gemensamt platsbibliotek. Endast text, inga röster ännu.

LINES = [
  # ref, OSM-relation, flik-text
  ("1", 5455642, "Tvärs genom stan"),
  ("2", 53646, "Över älven till Biskopsgården"),
  ("3", 2413521, "Majorna och Vasastan"),
  ("4", 2413520, "Från Mölndal till Angered"),
  ("5", 2184933, "Hisingen, Korsvägen och Liseberg"),
  ("6", 2213139, "Hela stan på en vagn"),
  ("7", 2247615, "Från Tynnered till rymdgatorna"),
  ("8", 2413330, "Chalmers, Ullevi och Angered"),
  ("9", 2418222, "Majorna, Haga och Angered"),
  ("10", 2413329, "Från Guldheden till Lindholmen"),
  ("12", 19977485, "Mölndal, Liseberg och Lindholmen"),
]

# Platsbibliotek: berättelse + tips per hållplats (namn exakt som i OSM).
PLACES = {
  "Drottningtorget": {
    "story": "Drottningtorget ligger mitt framför Centralstationen, som invigdes 1858 och är en av landets äldsta stationsbyggnader som fortfarande används. Härifrån utgår stora delar av Nordens största spårvägsnät. Göteborg fick hästspårvagnar 1879 och elektriska vagnar 1902, och staden valde att behålla spårvagnen när många andra svenska städer lade ner sin.",
    "tips": [["Nordstan, inomhusgalleria", "2 min"], ["Lilla Bommen och Göteborgsoperan", "8 min"]]},
  "Brunnsparken": {"old": "Brunnsparken"},
  "Domkyrkan": {"old": "Domkyrkan"},
  "Grönsakstorget": {"old": "Grönsakstorget"},
  "Stenpiren": {"new11": "Stenpiren"},
  "Järntorget": {"old": "Järntorget"},
  "Stigbergstorget": {"old": "Stigbergstorget"},
  "Mariaplan": {"old": "Mariaplan"},
  "Långedrag": {"old": "Långedrag"},
  "Kungssten": {
    "story": "Kungssten ligger nära Göta älvs mynning. Härifrån ser du Älvsborgsbron, som var Sveriges längsta hängbro när den invigdes 1966. Ute i älvmynningen ligger Nya Älvsborgs fästning från 1600-talet, som skyddade staden mot danskarna. Vid vattnet nedanför ligger Klippan, med gamla sjömanshus och resterna av den äldre Älvsborgs fästning.",
    "tips": [["Klippans kulturreservat", "15 min"], ["Röda Sten konsthall under Älvsborgsbron", "20 min"]]},
  "Lilla Bommen": {
    "story": "Vid Lilla Bommen möter staden älven. Den röd-vita skyskrapan kallas Läppstiftet. Den stod klar 1989 och har en utsiktsvåning högst upp. Bredvid ligger Göteborgsoperan, invigd 1994, och vid kajen ligger segelfartyget Barken Viking från 1906.",
    "tips": [["Göteborgsoperan", "3 min"], ["Barken Viking vid kajen", "4 min"]]},
  "Kungsportsplatsen": {
    "story": "Statyn mitt på platsen föreställer Karl IX till häst, men göteborgarna kallar den Kopparmärra. Den restes 1904. Här börjar Kungsportsavenyn, och vid vallgraven intill går de platta sightseeingbåtarna Paddan, som får ducka under stadens låga broar. Ett kort stycke bort ligger Stora Saluhallen från 1889.",
    "tips": [["Stora Saluhallen vid Kungstorget", "3 min"], ["Paddan, båttur på kanalerna", "2 min"]]},
  "Valand": {
    "story": "Vi är på Kungsportsavenyn, som göteborgarna bara kallar Avenyn. Den är stadens paradgata och sträcker sig upp till Götaplatsen, där Carl Milles staty Poseidon har stått sedan 1931. Längs vägen finns restauranger, uteserveringar och teatrar.",
    "tips": [["Promenad upp längs Avenyn", "2 min"], ["Götaplatsen och Poseidon", "8 min"]]},
  "Berzeliigatan": {
    "story": "Härifrån är det nära till Götaplatsen, stadens kulturtorg. Där ligger Göteborgs konstmuseum, som öppnade 1923, och runt torget finns även Stadsteatern och Konserthuset. Mitt på platsen står Poseidon, Carl Milles kraftfulla havsgud.",
    "tips": [["Göteborgs konstmuseum", "4 min"], ["Götaplatsen och Poseidon", "4 min"]]},
  "Korsvägen": {
    "story": "Korsvägen är porten till Göteborgs evenemangsstråk. Här ligger nöjesparken Liseberg, som öppnade 1923, vetenskapscentret Universeum och Världskulturmuseet. Svenska Mässan ligger också alldeles intill.",
    "tips": [["Liseberg", "4 min"], ["Universeum", "3 min"], ["Världskulturmuseet", "3 min"]]},
  "Liseberg Station": {
    "story": "Vi är vid Lisebergs norra sida. Nöjesparken öppnade 1923 i samband med stadens jubileumsutställning och är i dag en av Nordens mest besökta. Vid jul förvandlas den till en julmarknad med miljontals ljus.",
    "tips": [["Liseberg", "3 min"]]},
  "Liseberg Södra": {
    "story": "Nu passerar vi Lisebergs södra sida. Här får du ofta en skymt av berg- och dalbanorna. Lisebergshöjden bakom parken var en gång en del av Lisebergs gård, ett landställe som gav parken dess namn.",
    "tips": [["Lisebergs södra entré", "3 min"]]},
  "Scandinavium": {
    "story": "Den stora arenan här är Scandinavium, invigd 1971. Här har det spelats ishockey, hållits konserter och arrangerats världsmästerskap. Strax intill ligger Nya Ullevi.",
    "tips": [["Scandinavium", "2 min"], ["Nya Ullevi", "5 min"]]},
  "Ullevi Södra": {
    "story": "Nya Ullevi byggdes till fotbolls-VM 1958 och är fortfarande en av Sveriges största arenor. Den är också känd för konserterna. När Bruce Springsteen spelade här 1985 gungade läktarna så kraftigt att arenan senare fick förstärkas.",
    "tips": [["Nya Ullevi", "2 min"], ["Heden, stort öppet fält", "4 min"]]},
  "Chalmers": {
    "story": "Chalmers tekniska högskola grundades 1829 med pengar som William Chalmers testamenterade. Han hade arbetat för Svenska Ostindiska Kompaniet. Runt omkring ligger campus Johanneberg, där tusentals ingenjörer utbildas varje år.",
    "tips": [["Chalmers campus Johanneberg", "2 min"], ["Utsikt från Chalmersområdet", "6 min"]]},
  "Sahlgrenska Huvudentré": {
    "story": "Här ligger Sahlgrenska universitetssjukhuset, ett av Nordeuropas största sjukhus. Det har fått sitt namn efter Niclas Sahlgren, ännu en av de rika direktörerna i Ostindiska Kompaniet, vars pengar lade grunden till sjukhuset.",
    "tips": [["Botaniska trädgården", "8 min"]]},
  "Botaniska Trädgården": {
    "story": "Göteborgs botaniska trädgård öppnade 1923 och är en av Europas större botaniska trädgårdar. Här finns en klippträdgård, en japansk dal och växthus med tusentals växter. På andra sidan vägen ligger Slottsskogen, stadens stora stadspark.",
    "tips": [["Botaniska trädgården", "2 min"], ["Slottsskogen", "3 min"]]},
  "Linnéplatsen": {
    "story": "Vid Linnéplatsen börjar Slottsskogen, stadens stora park från 1874. Där finns djur, dammar och Naturhistoriska museet, som har en uppstoppad blåval från 1865. Åt andra hållet går Linnégatan, en av stadens mest omtyckta restauranggator.",
    "tips": [["Slottsskogen", "2 min"], ["Naturhistoriska museet och blåvalen", "10 min"], ["Linnégatan, restauranger", "2 min"]]},
  "Hagakyrkan": {
    "story": "Hagakyrkan invigdes 1859 och ligger vid Haga, en av Göteborgs äldsta stadsdelar. Längs Haga Nygata finns små butiker och kaféer. Här säljs de berömda jättekanelbullarna, stora som en assiett.",
    "tips": [["Haga Nygata och jättekanelbullar", "3 min"], ["Skansen Kronan, utsikt över staden", "10 min, uppför"]]},
  "Vasaplatsen": {
    "story": "Vi är i Vasastaden, med pampiga stenhus från slutet av 1800-talet. Här ligger också flera av Göteborgs universitets byggnader. Vasaparken, med universitetets huvudbyggnad, ligger alldeles intill.",
    "tips": [["Vasaparken", "2 min"], ["Röhsska museet för design och konsthantverk", "6 min"]]},
  "Handelshögskolan": {
    "story": "Den stora byggnaden här är Handelshögskolan vid Göteborgs universitet. Kvarteren runt omkring är Vasastaden, en av stadens mest välbevarade sekelskiftesmiljöer.",
    "tips": [["Vasastadens kaféer", "3 min"]]},
  "Nils Ericsonsplatsen": {
    "story": "Nils Ericsonsplatsen är uppkallad efter Nils Ericson, som byggde Sveriges första stambanor. Han var bror till uppfinnaren John Ericsson. Under oss byggs Västlänken, en järnvägstunnel under centrala Göteborg.",
    "tips": [["Nordstan, inomhusgalleria", "3 min"]]},
  "Frihamnen": {
    "story": "Vi har just korsat Göta älv på Hisingsbron, en lyftbro som öppnade 2021 och ersatte den gamla Götaälvbron. Frihamnen var förr en hamn där varor kunde lagras utan tull. Nu växer här en ny stadsdel fram.",
    "tips": [["Jubileumsparken med bastu och bad", "6 min"]]},
  "Jubileumsparken": {
    "story": "Jubileumsparken anlades till Göteborgs 400-årsjubileum. Här finns en offentlig bastu och ett bad i älven, och parken används för att pröva idéer inför den nya stadsdelen som ska byggas runt Frihamnen.",
    "tips": [["Bastun i Jubileumsparken", "2 min"]]},
  "Lindholmen": {
    "story": "Lindholmen var länge ett av Göteborgs stora varv. Där fartyg byggdes förr ligger i dag Lindholmen Science Park och en del av Chalmers. Från kajen ser du rakt över älven mot centrum.",
    "tips": [["Promenad längs kajen", "3 min"], ["Färja tillbaka över älven", "6 min"]]},
  "Hjalmar Brantingsplatsen": {
    "story": "Hjalmar Brantingsplatsen är Hisingens stora knutpunkt. Hisingen är Sveriges fjärde största ö, och här byggdes en gång både fartyg och bilar. Volvo grundades i Göteborg 1927, och huvudkontoret ligger fortfarande på Hisingen.",
    "tips": [["Backaplan, handel", "8 min"]]},
  "Rambergsvallen": {
    "story": "Ovanför oss reser sig Ramberget med Keillers park. Från toppen har du en av de bästa utsikterna över Göteborg och älven. Det är en brant men kort promenad upp.",
    "tips": [["Keillers park och utsikten från Ramberget", "10 min, uppför"]]},
  "Vårväderstorget": {
    "story": "Vi är i Biskopsgården. Lägg märke till gatunamnen: Vårväderstorget, Mildvädersgatan, Önskevädersgatan och Friskväderstorget. Här har gatorna fått namn efter olika sorters väder.",
    "tips": [["Vårväderstorget, lokala butiker", "1 min"]]},
  "Gamlestads Torg": {
    "story": "Gamlestaden är just det, den gamla staden. Här grundades Nya Lödöse 1473, långt innan dagens Göteborg anlades 1621. Senare blev området industri, och här växte kullagerföretaget SKF fram.",
    "tips": [["Gamlestadens fabriker, mat och design", "4 min"]]},
  "SKF": {
    "story": "Hållplatsen har fått namn efter SKF, som grundades i Göteborg 1907 och blev världens ledande tillverkare av kullager. Fabriksområdet här i Gamlestaden har varit företagets hem i över hundra år.",
    "tips": [["Gamlestaden", "5 min"]]},
  "Kortedala Torg": {
    "story": "Kortedala byggdes på 1950-talet som en modern förort med allt nära till hands: bostäder, torg, skolor och grönområden. Här finns fortfarande mycket av den tidens arkitektur kvar.",
    "tips": [["Kortedala torg", "1 min"]]},
  "Rymdtorget": {
    "story": "Välkommen till Bergsjön. Titta på gatunamnen här: Rymdtorget, Galileis gata, Teleskopgatan och Komettorget. Stadsdelen byggdes på 1960-talet, när rymdåldern var som mest spännande.",
    "tips": [["Bergsjöns natur och promenadstigar", "5 min"]]},
  "Angered Centrum": {
    "story": "Angered byggdes på 1970-talet och är i dag en av Göteborgs mest internationella stadsdelar. Här ligger kulturhuset Blå Stället, och runt omkring finns stora naturområden med sjöar och skog.",
    "tips": [["Kulturhuset Blå Stället", "2 min"]]},
  "Hammarkullen": {
    "story": "Hammarkullen är känt för sin karneval, som varje år fyller stadsdelen med musik, dans och färgglada kostymer. Hållplatsen ligger djupt inne i berget och nås med en lång rulltrappa.",
    "tips": [["Hammarkullens torg", "3 min"]]},
  "Svingeln": {
    "story": "Uppe på berget i närheten ligger Skansen Lejonet, en försvarsborg från 1600-talet med ett förgyllt lejon på toppen. Den byggdes för att skydda staden från angrepp österifrån.",
    "tips": [["Skansen Lejonet", "8 min"]]},
  "Östra Sjukhuset": {
    "story": "Ändhållplatsen ligger vid Östra sjukhuset. Härifrån är det nära till Delsjöområdet, ett stort naturreservat med sjöar, skog och bad, där många göteborgare tillbringar helgerna.",
    "tips": [["Delsjöområdet", "20 min"]]},
  "Virginsgatan": {
    "story": "Vi närmar oss Kålltorp, ett lugnt villa- och bostadsområde i östra Göteborg. Härifrån är det inte långt till Delsjöområdet, ett stort naturreservat med sjöar och skog.",
    "tips": [["Kålltorpssjön", "6 min"], ["Delsjöområdet", "15 min"]]},
  "Mölndals Innerstad": {
    "story": "Välkommen till Mölndal. Längs forsen i Mölndals kvarnby har vattenkraften drivit kvarnar och fabriker i flera hundra år. I dag är kvarnbyn ett kulturmiljöområde med museum och kaféer.",
    "tips": [["Mölndals kvarnby", "8 min"]]},
  "Krokslätts Fabriker": {
    "story": "Krokslätts fabriker är gamla industribyggnader där det en gång tillverkades textilier. I dag huserar här företag, restauranger och bostäder, ett exempel på hur gamla fabriker får nytt liv.",
    "tips": [["Krokslätts fabriker", "2 min"]]},
  "Frölunda Torg": {
    "story": "Frölunda Torg öppnade 1966 och var ett av Sveriges första stora köpcentrum i förort. Runt omkring ligger Västra Frölunda, och några kilometer västerut börjar havet och skärgården.",
    "tips": [["Frölunda Torg, köpcentrum", "2 min"]]},
  "Musikvägen": {
    "story": "Här i Västra Frölunda har gatorna musikaliska namn, som Musikvägen och Positivgatan. Stadsdelen byggdes under 1960-talet, när Göteborg växte snabbt söderut.",
    "tips": [["Ruddalens idrottsområde", "8 min"]]},
  "Opaltorget": {
    "story": "Vi är i Tynnered, där gatorna har fått namn efter ädelstenar: Opaltorget, Smaragdgatan och Briljantgatan. Härifrån är det nära till naturreservat och havsbad i Västra Frölunda.",
    "tips": [["Opaltorget", "1 min"]]},
  "Chapmans Torg": {
    "story": "Chapmans torg är uppkallat efter Fredrik Henrik af Chapman, som föddes i Göteborg 1721 och blev en av sin tids främsta skeppsbyggare. Här i Majorna bodde förr många som arbetade på varven och i hamnen.",
    "tips": [["Majornas kaféer och vintagebutiker", "2 min"]]},
  "Ostindiegatan": {
    "story": "Gatunamnet påminner om Svenska Ostindiska Kompaniet, som hade sitt säte i Göteborg mellan 1731 och 1813. Kompaniets skepp seglade till Kina och kom hem lastade med te, porslin och siden.",
    "tips": [["Majorna", "3 min"]]},
  "Masthuggstorget": {
    "story": "Masthuggstorget ligger nedanför Masthuggsberget. Uppe på berget ligger Masthuggskyrkan från 1914, och runt torget finns några av stadens äldsta landshövdingehus.",
    "tips": [["Masthuggskyrkan, utsikt", "8 min, uppför"]]},
}

# "Titta ut": sevärdhetens position. {side} ersätts med "Till vänster"/"Till höger"/"Rakt fram"
# utifrån linjens färdriktning där den passerar.
LOOKS = [
  {"id": "feskekorka", "lat": 57.70125, "lon": 11.95706, "r": 220,
   "text": "{side}, vid kanalen, ligger Feskekôrka, stadens fiskhall från 1874. Den ser ut som en kyrka, och göteborgarna kallar den fiskkyrkan."},
  {"id": "masthuggskyrkan", "lat": 57.6976, "lon": 11.9409, "r": 260,
   "text": "{side}, uppe på berget, ser du Masthuggskyrkan från 1914."},
  {"id": "skansenkronan", "lat": 57.6966, "lon": 11.9504, "r": 300,
   "text": "{side}, uppe på berget, syns Skansen Kronan, en försvarsborg från 1600-talet."},
  {"id": "skansenlejonet", "lat": 57.7158, "lon": 11.9887, "r": 320,
   "text": "{side} ligger Skansen Lejonet, en försvarsborg från 1600-talet med ett förgyllt lejon på toppen."},
  {"id": "lappstiftet", "lat": 57.7117, "lon": 11.9677, "r": 260,
   "text": "{side} ser du den röd-vita skyskrapan som göteborgarna kallar Läppstiftet."},
  {"id": "ullevi", "lat": 57.7062, "lon": 11.9870, "r": 260,
   "text": "{side} reser sig Nya Ullevi, arenan som byggdes till fotbolls-VM 1958."},
  {"id": "liseberg", "lat": 57.6950, "lon": 11.9925, "r": 280,
   "text": "{side} ligger nöjesparken Liseberg."},
]
