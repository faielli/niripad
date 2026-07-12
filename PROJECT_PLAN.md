# Editor di testo integrato per Arch Linux (Niri / Wayland)

## Contesto del progetto

Editor di testo multitab con syntax highlighting, pensato per girare
nativamente su Arch Linux con:

- Compositor **Niri** (Wayland, scrollable-tiling), senza KDE
- GPU NVIDIA con driver proprietari legacy (`nvidia-550xx-utils`, GTX 1070)
- Possibile presenza di **DankMaterialShell (DMS)** come shell
- Launcher Wayland-native (es. wofi, fuzzel) invece di menu stile KDE

Stack: Python 3 + PyQt6.

## Regole di esecuzione per l'agente

- Esegui **UNA fase alla volta**, nell'ordine in cui sono elencate.
- Al termine di ogni fase, fornisci una checklist di test manuale e
  **fermati** in attesa di conferma prima di procedere alla fase successiva.
- Mostra diff o file modificati/aggiunti ad ogni fase, non riscrivere da
  zero moduli già completati nelle fasi precedenti.
- Mantieni la struttura modulare: `main.py`, `editor_tab.py`,
  `main_window.py`, e nuovi moduli separati per ogni funzionalità
  significativa (es. `syntax_highlighter.py`, `search_dialog.py`,
  `file_tree.py`, `command_palette.py`, `theme_manager.py`).
- Non introdurre dipendenze da KDE (KIO, KDE Frameworks, ecc.) o
  assunzioni su un window manager con decorazioni proprie: Niri gestisce
  il tiling, quindi l'editor deve restare "leggero" a livello di finestra.

---

## Fase 1 — Scheletro base + integrazione Wayland/Niri

Crea lo scheletro dell'editor:

- Finestra principale con `QTabWidget` per tab multiple
- Apertura/chiusura file da menu e scorciatoie: Ctrl+O, Ctrl+N, Ctrl+W
- Salvataggio (Ctrl+S) e "salva con nome"
- Indicatore visivo (es. asterisco nel titolo tab) per modifiche non salvate

Vincoli specifici Niri/Wayland/NVIDIA:

- Forza `QT_QPA_PLATFORM=wayland` con fallback a xwayland se necessario
- Nessuna decorazione client-side pesante o barra titolo custom invasiva:
  usa le CSD minime di Qt, valuta `QT_WAYLAND_DISABLE_WINDOWDECORATION`
  se serve integrazione più pulita col tiling di Niri
- Verifica/documenta eventuali variabili d'ambiente utili contro
  tearing o flickering con NVIDIA proprietario su Wayland
  (es. `__GL_GSYNC_ALLOWED`, `__GL_VRR_ALLOWED`)
- Includi un file `.desktop` compatibile con launcher Wayland-native
  (wofi, fuzzel, rofi-wayland)

**Checklist di test attesa:** apertura/chiusura tab, resize e
comportamento sotto tiling automatico di Niri, focus da tastiera,
salvataggio file.

---

## Fase 2 — Syntax highlighting

Aggiungi syntax highlighting via `QSyntaxHighlighter` per:

Python, Bash/Shell, C/C++, JavaScript/TypeScript, HTML/CSS, JSON, YAML,
TOML, Markdown, SQL, Rust.

- Rilevamento automatico del linguaggio da estensione file e da shebang
- Tema scuro di default (stile Nord o Dracula), con supporto per tema
  chiaro alternativo
- Non modificare la logica di apertura/salvataggio della Fase 1

**Checklist di test attesa:** apertura di un file per ciascun linguaggio
supportato, verifica colori/evidenziazione corretti, cambio tema.

---

## Fase 3 — Ricerca, sostituzione e funzioni core da editor moderno

Aggiungi:

- Ricerca/sostituzione con supporto regex (Ctrl+F, Ctrl+H), ricerca
  estesa a tutti i tab aperti
- Numerazione righe
- Auto-indentazione e bracket/quote auto-chiusura
- Code folding
- Undo/redo multilivello persistente per sessione

**Checklist di test attesa:** ricerca con e senza regex, sostituzione
singola/globale, folding di blocchi annidati, undo/redo su più modifiche.

---

## Fase 4 — File tree, produttività e configurazione

Aggiungi:

- Pannello laterale con `QTreeView` per navigare una cartella di progetto
- Command palette in stile VSCode (Ctrl+Shift+P) con le azioni principali
- Scorciatoie da tastiera rimappabili da file di configurazione
  (`~/.config/nome-editor/keybindings.json` o `.toml`)
- File di configurazione generale per tema, font, plugin abilitati
  (`~/.config/nome-editor/config.toml`)

**Checklist di test attesa:** navigazione file tree, apertura file da
doppio click, esecuzione azioni da command palette, modifica
keybinding da file e verifica che venga applicata al riavvio.

---

## Fase 5 — Integrazione desktop Niri avanzata

Aggiungi (senza toccare le funzionalità delle fasi precedenti):

- Sincronizzazione tema dark/light: dato che senza KDE non c'è un
  color-scheme daemon centralizzato, leggi la preferenza da una fonte
  compatibile con l'ambiente (es. `gsettings`, variabile d'ambiente
  `GTK_THEME`, o file di configurazione di DMS se presente), con
  fallback manuale da impostazioni interne dell'editor
- Esempio di binding in formato KDL per `~/.config/niri/config.kdl`
  per aprire l'editor con una scorciatoia dedicata
- Se DankMaterialShell (DMS) è rilevabile: suggerisci eventuali
  window-rule Niri per comportamento floating/tiling di default
  (es. dialog di ricerca sempre floating, finestra principale sempre tiled)

**Checklist di test attesa:** cambio tema di sistema riflesso
nell'editor, apertura via keybinding Niri, comportamento floating/tiled
coerente con le window-rule suggerite.
