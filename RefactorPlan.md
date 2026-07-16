# RefactorPlan

## Cél

Az app jelenlegi, modulonként különálló Python fájlszerkezetét professzionálisabb, skálázhatóbb, könnyebben karbantartható desktop alkalmazás struktúrává kell alakítani.

A fő célok:

- egységes projektstruktúra
- tiszta backend/frontend szétválasztás
- új modulok könnyebb hozzáadása
- kevesebb duplikált UI és worker kód
- jobb tesztelhetőség
- stabilabb buildelés PyInstallerrel
- átláthatóbb importok
- egységes hibakezelés, logging és progress kezelés

---

## Javasolt célstruktúra

```text
dataprocessingtool/
├── main.pyw
├── README.md
├── requirements.txt
├── version.json
├── RefactorPlan.md
│
├── app/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── paths.py
│   │   └── constants.py
│   │
│   ├── frontend/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── theme.py
│   │   ├── routes.py
│   │   ├── components/
│   │   │   ├── __init__.py
│   │   │   ├── file_picker_row.py
│   │   │   ├── progress_dialog.py
│   │   │   ├── csv_viewer.py
│   │   │   └── message_helpers.py
│   │   └── modules/
│   │       ├── __init__.py
│   │       ├── barcode_pdf/
│   │       │   ├── __init__.py
│   │       │   └── view.py
│   │       ├── cofanet/
│   │       │   ├── __init__.py
│   │       │   └── view.py
│   │       ├── ksh/
│   │       │   ├── __init__.py
│   │       │   └── view.py
│   │       ├── merkantil/
│   │       │   ├── __init__.py
│   │       │   └── view.py
│   │       └── mouse_mover/
│   │           ├── __init__.py
│   │           └── view.py
│   │
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── workers/
│   │   │   ├── __init__.py
│   │   │   ├── background_worker.py
│   │   │   └── background_task.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── update_service.py
│   │   │   ├── file_service.py
│   │   │   └── logging_service.py
│   │   └── modules/
│   │       ├── __init__.py
│   │       ├── barcode_pdf/
│   │       │   ├── __init__.py
│   │       │   ├── service.py
│   │       │   └── models.py
│   │       ├── cofanet/
│   │       │   ├── __init__.py
│   │       │   ├── service.py
│   │       │   ├── parser.py
│   │       │   ├── excel_writer.py
│   │       │   └── models.py
│   │       ├── ksh/
│   │       │   ├── __init__.py
│   │       │   ├── service.py
│   │       │   ├── parser.py
│   │       │   ├── excel_writer.py
│   │       │   └── models.py
│   │       ├── merkantil/
│   │       │   ├── __init__.py
│   │       │   ├── service.py
│   │       │   ├── parser.py
│   │       │   ├── csv_writer.py
│   │       │   └── models.py
│   │       └── mouse_mover/
│   │           ├── __init__.py
│   │           ├── service.py
│   │           └── models.py
│   │
│   └── resources/
│       ├── __init__.py
│       └── resource_path.py
│
├── icons/
│   ├── coface_icon.png
│   ├── ksh_icon.png
│   ├── mouse_icon.png
│   ├── otp_icon.png
│   ├── pdf_icon.png
│   └── synthwave_icon.png
│
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   ├── barcode_pdf/
│   ├── cofanet/
│   ├── ksh/
│   └── merkantil/
│
├── build/
│   ├── pyinstaller.spec
│   └── hooks/
│
└── logs/
```

---

## Fő architekturális elvek

| Elv | Magyarázat | Haszon |
|---|---|---|
| `main.pyw` legyen az egyetlen belépési pont | Innen induljon a Qt app és a főablak | Egyszerű indítás, tiszta build |
| `frontend` csak UI-val foglalkozzon | Ablakok, gombok, dialogok, routing | Könnyebb UI módosítás |
| `backend` csak feldolgozással foglalkozzon | PDF, Excel, CSV, fájlműveletek, üzleti logika | Tesztelhetőbb kód |
| Modulonként azonos struktúra | Minden modulban `view.py`, `service.py`, `models.py` | Könnyebb bővítés |
| Közös worker rendszer | Egy központi háttérfeladat-kezelés | Egységes progress/cancel/error |
| Közös komponensek | File picker, progress dialog, üzenetek | Kevesebb duplikáció |
| Konfiguráció központosítása | Pathok, verzió, app metadata, GitHub repo adatok | Kevesebb hardcoded érték |
| Tesztek backend modulokra | UI nélkül tesztelhető feldolgozás | Biztonságos refaktor |

---

## Javasolt refaktorálási fázisok

## 1. fázis: Projektstruktúra előkészítése

### Feladatok

- Új `app/` mappa létrehozása.
- `main.pyw` létrehozása a projekt gyökerében.
- Jelenlegi `main_menu.pyw` logikájának későbbi átköltöztetése `app/frontend/main_window.py` alá.
- `icons/` mappa megtartása gyökérszinten.
- `theme.py`, `utils.py`, `background_worker.py`, `background_task.py` későbbi áthelyezési céljainak kijelölése.

### Eredmény

A projektnek lesz egy világos, új célstruktúrája, de ebben a fázisban még minimális viselkedésváltozással.

---

## 2. fázis: Közös infrastruktúra áthelyezése

### Jelenlegi fájl | Célhely

| Jelenlegi | Új hely |
|---|---|
| `theme.py` | `app/frontend/theme.py` |
| `utils.py` | `app/resources/resource_path.py` vagy `app/config/paths.py` |
| `background_worker.py` | `app/backend/workers/background_worker.py` |
| `background_task.py` | `app/backend/workers/background_task.py` |
| `auto_updater.py` | `app/backend/services/update_service.py` |

### Fontos

Ebben a fázisban csak importokat szabad rendezni. Üzleti logikát még nem érdemes átírni.

### Eredmény

A közös app infrastruktúra elkülönül a konkrét üzleti moduloktól.

---

## 3. fázis: Főablak és routing kialakítása

### Javaslat

A jelenlegi `main_menu.pyw` helyett legyen:

```text
main.pyw
app/frontend/main_window.py
app/frontend/routes.py
```

### `routes.py` szerepe

A modulok listája ne hardcoded gombgeneráló listában legyen, hanem strukturált route definícióként.

Példa route-adatok szintjén:

| Mező | Jelentés |
|---|---|
| `id` | modul azonosító |
| `label` | gomb felirata |
| `icon` | ikon elérési út |
| `view_class` | megnyitandó UI osztály |
| `enabled` | modul aktív-e |

### Haszon

- Új modul hozzáadása egyszerűbb.
- A főablak nem tud túl sokat a modulokról.
- Később keresés, jogosultság, kategorizálás is könnyebb.

---

## 4. fázis: Modulok egységesítése

### Jelenlegi modulok javasolt új nevei

| Jelenlegi mappa | Új modulnév |
|---|---|
| `barcode_pdf_masolas` | `barcode_pdf` |
| `cofanet_help` | `cofanet` |
| `ksh_iparagi_ertekesites` | `ksh` |
| `merkantil_pdf_feldolgozo` | `merkantil` |
| `mouse_mover` | `mouse_mover` |

### Modulonkénti frontend/backend felosztás

Minden modul kapjon frontend és backend oldalt:

```text
app/frontend/modules/ksh/view.py
app/backend/modules/ksh/service.py
app/backend/modules/ksh/models.py
```

### Szerepkörök

| Fájl | Feladat |
|---|---|
| `view.py` | PySide6 UI, input mezők, gombok, message boxok |
| `service.py` | fő üzleti folyamat |
| `parser.py` | bemeneti fájlok olvasása/parsolása |
| `excel_writer.py` | Excel mentés/formázás |
| `csv_writer.py` | CSV export |
| `models.py` | dataclass alapú eredmény/input modellek |

---

## 5. fázis: Backend service-ek tisztítása

### Cél

A feldolgozó függvények ne ad-hoc dict-eket adjanak vissza, hanem egységes eredményobjektumokat.

### Javasolt eredménystruktúra

Minden feldolgozó service hasonló adatokat adjon vissza:

| Mező | Jelentés |
|---|---|
| `success` | sikeres volt-e |
| `cancelled` | megszakították-e |
| `output_path` | fő kimeneti fájl |
| `summary` | rövid emberi összegzés |
| `warnings` | nem végzetes problémák |
| `stats` | darabszámok, feldolgozott sorok |

### Haszon

- UI egységesen tud üzenetet mutatni.
- Könnyebb logolni.
- Könnyebb tesztelni.

---

## 6. fázis: Worker rendszer professzionalizálása

### Jelenlegi állapot

Már van közös:

- `BackgroundWorker`
- `BackgroundTask`

### Javasolt továbbfejlesztés

Kerüljön ide:

```text
app/backend/workers/
├── background_worker.py
├── background_task.py
├── progress.py
└── task_result.py
```

### Javasolt egységes progress modell

| Mező | Jelentés |
|---|---|
| `message` | aktuális lépés szövege |
| `current` | aktuális állás |
| `total` | teljes mennyiség |
| `indeterminate` | határozatlan progress |

### Haszon

- Egységes progress minden modulban.
- Könnyebb cancel kezelés.
- Kevesebb UI-specifikus ismétlés.

---

## 7. fázis: Konfiguráció és path kezelés

### Javasolt fájlok

```text
app/config/settings.py
app/config/paths.py
app/config/constants.py
```

### Ide kerüljenek

| Elem | Jelenlegi probléma |
|---|---|
| GitHub owner/repo | `auto_updater.py`-ban hardcoded |
| output mappák | modulonként külön képződnek |
| verziófájl neve | globális stringként van |
| log fájl neve | globális stringként van |
| ikon pathok | több helyen kézzel hivatkozva |

### Haszon

- Egyszerűbb build/release.
- Kevesebb véletlen path hiba.
- Könnyebb később portable/appdata módra váltani.

---

## 8. fázis: Logging és hibakezelés

### Javasolt struktúra

```text
app/backend/services/logging_service.py
logs/app.log
logs/update.log
```

### Javasolt logging szintek

| Szint | Mire |
|---|---|
| `INFO` | feldolgozás indul/kész |
| `WARNING` | hiányzó fájl, kihagyott sor |
| `ERROR` | feldolgozási hiba |
| `DEBUG` | fejlesztői részletek |

### UI hibák

A UI ne nyers tracebacket mutasson elsődlegesen. Legyen:

- rövid emberi hibaüzenet
- opcionális részletek gomb
- log fájlba teljes traceback

---

## 9. fázis: Tesztstruktúra

### Javasolt mappa

```text
tests/
├── fixtures/
│   ├── barcode_pdf/
│   ├── cofanet/
│   ├── ksh/
│   └── merkantil/
├── test_barcode_pdf.py
├── test_cofanet.py
├── test_ksh.py
└── test_merkantil.py
```

### Elsőként tesztelendő részek

| Modul | Tesztelendő |
|---|---|
| Barcode PDF | Excelből barcode lista, hiányzó PDF lista, másolt darabszám |
| Merkantil | PDF textből kategóriák, összegek, CSV tartalom |
| Cofanet | SAP parser, Praktiker összevonás, EUR/HUF konverzió |
| KSH | Matstamm lookup, Egyenleg számítás, XLSX fejléc |

### Haszon

A nagy refaktor biztonságosan végezhető, mert minden lépés után ellenőrizhető az üzleti működés.

---

## 10. fázis: Build és release rendezése

### Javasolt mappa

```text
build/
├── pyinstaller.spec
├── hooks/
└── assets_manifest.txt
```

### Rendezendő pontok

- ikonok biztos csomagolása
- dinamikus importok megszüntetése vagy explicit hidden import lista
- `version.json` kezelése
- auto-update kompatibilitás
- output/log mappák helye becsomagolt futásnál

---

## 11. fázis: Auto-updater újragondolása

### Jelenlegi kockázat

Az updater közvetlenül GitHub release-ből írja felül a fájlokat. Ez működőképes, de hosszabb távon kockázatos.

### Javasolt fejlesztések

| Fejlesztés | Miért |
|---|---|
| backup update előtt | hibás update visszaállítható |
| checksum ellenőrzés | sérült letöltés kiszűrhető |
| release asset preferálása zipball helyett | kontrolláltabb csomag |
| update lock file | párhuzamos update elkerülése |
| rollback funkció | stabilabb felhasználói élmény |

---

## Refaktorálási sorrend javaslat

| Sorrend | Lépés | Kockázat |
|---|---|---|
| 1 | Új mappák létrehozása | alacsony |
| 2 | Közös infra áthelyezése | alacsony-közepes |
| 3 | `main.pyw` és főablak áthelyezése | közepes |
| 4 | Egy modul próba-refaktora, pl. Barcode PDF | közepes |
| 5 | Tesztek hozzáadása az első modulhoz | alacsony |
| 6 | Merkantil refaktor | közepes |
| 7 | Cofanet refaktor | közepes-magas |
| 8 | KSH refaktor | magas |
| 9 | Mouse Mover refaktor | alacsony-közepes |
| 10 | Build/update rendezés | magas |

---

## Ajánlott első pilot modul

Elsőként a `barcode_pdf` modult érdemes refaktorálni.

### Miért?

- kisebb üzleti logika
- egyszerű input/output
- gyorsan manuálisan tesztelhető
- jó minta lehet a többi modulhoz

### Pilot cél

A Barcode modulból kialakítani a végleges mintát:

```text
app/frontend/modules/barcode_pdf/view.py
app/backend/modules/barcode_pdf/service.py
app/backend/modules/barcode_pdf/models.py
```

Ha ez stabil, ugyanazt a mintát lehet alkalmazni a többi modulra.

---

## Refaktor közbeni szabályok

| Szabály | Miért fontos |
|---|---|
| Egyszerre csak egy modul mozgatása | könnyebb hibakeresés |
| Minden lépés után manuális teszt | UI regresszió kiszűrése |
| Üzleti logika módosítása nélkül kezdeni | kisebb kockázat |
| Importok rendezése külön commitban | könnyebb review |
| Tesztek írása a nagyobb mozgatások előtt | biztonság |
| Régi mappák törlése csak a végén | rollback lehetőség |

---

## Végállapot

A refaktor végére az app:

- `main.pyw`-ból indul
- tiszta `app/frontend` és `app/backend` szerkezetet használ
- modulonként egységes felépítésű
- közös worker/progress rendszert használ
- tesztelhető backend service-ekre épül
- könnyebben buildelhető és release-elhető
- új modulokkal egyszerűen bővíthető

---

## Rövid ajánlás

A teljes refaktort nem érdemes egy nagy lépésben megcsinálni. A legbiztonságosabb út:

1. új struktúra létrehozása
2. közös infrastruktúra áthelyezése
3. Barcode modul pilot refaktor
4. tesztelés
5. többi modul egyenkénti áthelyezése
6. build/update véglegesítése

Így a projekt professzionálisabb lesz, de közben végig működőképes marad.
