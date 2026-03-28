# STNH Event Browser - Projektdokumentation

Vollständige technische Dokumentation des Star Trek: New Horizons Event Browsers.
Ein Single-Page-Application (SPA) zur Darstellung aller ~8.867 Events des STNH Stellaris-Mods.

---

## Inhaltsverzeichnis

1. [Projektübersicht](#1-projektübersicht)
2. [Verzeichnisstruktur](#2-verzeichnisstruktur)
3. [Daten-Pipeline (Python)](#3-daten-pipeline-python)
4. [Frontend (HTML/CSS/JS)](#4-frontend-htmlcssjs)
5. [Generierte Assets](#5-generierte-assets)
6. [Deployment (GitHub Pages)](#6-deployment-github-pages)
7. [Update-Workflow](#7-update-workflow)
8. [Konfiguration anpassen](#8-konfiguration-anpassen)
9. [Erweiterung & Wartung](#9-erweiterung--wartung)

---

## 1. Projektübersicht

| Eigenschaft | Wert |
|---|---|
| Events | ~8.867 |
| Event-Dateien | 430 (0 Parse-Fehler) |
| Namespaces | 287 |
| Sprachen | 7 (EN, DE, FR, ES, RU, PL, BR-PT) |
| Event-Bilder | 731 WebP (8,1 MB) |
| GFX Sprites | 3.960 gesamt, 728 Event-Bilder |
| Pipeline-Laufzeit | ~11 Sekunden |
| Frontend | Vanilla HTML/CSS/JS (~12 KB JS, ~16 KB CSS) |
| Deployment | GitHub Pages (automatisch bei push) |

### Architektur-Diagramm

```
┌─────────────────────────────────────────────────────────┐
│  STNH Mod (git01/)                                      │
│  ├── events/*.txt          (430 Dateien, PDX-Syntax)    │
│  ├── localisation/{lang}/  (7 Sprachen, .yml)           │
│  ├── interface/*.gfx       (45 Dateien, Sprite-Defs)    │
│  ├── common/on_actions/    (18 Dateien)                  │
│  ├── common/event_chains/  (19 Dateien)                  │
│  └── gfx/event_pictures/   (DDS-Quelldateien)           │
└──────────────────────┬──────────────────────────────────┘
                       │ Python Pipeline (UPDATE_EVENTS.py)
                       ▼
┌─────────────────────────────────────────────────────────┐
│  Event Browser (git10/)                                  │
│  ├── assets/               (generierte JSON-Dateien)     │
│  ├── pictures/             (konvertierte WebP-Bilder)    │
│  ├── js/                   (Frontend-Module)             │
│  ├── index.html            (SPA Entry Point)             │
│  └── style.css             (Dark Theme)                  │
└──────────────────────┬──────────────────────────────────┘
                       │ git push → GitHub Pages
                       ▼
              [ Live Website ]
```

---

## 2. Verzeichnisstruktur

```
stnh_event_browser/
│
├── .github/
│   └── workflows/
│       └── deploy.yml              # GitHub Pages Auto-Deployment
│
├── assets/                          # [GENERIERT] JSON-Daten
│   ├── events_index.json           # Leichtgewichtiger Event-Index (2,6 MB)
│   ├── namespaces.json             # Namespace-Metadaten (Faction, Category)
│   ├── relationships.json          # Event-Trigger-Graph (635 KB)
│   ├── on_actions.json             # On-Action → Event Mappings
│   ├── event_chains.json           # Event-Chain-Definitionen
│   ├── pictures_map.json           # GFX-Name → Textur-Pfad (647 KB)
│   ├── last_update.json            # Timestamp + Phasen-Statistiken
│   ├── events_detail/              # Detail-JSONs pro Namespace (272 Dateien)
│   │   ├── STH_federation_flavour.json
│   │   ├── STH_klingon_story.json
│   │   └── ...
│   └── localisation/               # Gefilterte Loc-Keys pro Sprache
│       ├── english.json
│       ├── german.json
│       └── ...
│
├── pictures/                        # [GENERIERT] 731 WebP Event-Bilder
│   ├── abronath_arming.webp
│   └── ...
│
├── fonts/                           # Star Trek Schriftarten
│   ├── federation-ds9-title.TTF
│   └── Tungsten-Light.ttf
│
├── js/                              # Frontend JavaScript
│   ├── data.js                     # DataManager - Asynchrones Laden
│   ├── state.js                    # AppState - URL-synchronisierter State
│   ├── i18n.js                     # Mehrsprachigkeit
│   ├── search.js                   # Volltextsuche
│   ├── filters.js                  # Filterlogik
│   ├── render.js                   # HTML-Rendering (Cards + Detail)
│   ├── main.js                     # App-Initialisierung
│   └── ui/                         # UI-Komponenten
│       ├── event-list.js           # Paginierte Event-Liste
│       ├── event-detail.js         # Event-Detailansicht
│       ├── namespace-nav.js        # Sidebar-Navigation (Faction-Gruppen)
│       └── chain-viewer.js         # Event-Chain-Visualisierung
│
├── update/                          # Python Daten-Pipeline
│   ├── UPDATE_EVENTS.py            # Master-Script (7 Phasen)
│   ├── UPDATE.bat                  # Ein-Klick Update + Deploy (goto-basiert)
│   ├── UPDATE_QUICK.bat            # Schnell-Update ohne Bilder (goto-basiert)
│   ├── config.py                   # Pfade & Konfiguration
│   ├── parse_pdx.py               # Rekursiver PDX-Parser
│   ├── lex_pdx.py                 # (Legacy) PLY-Lexer, nicht mehr verwendet
│   ├── parse_events.py            # Event-Extraktion
│   ├── parse_localisation.py      # Lokalisierungs-Parser
│   ├── parse_gfx_mappings.py      # GFX Sprite-Mappings
│   ├── parse_on_actions.py        # On-Action-Parser
│   ├── parse_event_chains.py      # Event-Chain-Parser
│   ├── build_relationships.py     # Trigger-Graph-Builder
│   ├── generate_events_json.py    # JSON-Generierung + Faction-Mapping
│   ├── convert_images.py          # DDS → WebP Konvertierung
│   └── requirements.txt           # Python-Abhängigkeiten
│
├── index.html                       # SPA Entry Point
├── style.css                        # Komplettes Styling (16 KB)
└── .gitignore
```

---

## 3. Daten-Pipeline (Python)

### 3.1 Master-Script: `UPDATE_EVENTS.py`

Orchestriert alle 7 Phasen der Datenverarbeitung:

```
Phase 1: Pfad-Validierung     → config.validate_paths()
Phase 2: Lokalisierung parsen  → parse_all_languages()
Phase 3: GFX Sprites parsen    → parse_gfx_mappings()
Phase 4: Events parsen         → parse_all_events()
Phase 5: JSON generieren       → generate_all_json()
Phase 6: Bilder konvertieren   → convert_event_images()  [optional]
Phase 7: Zusammenfassung
```

**Aufruf:**
```bash
python UPDATE_EVENTS.py              # Vollständig (~11s)
python UPDATE_EVENTS.py --skip-images  # Ohne Bilder (~5s)
```

**Skeleton:**
```python
# UPDATE_EVENTS.py
import argparse, time
from config import validate_paths, print_config, ...
from parse_localisation import parse_all_languages
from parse_gfx_mappings import parse_gfx_mappings
from parse_events import parse_all_events
from generate_events_json import generate_all_json
from convert_images import convert_event_images

def phase_validate():     ...  # Prüft ob Mod-Pfad existiert
def phase_localisation(): ...  # → {lang: {key: value}} für 7 Sprachen
def phase_gfx():          ...  # → {sprite_name: {texturefile, frames}}
def phase_events():       ...  # → (events_list, namespaces_dict, stats)
def phase_generate():     ...  # → Schreibt alle JSON-Dateien
def phase_images(skip):   ...  # → DDS→WebP (nur neue/geänderte)
def phase_summary():      ...  # → Statistiken ausgeben

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-images', action='store_true')
    args = parser.parse_args()
    # Phasen 1-7 ausführen...
```

---

### 3.2 Konfiguration: `config.py`

Zentrale Pfad- und Datendefinitionen:

```python
# === PFADE ANPASSEN ===

# Stellaris-Mod-Verzeichnis (Quelldaten, read-only)
STNH_MOD_ROOT = r"C:\Users\marcj\git01\New-Horizons-Development"

# Event Browser Repository (Ausgabe)
EVENT_BROWSER_ROOT = r"C:\Users\marcj\git10\stnh_event_browser"

# Automatisch abgeleitet:
MOD_EVENTS_DIR       = STNH_MOD_ROOT / "events"
MOD_LOCALISATION_DIR = STNH_MOD_ROOT / "localisation"
MOD_ON_ACTIONS_DIR   = STNH_MOD_ROOT / "common/on_actions"
MOD_EVENT_CHAINS_DIR = STNH_MOD_ROOT / "common/event_chains"
MOD_INTERFACE_DIR    = STNH_MOD_ROOT / "interface"
MOD_GFX_EVENT_PICTURES = STNH_MOD_ROOT / "gfx/event_pictures"

OUTPUT_ASSETS_DIR        = EVENT_BROWSER_ROOT / "assets"
OUTPUT_EVENTS_DETAIL_DIR = OUTPUT_ASSETS_DIR / "events_detail"
OUTPUT_LOCALISATION_DIR  = OUTPUT_ASSETS_DIR / "localisation"
OUTPUT_PICTURES_DIR      = EVENT_BROWSER_ROOT / "pictures"

# Sprachen (Unterordner in localisation/)
LANGUAGES = ['english', 'german', 'french', 'spanish',
             'russian', 'polish', 'braz_por']

# Event-Typen (PDX-Schlüsselwörter)
EVENT_TYPES = ['country_event', 'planet_event', 'fleet_event',
               'ship_event', 'pop_event', 'observer_event',
               'situation_event']

# Funktionen
validate_paths()  # Prüft ob alle Quellpfade existieren
print_config()    # Gibt Konfiguration aus
```

**Zum Anpassen für andere Systeme:** Nur `STNH_MOD_ROOT` und `EVENT_BROWSER_ROOT` ändern.

---

### 3.3 PDX-Parser: `parse_pdx.py`

Eigenentwickelter rekursiver Parser für Stellaris PDX-Syntax (nicht PLY-basiert).

**Warum kein PLY?** PLY hatte Probleme mit Error Recovery bei den vielen Sonderfällen der PDX-Syntax (Doppelpunkte in IDs, Operatoren, @Variablen).

**Architektur:**

```python
# Tokenizer
class PdxLexer:
    """Regex-basierter Tokenizer für PDX-Syntax."""
    # Token-Typen: COMMENT, STRING, OPERATOR (>=, <=, >, <, =),
    #              LBRACE, RBRACE, VARIABLE (@name), NUMBER, WORD
    def tokenize(text) → list[Token]

# Parser
class PdxParser:
    """Rekursiver Descent Parser."""
    def parse(text) → list[dict]
    # Erkennt automatisch:
    # - key = value       → {'key': 'value'}
    # - key = { ... }     → {'key': [nested...]}   (Block)
    # - { val1 val2 }     → [val1, val2]           (Liste)

# Hilfsfunktionen für Zugriff auf Parse-Ergebnisse
def get_value(data, key, default=None)   # Einzelwert
def get_all_values(data, key)             # Alle Werte eines Keys
def get_blocks(data, key)                 # Alle Blöcke eines Keys
```

**Anpassung:** Neue Token-Typen in `PdxLexer.PATTERNS` hinzufügen. Neue Syntax-Konstrukte in `PdxParser.parse_statement()` behandeln.

---

### 3.4 Event-Parser: `parse_events.py`

Extrahiert alle Events aus den 430 Event-Dateien.

```python
def parse_all_events() → (events, namespaces, stats):
    """
    Rückgabe:
      events:     Liste aller Events (dicts)
      namespaces: {namespace_name: {files: [...], event_count: N}}
      stats:      {total_files, parsed_ok, total_events, ...}
    """

# Pro Event extrahierte Felder:
event = {
    'id':               'STH_federation_flavour.100',
    'type':             'country_event',
    'namespace':        'STH_federation_flavour',
    'source_file':      'STH_federation_flavour_events.txt',
    'title':            'STH_federation_flavour.100.name',  # Loc-Key
    'descriptions':     [{'text': 'loc_key', 'trigger': {...}}],
    'picture':          'GFX_evt_federation_council',
    'is_triggered_only': True,
    'hide_window':      False,
    'fire_only_once':   True,
    'diplomatic':       False,
    'trigger':          [...],    # PDX-Block
    'immediate':        [...],    # PDX-Block
    'after':            [...],    # PDX-Block
    'mean_time_to_happen': [...], # PDX-Block
    'options':          [{
        'name': 'loc_key',
        'allow': [...],
        'trigger': [...],
        'ai_chance': [...],
        'effects': [...],
        'triggered_events': ['event.id1', 'event.id2']
    }],
    'triggered_events': ['event.id1', ...]  # Gesamt (alle Quellen)
}
```

---

### 3.5 Lokalisierungs-Parser: `parse_localisation.py`

```python
def parse_all_languages() → {lang: {key: value}}
    """Parst .yml-Dateien aller 7 Sprachen."""
    # Regex: key:0 "value" oder key: "value"
    # Encoding: UTF-8-SIG mit latin-1 Fallback
    # Format-Codes (§R, §W, etc.) werden entfernt

def resolve_variable_refs(loc_data) → dict
    """Löst $key$-Referenzen rekursiv auf.
    Stellaris-Loc nutzt $other_key$ um Text aus anderen Keys einzubetten.
    z.B. ancrel.8021.desc = "$ancrel.8020.intro$\n\n$ancrel.8020.failure$"
    → wird zu vollem Text aufgelöst.
    Konvertiert auch literale \\n zu echten Newlines.
    Loop-Protection verhindert Endlos-Rekursion."""
```

**Bekanntes Problem:** Einige `.yml`-Dateien haben Encoding-Probleme. Der Parser versucht zuerst UTF-8-SIG, dann latin-1 als Fallback.

---

### 3.6 GFX-Mapping-Parser: `parse_gfx_mappings.py`

```python
def parse_gfx_mappings() → {sprite_name: {texturefile, frames}}
    """Parst 45 .gfx-Dateien, extrahiert spriteType und
    frameAnimatedSpriteType Blöcke."""
    # Ergebnis: 3.960 Sprites, davon 728 Event-Bilder
```

---

### 3.7 On-Actions-Parser: `parse_on_actions.py`

```python
def parse_on_actions() → {on_action_name: [event_ids]}
    """Parst 18 On-Action-Dateien.
    Unterstützt: events = { id1 id2 } und
                 country_event = { id = X }"""
```

---

### 3.8 Event-Chains-Parser: `parse_event_chains.py`

```python
def parse_event_chains() → {chain_id: {title, desc, picture, icon, counters}}
    """Parst 19 Event-Chain-Dateien."""
```

---

### 3.9 JSON-Generierung: `generate_events_json.py`

Zentrale Datei für die Ausgabe-Generierung. Enthält auch die **Faction-Zuordnung**.

```python
# Faction-Erkennung anhand des Namespace-Namens
FACTION_PATTERNS = {
    'federation': ['federation', 'fed_', 'starfleet', 'earth_', 'human_'],
    'klingon':    ['klingon', 'klg_'],
    'romulan':    ['romulan', 'rom_', 'reman'],
    'cardassian': ['cardassian', 'card_'],
    'dominion':   ['dominion'],
    'borg':       ['borg'],
    'ferengi':    ['ferengi'],
    'bajoran':    ['bajor'],
    'vulcan':     ['vulcan'],
    'andorian':   ['andorian', 'andor_'],
    'tholian':    ['tholian'],
    'breen':      ['breen'],
    'kazon':      ['kazon'],
    'vidiian':    ['vidiian'],
    'hirogen':    ['hirogen'],
    'species_8472': ['species_8472', 'undine', 'fluidic'],
    'xindi':      ['xindi'],
    'temporal':   ['temporal', 'time_'],
    'mirror':     ['mirror'],
    'generic':    [],  # Fallback
}

def detect_faction(namespace) → str:
    """Matcht namespace-Name gegen Patterns. Erste Übereinstimmung gewinnt."""

def detect_category(namespace, source_file) → str:
    """Kategorien: story, quest, diplomacy, war, anomaly, colony, crisis, tutorial, misc"""

def generate_all_json(events, namespaces, loc_data, gfx_data, on_actions, chains):
    """Generiert alle JSON-Ausgabedateien."""
```

**Neue Faction hinzufügen:**
1. Neuen Eintrag in `FACTION_PATTERNS` hinzufügen
2. Pattern-Strings sind Teilstring-Matches auf den lowercased Namespace-Namen
3. Frontend erkennt neue Factions automatisch (keine Änderung nötig)

---

### 3.10 Bildkonvertierung: `convert_images.py`

```python
def convert_event_images(gfx_mappings, events) → stats:
    """Konvertiert nur Event-referenzierte DDS-Bilder zu WebP.
    Benötigt: ImageMagick (magick convert)

    - Animierte Sprites (frames > 1): Erster Frame wird zugeschnitten
    - Einzelbilder: Direkte Konvertierung
    - Resize: 480x300, Qualität 80
    - Nur neue/geänderte Bilder werden konvertiert (Timestamp-Check)
    """
```

**Voraussetzung:** [ImageMagick](https://imagemagick.org/) muss installiert sein (`magick` im PATH). Wird bei `--skip-images` übersprungen.

---

### 3.11 Beziehungs-Graph: `build_relationships.py`

```python
def build_relationships(events) → {event_id: {triggers: [...], triggered_by: [...]}}
    """Baut bidirektionalen Trigger-Graph.
    Berücksichtigt: Event-Level und Option-Level triggered_events."""

def get_stats() → {total_edges, events_with_triggers}
```

---

## 4. Frontend (HTML/CSS/JS)

### 4.1 Übersicht

Single-Page-Application ohne Build-Tools, Frameworks oder npm. Vanilla HTML/CSS/JS.

### 4.2 `index.html` - Seitenstruktur

```
┌──────────────────────────────────────────────────┐
│ Header: Logo | Suchfeld | Sprach-Dropdown | Text ±│
├──────────────────────────────────────────────────┤
│ Filter-Bar: Typ | Faction | Kategorie | Toggles  │
├────────┬─────────────────────────┬───────────────┤
│ Side-  │ Event-Liste             │ Event-Detail  │
│ bar    │ (paginiert, 100/Seite)  │ (sticky)      │
│        │                         │               │
│ Fac-   │ [Card] [Card] [Card]    │ Bild          │
│ tions  │ [Card] [Card] [Card]    │ Meta-Badges   │
│  └ NS  │ [Card] [Card] [Card]    │ Beschreibung  │
│  └ NS  │                         │ Trigger       │
│        │ Pagination              │ Optionen      │
│        │                         │ Effekte       │
├────────┴─────────────────────────┴───────────────┤
│ Footer                                            │
└──────────────────────────────────────────────────┘
```

**Script-Ladereihenfolge (wichtig!):**
```html
<script src="js/data.js"></script>      <!-- 1. Daten-Layer -->
<script src="js/state.js"></script>     <!-- 2. State Management -->
<script src="js/i18n.js"></script>      <!-- 3. Internationalisierung -->
<script src="js/search.js"></script>    <!-- 4. Suchmaschine -->
<script src="js/filters.js"></script>   <!-- 5. Filter -->
<script src="js/render.js"></script>    <!-- 6. Rendering -->
<script src="js/ui/event-list.js"></script>
<script src="js/ui/event-detail.js"></script>
<script src="js/ui/namespace-nav.js"></script>
<script src="js/ui/chain-viewer.js"></script>
<script src="js/main.js"></script>      <!-- 7. Init (zuletzt!) -->
```

### 4.3 JavaScript-Module

#### `js/data.js` - DataManager

Asynchrones Laden und Caching aller Daten.

```javascript
const DataManager = (() => {
    // Öffentliche API:
    loadInitial()              // → Promise: events_index + namespaces + pictures_map
    loadNamespaceDetail(ns)    // → Promise: Lazy-Load Detail-JSON
    loadLocalisation(lang)     // → Promise: Lazy-Load Sprachdatei
    loadRelationships()        // → Promise: Trigger-Graph
    loadOnActions()            // → Promise: On-Action-Mappings
    loadEventChains()          // → Promise: Event-Chains

    getIndex()                 // → events_index Daten
    getNamespaces()            // → namespaces Daten
    getPictureUrl(gfxName)     // → WebP-Pfad oder null
})();
```

**Caching:** Detail- und Lokalisierungsdaten werden nach dem ersten Laden im Speicher gehalten.

#### `js/state.js` - AppState

URL-synchronisierter State mit localStorage-Persistenz.

```javascript
const AppState = (() => {
    // State-Felder (alle URL-Parameter):
    // search, type, faction, category, namespace,
    // showHidden, triggeredOnly, page, lang, selectedEvent, sort

    init()                     // URL-Parameter lesen
    get(key)                   // Wert lesen
    set(key, value)            // Wert setzen + URL aktualisieren
    setMultiple(updates)       // Mehrere Werte + URL
    onChange(callback)          // Listener registrieren
})();
```

**Persistenz:** Spracheinstellung wird in `localStorage['stnh_eb_lang']` gespeichert, Schriftgröße in `localStorage['stnh_eb_fontsize']`.

#### `js/i18n.js` - Internationalisierung

```javascript
const I18n = (() => {
    setLanguage(lang)          // Sprachdatei laden
    t(key)                     // Übersetzen (Fallback: Key selbst)
    getLang()                  // Aktuelle Sprache
})();
```

#### `js/search.js` - SearchEngine

Client-seitige Volltextsuche mit Spezial-Prefixen.

```javascript
const SearchEngine = (() => {
    search(query, events)      // → Gefilterte Events
    highlightText(text, query) // → HTML mit <mark>-Tags

    // Such-Modi:
    // "id:xyz"      → Event-ID-Suche
    // "ns:xyz"      → Namespace-Suche
    // "faction:xyz" → Faction-Suche
    // "xyz abc"     → Multi-Term AND über id, name, ns, snippet
})();
```

#### `js/filters.js` - Filter-Pipeline

```javascript
const Filters = (() => {
    apply(events, state)       // → Gefilterte Events (AND-Logik)
    populateDropdowns(events)  // → Dropdowns aus Daten befüllen

    // Pipeline: Type → Faction → Category → Hidden → Search → Namespace
})();
```

#### `js/render.js` - HTML-Rendering

```javascript
const Render = (() => {
    eventCard(event, query)    // → HTML für Event-Karte
    eventDetail(event, rels)   // → HTML für Detailansicht

    // Detail enthält: Bild, Meta-Badges, Beschreibungen,
    // Trigger, Immediate, Options, After, MTTH, Beziehungen
})();
```

#### `js/ui/event-list.js` - Event-Liste

```javascript
const EventList = (() => {
    render(events, page, query)      // → Paginierte Liste rendern
    renderPagination(total, page)    // → Pagination-Controls
    // 100 Events pro Seite
})();
```

#### `js/ui/event-detail.js` - Detailansicht

```javascript
const EventDetail = (() => {
    show(eventId, namespace)   // → Detail laden + anzeigen
    navigateToEvent(eventId)   // → Zu Event navigieren (z.B. aus Link)
    hide()                     // → Panel schließen
    init()                     // → Close-Button verdrahten
})();
```

#### `js/ui/namespace-nav.js` - Sidebar

```javascript
const NamespaceNav = (() => {
    render()                   // → Sidebar aus namespaces.json generieren
    updateActive()             // → Aktiven Namespace hervorheben

    // Gruppierung: Factions (klappbar) → Namespaces (mit Event-Count)
    // Sortierung: Factions alphabetisch, 'generic' immer zuletzt
    // Namespaces innerhalb einer Faction alphabetisch
    // Neue Factions werden automatisch erkannt!
})();
```

#### `js/ui/chain-viewer.js` - Event-Chain-Viewer

```javascript
const ChainViewer = (() => {
    show(eventId)              // → Modal mit Chain-Graph öffnen
    hide()                     // → Modal schließen
    // Rekursiver Tree-Build, max. Tiefe 10, Zyklen-Erkennung
})();
```

#### `js/main.js` - Initialisierung

```javascript
// Initialisierungsreihenfolge:
// 1. DataManager.loadInitial()
// 2. I18n.setLanguage(default)
// 3. Event-Namen aus Loc-Keys auflösen
// 4. Filter-Dropdowns befüllen
// 5. Namespace-Sidebar rendern
// 6. EventDetail + ChainViewer init
// 7. Initiales Rendering

// Font-Size-Control:
// - "Text −/+" Buttons im Header (rechts neben Sprach-Dropdown)
// - Bereich: 90% bis 160%, Schritte: ±10%
// - Default: 118%, gespeichert in localStorage['stnh_eb_fontsize']
// - Skaliert gesamte UI über CSS-Variable --base-font-size

// iframe-Einbettung (WordPress):
// - notifyParentHeight() sendet document.body.scrollHeight per postMessage
// - Aufgerufen nach jedem renderAll() und per ResizeObserver auf body
// - Nur aktiv wenn window.parent !== window (= eingebettet in iframe)
// - Parent empfängt {type: 'stnh-resize', height: N} und setzt iframe-Höhe

// Event-Listener:
// - Suchfeld (200ms Debounce)
// - Filter-Dropdowns
// - Sprach-Auswahl
// - Font-Size Buttons (−/+)
// - AppState onChange → renderAll()
// - ResizeObserver auf body (für iframe-Einbettung)
```

### 4.4 `style.css` - Design-System

```css
/* Basis-Schriftgröße (dynamisch per JS steuerbar) */
html { font-size: var(--base-font-size, 118%); }

/* Farbschema */
--bg:      #111111        /* Hintergrund */
--text:    #e4e7eb        /* Text */
--accent:  #d1ce04        /* Gold (Primär) */
--surface: #1a1a1a        /* Karten-Hintergrund */

/* Event-Typ-Farben */
country:   #4a9eff  (Blau)
ship:      #4aff7a  (Grün)
planet:    #c97a3a  (Orange)
fleet:     #ff9a4a  (Hell-Orange)
situation: #a64aff  (Lila)
observer:  #ff4a8a  (Pink)
pop:       #4affc8  (Cyan)

/* Schriftarten */
federation-ds9-title.TTF    /* Star Trek Überschriften */
Tungsten-Light.ttf          /* Badges und Labels */

/* Responsive Breakpoints */
@media (max-width: 1200px)  /* Sidebar verstecken */
@media (max-width: 921px)   /* Detail-Panel untendrunter */
@media (max-width: 544px)   /* Mobile Layout */
```

---

## 5. Generierte Assets

| Datei | Größe | Inhalt |
|---|---|---|
| `events_index.json` | 2,6 MB | Alle Events (kompakt): id, name, type, ns, pic, snippet, flags |
| `events_detail/{ns}.json` | ~4 MB | Volle Event-Daten pro Namespace (272 Dateien) |
| `namespaces.json` | 42 KB | Namespace → faction, category, source_files, event_count |
| `relationships.json` | 635 KB | Event-Trigger-Graph (bidirektional) |
| `on_actions.json` | 30 KB | on_action → [event_ids] |
| `event_chains.json` | 12 KB | Chain-Definitionen |
| `pictures_map.json` | 647 KB | GFX-Name → {texturefile, frames} (3.960 Sprites) |
| `localisation/{lang}.json` | ~100 KB | Gefilterte Loc-Keys (~10k pro Sprache) |
| `last_update.json` | ~1 KB | Timestamp + Phasen-Statistiken |
| `pictures/*.webp` | 8,1 MB | 731 WebP-Bilder (480×300, Q80) |

---

## 6. Deployment (GitHub Pages)

### `.github/workflows/deploy.yml`

```yaml
on:
  push:
    branches: [master]
  workflow_dispatch:        # Manuell auslösbar

jobs:
  deploy:
    permissions:
      pages: write
      id-token: write
      contents: read
    steps:
      - Checkout
      - Setup Pages
      - Upload artifact (ganzes Repo)
      - Deploy to GitHub Pages

concurrency:
  group: "pages"            # Nur ein Deployment gleichzeitig
```

**Trigger:** Jeder Push auf `master` startet automatisch das Deployment. Manuell über GitHub Actions "Run workflow" möglich.

---

## 7. Update-Workflow

### Vollständiges Update (mit Bildern)

```
update/UPDATE.bat per Doppelklick starten
  │
  ├── python UPDATE_EVENTS.py
  │   ├── Phase 1: Pfade validieren
  │   ├── Phase 2: 7 Sprachen parsen
  │   ├── Phase 3: GFX Sprites parsen
  │   ├── Phase 4: 430 Event-Dateien parsen
  │   ├── Phase 5: JSON generieren
  │   ├── Phase 6: Bilder konvertieren (DDS → WebP)
  │   └── Phase 7: Zusammenfassung
  │
  ├── git add assets/ pictures/
  ├── git commit -m "Update event browser - {datum}"
  └── git push → GitHub Pages Deployment
```

### Schnell-Update (ohne Bilder)

```
update/UPDATE_QUICK.bat per Doppelklick starten
  │
  ├── python UPDATE_EVENTS.py --skip-images
  ├── git add assets/
  ├── git commit -m "Update event browser (quick) - {datum}"
  └── git push
```

---

## 8. Konfiguration anpassen

### Anderes System / andere Pfade

Nur `update/config.py` ändern:

```python
# Diese beiden Pfade anpassen:
STNH_MOD_ROOT = r"D:\Games\Stellaris\mod\stnh"       # Mod-Verzeichnis
EVENT_BROWSER_ROOT = r"D:\Projects\stnh_event_browser" # Browser-Repo
```

### Neue Sprache hinzufügen

1. `config.py`: Sprache zu `LANGUAGES` Liste hinzufügen
2. Sicherstellen, dass `localisation/{neue_sprache}/` im Mod existiert
3. `index.html`: `<option>` zum Sprach-Dropdown hinzufügen

### Neue Faction hinzufügen

1. `generate_events_json.py`: Eintrag zu `FACTION_PATTERNS` hinzufügen:
   ```python
   'neue_faction': ['pattern1', 'pattern2'],
   ```
2. Frontend erkennt neue Factions automatisch (dynamische Sidebar)

### Neuen Event-Typ unterstützen

1. `config.py`: Typ zu `EVENT_TYPES` hinzufügen
2. `style.css`: Farbe für neuen Typ definieren:
   ```css
   .type-badge.neuer_event { background: #farbe; }
   ```

### Schriftgröße anpassen

Die Basis-Schriftgröße ist über eine CSS-Variable `--base-font-size` steuerbar.
Da alle Größen in `rem` definiert sind, skaliert die gesamte UI proportional.

- **Benutzer:** Text −/+ Buttons im Header (rechts neben Sprach-Dropdown)
- **Entwickler:** Default in `style.css` ändern:
  ```css
  html { font-size: var(--base-font-size, 118%); }  /* 118% = Default */
  ```
- **Bereich:** 90% – 160% (in 10%-Schritten)
- **Persistenz:** `localStorage['stnh_eb_fontsize']`

### Bilder-Qualität / Größe ändern

In `convert_images.py` die ImageMagick-Parameter anpassen:
- Zielgröße: `480x300` (resize Parameter)
- Qualität: `80` (quality Parameter)

---

## 9. Erweiterung & Wartung

### Neues Parser-Modul hinzufügen

1. Neue Datei `update/parse_neues_ding.py` erstellen
2. Funktion `parse_neues_ding() → data` implementieren
3. In `UPDATE_EVENTS.py` neue Phase einbinden
4. In `generate_events_json.py` Ausgabe-JSON generieren
5. Im Frontend (`js/data.js`) Ladefunktion hinzufügen

### Frontend-Modul hinzufügen

1. Neue Datei `js/ui/neues_modul.js` erstellen
2. Modul als IIFE (Revealing Module Pattern):
   ```javascript
   const NeuesModul = (() => {
       function render() { ... }
       return { render };
   })();
   ```
3. In `index.html` einbinden (vor `main.js`!)
4. In `js/main.js` initialisieren

### Häufige Wartungsaufgaben

| Aufgabe | Datei(en) |
|---|---|
| Faction falsch zugeordnet | `generate_events_json.py` → `FACTION_PATTERNS` |
| Neue Events werden nicht erkannt | `parse_pdx.py` (Parser-Fehler?) oder `parse_events.py` |
| Bilder fehlen | `parse_gfx_mappings.py` + `convert_images.py` prüfen |
| Lokalisierung fehlt/falsch | `parse_localisation.py` (Encoding? $key$-Referenzen?) |
| Filter funktioniert nicht | `js/filters.js` |
| Styling anpassen | `style.css` |

### Abhängigkeiten

| Abhängigkeit | Version | Zweck | Erforderlich? |
|---|---|---|---|
| Python | 3.8+ | Pipeline | Ja |
| ImageMagick | 7+ | DDS→WebP | Nur für Bilder |
| Git | - | Deployment | Ja |
| PLY | 3.11+ | (reserviert) | Nein (aktuell ungenutzt) |
| npm/Node | - | - | Nicht benötigt |
