(() => {
  // Virtual HUB75 LED Matrix Dimensions
  const COLS = 192;
  const ROWS = 64;
  const CELL = 8; // 192 * 8 = 1536px wide, 64 * 8 = 512px tall

  // State
  const state = {
    location: '49418',
    airport: 'KGRR',
    radiusNm: 45,
    filterMode: 'all',
    airlineFilter: 'all',
    palette: 'rgb',
    simMode: 'live',
    flights: [],
    operatorCounts: {},
    selectedIndex: 0,
    isLocked: false,
    lastCycleTime: performance.now(),
    cycleIntervalMs: 8000,
    tickerOffsetPx: 0,
    radarSweepDeg: 0,
    weather: null,
    observer: {
      id: '49418',
      name: 'Grandville, MI (ZIP 49418)',
      short_name: '49418 HOME',
      lat: 42.8836,
      lon: -85.7606,
      radius_nm: 45,
    },
    blipHitboxes: [],
  };

  const OPERATOR_LABELS = {
    all: 'ALL AIRLINES & CRAFT',
    DAL: 'DELTA AIR LINES',
    AAL: 'AMERICAN AIRLINES',
    UAL: 'UNITED AIRLINES',
    SWA: 'SOUTHWEST AIRLINES',
    AAY: 'ALLEGIANT AIR',
    GA_PRIVATE: 'PERSONAL / PRIVATE',
    CARGO: 'CARGO (FEDEX/UPS)',
    MIL_GOV: 'MILITARY / GOV',
    OTHER_COMM: 'OTHER COMMERCIAL',
  };

  // Standard 5x7 Dot-Matrix Bitmap Font (each row is 5-bit integer, 7 rows tall)
  const FONT_5X7 = {
    ' ': [0, 0, 0, 0, 0, 0, 0],
    'A': [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    'B': [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110],
    'C': [0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110],
    'D': [0b11100, 0b10010, 0b10001, 0b10001, 0b10001, 0b10010, 0b11100],
    'E': [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
    'F': [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000],
    'G': [0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01110],
    'H': [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    'I': [0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    'J': [0b00111, 0b00010, 0b00010, 0b00010, 0b10010, 0b10010, 0b01100],
    'K': [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001],
    'L': [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
    'M': [0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001],
    'N': [0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001],
    'O': [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    'P': [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
    'Q': [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101],
    'R': [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
    'S': [0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110],
    'T': [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
    'U': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    'V': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100],
    'W': [0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001],
    'X': [0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001],
    'Y': [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100],
    'Z': [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111],
    '0': [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
    '1': [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    '2': [0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111],
    '3': [0b11110, 0b00001, 0b00001, 0b01110, 0b00001, 0b00001, 0b11110],
    '4': [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
    '5': [0b11111, 0b10000, 0b10000, 0b11110, 0b00001, 0b10001, 0b01110],
    '6': [0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
    '7': [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
    '8': [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
    '9': [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100],
    ':': [0b00000, 0b00100, 0b00100, 0b00000, 0b00100, 0b00100, 0b00000],
    '.': [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b01100, 0b01100],
    ',': [0b00000, 0b00000, 0b00000, 0b00000, 0b00100, 0b00100, 0b01000],
    '-': [0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000],
    '+': [0b00000, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0b00000],
    '/': [0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000],
    '%': [0b11001, 0b11010, 0b00010, 0b00100, 0b01000, 0b01011, 0b10011],
    '°': [0b00110, 0b01001, 0b01001, 0b00110, 0b00000, 0b00000, 0b00000],
    '>': [0b10000, 0b01000, 0b00100, 0b00010, 0b00100, 0b01000, 0b10000],
    '<': [0b00001, 0b00010, 0b00100, 0b01000, 0b00100, 0b00010, 0b00001],
    '!': [0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00000, 0b00100],
    '(': [0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010],
    ')': [0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000],
    '•': [0b00000, 0b00000, 0b01110, 0b01110, 0b01110, 0b00000, 0b00000],
    '↑': [0b00100, 0b01110, 0b10101, 0b00100, 0b00100, 0b00100, 0b00100],
    '↓': [0b00100, 0b00100, 0b00100, 0b00100, 0b10101, 0b01110, 0b00100],
    '✈': [0b00100, 0b00110, 0b00110, 0b11111, 0b00110, 0b00110, 0b00100],
  };

  // Pixel-art aircraft silhouettes (16x7 bitmap strings — matches 7px text row height)
  const SILHOUETTES = {
    jet: [
      '.......XX.......',
      '.X....XXXX......',
      'XX...XXXXXX.....',
      'XXXXXXXXXXXXXXXX',
      'XX...XXXXXX.....',
      '.X....XXXX......',
      '.......XX.......',
    ],
    jumbo: [
      '......XXXX......',
      '.XX..XXXXXX.....',
      'XXX.XXXXXXXX....',
      'XXXXXXXXXXXXXXXX',
      'XXX.XXXXXXXX....',
      '.XX..XXXXXX.....',
      '......XXXX......',
    ],
    regional: [
      '........X.......',
      '.X.....XXX......',
      'XX....XXXXX.....',
      'XXXXXXXXXXXXXXX.',
      'XX....XXXXX.....',
      '.X.....XXX......',
      '........X.......',
    ],
    prop: [
      '.......XX.....X.',
      '.X.....XX....XX.',
      'XX....XXXX...XX.',
      'XXXXXXXXXXXXXXXX',
      'XX....XXXX...XX.',
      '.X.....XX....XX.',
      '.......XX.....X.',
    ],
    heli: [
      '...XXXXXXXXXX...',
      '.......XX.......',
      'XX...XXXXXX.....',
      'XXXXXXXXXXXXXXX.',
      '....XXXXXXXXX...',
      '....X......X....',
      '...XXXXXXXXXX...',
    ],
    military: [
      '.....XX.........',
      '.X..XXXX........',
      'XX.XXXXXX.......',
      'XXXXXXXXXXXXXXXX',
      'XX.XXXXXX.......',
      '.X..XXXX........',
      '.....XX.........',
    ],
  };

  // Pixel-art 16x16 Airline Tail Logos (matches exact 16-row height of two 5x7 text lines + 2px gap)
  const AIRLINE_LOGOS = {
    DAL: {
      // Delta Red Widget on Navy
      bg: '#0a1931',
      fg1: '#e31837',
      fg2: '#a81228',
      pattern: [
        '................',
        '.......11.......',
        '......1111......',
        '.....111111.....',
        '....111..111....',
        '...111....111...',
        '..111..22..111..',
        '.111..2222..111.',
        '.11..222222..11.',
        '....22222222....',
        '...2222222222...',
        '..222222222222..',
        '................',
        '..111111111111..',
        '....11111111....',
        '................',
      ],
    },
    UAL: {
      // United Blue Globe
      bg: '#002244',
      fg1: '#38bdf8',
      fg2: '#ffffff',
      pattern: [
        '................',
        '.....111111.....',
        '...1122112211...',
        '..121112211121..',
        '.11122222222111.',
        '.22111122111122.',
        '.11222222222211.',
        '.11111222211111.',
        '.11111222211111.',
        '.11222222222211.',
        '.22111122111122.',
        '.11122222222111.',
        '..121112211121..',
        '...1122112211...',
        '.....111111.....',
        '................',
      ],
    },
    AAL: {
      // American Eagle / Stripes
      bg: '#0d2238',
      fg1: '#0078d2',
      fg2: '#e31837',
      pattern: [
        '................',
        '..........1111..',
        '........11111...',
        '......111111....',
        '.....11111......',
        '....1111........',
        '...111..........',
        '......1122......',
        '.......222222...',
        '.....2222222....',
        '....222222......',
        '...22222........',
        '..2222..........',
        '.222............',
        '..22............',
        '................',
      ],
    },
    SWA: {
      // Southwest Heart
      bg: '#1c2c6b',
      fg1: '#ffbf27',
      fg2: '#e31837',
      pattern: [
        '................',
        '..2222....2222..',
        '.222222..222222.',
        '.22222222222222.',
        '.22222222222222.',
        '.11122222222222.',
        '..111112222222..',
        '..111111112222..',
        '...1111111122...',
        '....11111111....',
        '.....111111.....',
        '......1111......',
        '.......11.......',
        '..111111111111..',
        '....22222222....',
        '................',
      ],
    },
    AAY: {
      // Allegiant Sunburst
      bg: '#002e5d',
      fg1: '#ff8200',
      fg2: '#ffd100',
      pattern: [
        '................',
        '.......22.......',
        '..22...22...22..',
        '...22..11..22...',
        '.....111111.....',
        '....11122111....',
        '.22211222211222.',
        '.22211222211222.',
        '....11122111....',
        '.....111111.....',
        '...22..11..22...',
        '..22........22..',
        '................',
        '.11111111111111.',
        '..222222222222..',
        '................',
      ],
    },
    FDX: {
      // FedEx Purple & Orange
      bg: '#240a40',
      fg1: '#ffffff',
      fg2: '#ff6600',
      pattern: [
        '................',
        '..111111111111..',
        '................',
        '.11111..22222...',
        '.11.....22..22..',
        '.11.....22...22.',
        '.1111...22...22.',
        '.1111...22...22.',
        '.11.....22...22.',
        '.11.....22..22..',
        '.11.....22222...',
        '................',
        '..222222222222..',
        '....22222222....',
        '..111111111111..',
        '................',
      ],
    },
    RCH: {
      // USAF Military Star
      bg: '#0c2418',
      fg1: '#10b981',
      fg2: '#ffffff',
      pattern: [
        '................',
        '.......22.......',
        '.......22.......',
        '......2222......',
        '......2222......',
        '.11122222222111.',
        '.11112222221111.',
        '.111..2222..111.',
        '.....222222.....',
        '....22222222....',
        '....222..222....',
        '...222....222...',
        '..22........22..',
        '..111111111111..',
        '....11111111....',
        '................',
      ],
    },
    DEFAULT: {
      bg: '#131d31',
      fg1: '#f59e0b',
      fg2: '#38bdf8',
      pattern: [
        '................',
        '.......11.......',
        '......1111......',
        '......1111......',
        '.....111111.....',
        '..222111111222..',
        '.22222111122222.',
        '.22222111122222.',
        '..22..1111..22..',
        '......1111......',
        '......1111......',
        '.....221122.....',
        '....22211222....',
        '...222....222...',
        '..22........22..',
        '................',
      ],
    },
  };

  // Virtual Framebuffer: 2D array of hex color strings (or null for off)
  const buffer = Array.from({ length: ROWS }, () => Array(COLS).fill(null));

  function clearBuffer() {
    for (let r = 0; r < ROWS; r++) {
      buffer[r].fill(null);
    }
  }

  function mapPaletteColor(colorHex) {
    if (!colorHex) return null;
    if (state.palette === 'rgb') return colorHex;
    // Monochrome / Retro shader overrides
    const hex = colorHex.toLowerCase();
    const isDim = hex === '#1e293b' || hex === '#0f172a' || hex === '#131d31' || hex === '#0a1931';
    if (state.palette === 'amber') {
      return isDim ? '#3b2104' : '#ff9f1c';
    }
    if (state.palette === 'cyan') {
      return isDim ? '#082f49' : '#38bdf8';
    }
    if (state.palette === 'green') {
      return isDim ? '#062e16' : '#22c55e';
    }
    return colorHex;
  }

  function setPixel(x, y, color) {
    const ix = Math.round(x);
    const iy = Math.round(y);
    if (ix >= 0 && ix < COLS && iy >= 0 && iy < ROWS) {
      buffer[iy][ix] = mapPaletteColor(color);
    }
  }

  function drawRect(x, y, w, h, color) {
    for (let dy = 0; dy < h; dy++) {
      for (let dx = 0; dx < w; dx++) {
        setPixel(x + dx, y + dy, color);
      }
    }
  }

  function drawHLine(x1, x2, y, color, dashed = false) {
    for (let x = x1; x <= x2; x++) {
      if (!dashed || x % 2 === 0) setPixel(x, y, color);
    }
  }

  function drawVLine(x, y1, y2, color) {
    for (let y = y1; y <= y2; y++) {
      setPixel(x, y, color);
    }
  }

  function drawText5x7(text, x, y, color, spacing = 1) {
    const str = String(text || '').toUpperCase();
    let cursorX = Math.round(x);
    for (let i = 0; i < str.length; i++) {
      const ch = str[i];
      const glyph = FONT_5X7[ch] || FONT_5X7[' '];
      for (let row = 0; row < 7; row++) {
        const bits = glyph[row];
        for (let col = 0; col < 5; col++) {
          if ((bits >> (4 - col)) & 1) {
            setPixel(cursorX + col, y + row, color);
          }
        }
      }
      cursorX += 5 + spacing;
    }
    return cursorX;
  }

  function drawAirlineLogo(airlineIcao, x, y) {
    const logo = AIRLINE_LOGOS[airlineIcao] || AIRLINE_LOGOS.DEFAULT;
    for (let r = 0; r < 16; r++) {
      const rowStr = logo.pattern[r] || '................';
      for (let c = 0; c < 16; c++) {
        const ch = rowStr[c];
        if (ch === '1') setPixel(x + c, y + r, logo.fg1);
        else if (ch === '2') setPixel(x + c, y + r, logo.fg2);
        else setPixel(x + c, y + r, logo.bg);
      }
    }
  }

  function drawSilhouette(silhouetteKey, x, y, color) {
    const grid = SILHOUETTES[silhouetteKey] || SILHOUETTES.jet;
    for (let r = 0; r < grid.length; r++) {
      const rowStr = grid[r];
      for (let c = 0; c < rowStr.length; c++) {
        if (rowStr[c] === 'X') {
          setPixel(x + c, y + r, color);
        }
      }
    }
  }

  function composeMatrixFrame(timestamp) {
    clearBuffer();

    const flights = state.flights;
    const current = flights[state.selectedIndex] || null;

    // Structural divider lines on the 192x64 matrix:
    // Band 1 (Top):    y = 0..19  (20 rows -> 2px top pad, 16px content y=2..17, 2px bottom pad)
    // Divider 1:       y = 20
    // Band 2 (Middle): y = 21..49 (29 rows -> 2px top pad, 25px content y=23..47, 2px bottom pad)
    // Divider 2:       y = 50
    // Band 3 (Ticker): y = 51..63 (13 rows -> 3px top pad, 7px content y=54..60, 3px bottom pad)
    const dividerColor = '#1e293b';
    drawHLine(0, COLS - 1, 20, dividerColor);
    drawHLine(0, COLS - 1, 50, dividerColor);
    drawVLine(74, 0, 20, dividerColor);
    drawVLine(62, 21, 49, dividerColor);
    drawVLine(128, 21, 49, dividerColor);

    if (!current) {
      // Idle / Scanning mode when no flights match filter
      drawAirlineLogo('DEFAULT', 2, 2);
      drawText5x7('SCANNING SKY', 20, 2, '#f59e0b', 1);
      drawText5x7(state.observer.short_name, 20, 11, '#38bdf8', 1);
      drawText5x7('NO ACTIVE TRANSPONDERS IN FILTER', 10, 32, '#94a3b8', 1);
      renderBottomTicker(timestamp);
      return;
    }

    // Emergency Squawk 7700 Flashing Banner Override
    const isEmergency = current.squawk === '7700' || current.squawk === '7600';
    const flashOn = isEmergency && Math.floor(timestamp / 350) % 2 === 0;

    // --- ZONE 1: TOP LEFT (0..73, 0..19) — 16x16 Airline Logo + Two 5x7 Text Rows (y=2..17) ---
    drawAirlineLogo(current.airline_icao, 2, 2);
    const fltColor = isEmergency ? (flashOn ? '#ef4444' : '#ffffff') : '#ffffff';
    drawText5x7(current.flight_number.slice(0, 8), 20, 2, fltColor, 1);

    const subTag = `${current.type_code} ${current.registration}`.slice(0, 9);
    drawText5x7(subTag, 20, 11, '#f59e0b', 1);

    // --- ZONE 2: TOP RIGHT (75..191, 0..19) — Origin -> Destination + Animated Route Bar ---
    const orig = (current.origin_iata || '---').slice(0, 3);
    const dest = (current.dest_iata || '---').slice(0, 3);
    drawText5x7(orig, 78, 2, '#38bdf8', 1);

    // Route progress bar centered vertically on Line 1 (y=5 is center of y=2..8)
    const barStart = 99;
    const barEnd = 163;
    const pct = Math.max(5, Math.min(95, current.progress_pct || 50));
    const planeX = Math.round(barStart + ((barEnd - barStart) * pct) / 100);

    for (let x = barStart; x <= barEnd; x++) {
      if (x < planeX - 2) {
        setPixel(x, 5, '#10b981');
      } else if (x > planeX + 3 && x % 2 === 0) {
        setPixel(x, 5, '#334155');
      }
    }
    // Little glowing airplane icon centered at y=2..8 (fuselage on y=5)
    drawText5x7('✈', planeX - 2, 2, '#f59e0b', 1);

    drawText5x7(dest, 168, 2, '#10b981', 1);

    // Phase / Status Badge under route bar (y=11..17)
    const badgeColor =
      current.phase_type === 'emergency'
        ? '#ef4444'
        : current.phase_type === 'arriving_kgrr' || current.phase_type === 'departing_kgrr'
          ? '#f59e0b'
          : '#94a3b8';
    drawText5x7(current.phase_badge.slice(0, 18), 78, 11, badgeColor, 1);

    // --- ZONE 3: MIDDLE LEFT (0..61, 21..49) — ALTITUDE & VERTICAL RATE (y=23, 32, 41) ---
    drawText5x7('ALTITUDE', 3, 23, '#64748b', 1);
    const vArrow = current.vertical_rate_fpm > 300 ? '↑' : current.vertical_rate_fpm < -300 ? '↓' : '';
    const altStr = `${current.altitude_ft.toLocaleString()}FT${vArrow}`;
    const altColor =
      current.vertical_rate_fpm > 300
        ? '#10b981'
        : current.vertical_rate_fpm < -300
          ? '#38bdf8'
          : '#f8fafc';
    drawText5x7(altStr.slice(0, 9), 3, 32, altColor, 1);

    const vpmSign = current.vertical_rate_fpm > 0 ? '+' : '';
    const vpmText = `${vpmSign}${current.vertical_rate_fpm}FPM`;
    drawText5x7(vpmText.slice(0, 9), 3, 41, '#f59e0b', 1);

    // --- ZONE 4: MIDDLE CENTER (63..127, 21..49) — GROUND SPEED, TRACK & 16x7 SILHOUETTE ---
    drawText5x7('SPD/TRK', 66, 23, '#64748b', 1);
    // Draw 16x7 pixel-art aircraft silhouette aligned with 'SPD/TRK' row (y=23..29)
    drawSilhouette(current.silhouette, 110, 23, '#f59e0b');

    drawText5x7(`${current.ground_speed_kts}KTS`, 66, 32, '#f8fafc', 1);
    const hdgStr = `${String(current.track_deg).padStart(3, '0')}° ${current.track_cardinal}`;
    drawText5x7(hdgStr.slice(0, 9), 66, 41, '#38bdf8', 1);

    // --- ZONE 5: MIDDLE RIGHT (129..191, 21..49) — SKY SPOTTER & ACTIVE VHF FREQ ---
    const atcShort = current.atc?.sector_short || '128.40 APP';
    drawText5x7(atcShort.slice(0, 10), 132, 23, '#38bdf8', 1);
    drawText5x7(`${current.distance_mi}MI ${current.bearing_cardinal}`, 132, 32, '#10b981', 1);
    drawText5x7(`${Math.round(current.elevation_deg)}° UP`, 132, 41, '#f59e0b', 1);

    // --- ZONE 6: BOTTOM TICKER (0..191, 51..63 -> 3px top pad, y=54..60 text, 3px bottom pad) ---
    renderBottomTicker(timestamp);
  }

  function renderBottomTicker(timestamp) {
    // Build ticker string from active flights + live KGRR METAR
    const parts = [];
    parts.push(`[${state.observer.short_name} R:${state.radiusNm}NM]`);

    if (state.flights.length > 0) {
      state.flights.slice(0, 6).forEach((f, idx) => {
        const marker = idx === state.selectedIndex ? '*' : '•';
        const freq = f.atc?.frequency_mhz || '128.400';
        parts.push(`${marker}${f.flight_number} (${f.origin_iata}>${f.dest_iata}) ${f.altitude_ft}FT [${freq}MHZ] ${f.distance_mi}MI ${f.bearing_cardinal}`);
      });
    }

    if (state.weather) {
      parts.push(`${state.weather.station || state.airport} ${state.weather.flight_category}: WIND ${state.weather.wind} VIS ${state.weather.visibility} TEMP ${state.weather.temp_f}F`);
    }

    const fullTicker = parts.join('   /   ') + '       ';
    const totalPxWidth = fullTicker.length * 6;
    const scrollX = COLS - Math.floor((timestamp / 55) % (totalPxWidth + COLS));

    drawText5x7(fullTicker, scrollX, 54, '#38bdf8', 1);
  }

  function renderMatrixToCanvas() {
    const canvas = document.getElementById('led-matrix-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    // Pitch-black PCB substrate
    ctx.fillStyle = '#05070b';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const radius = CELL * 0.36;

    for (let r = 0; r < ROWS; r++) {
      const cy = r * CELL + CELL / 2;
      for (let c = 0; c < COLS; c++) {
        const cx = c * CELL + CELL / 2;
        const color = buffer[r][c];

        if (!color) {
          // Unlit physical LED cavity
          ctx.fillStyle = '#0e131d';
          ctx.beginPath();
          ctx.arc(cx, cy, radius * 0.82, 0, Math.PI * 2);
          ctx.fill();
        } else {
          // Outer LED bloom halo
          ctx.save();
          ctx.fillStyle = color;
          ctx.shadowColor = color;
          ctx.shadowBlur = 7;
          ctx.beginPath();
          ctx.arc(cx, cy, radius, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();

          // Hot center diode highlight
          ctx.fillStyle = 'rgba(255, 255, 255, 0.35)';
          ctx.beginPath();
          ctx.arc(cx - 0.6, cy - 0.6, radius * 0.38, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }
  }

  // --- POLAR SKY-DOME RADAR SCOPE ---
  function renderRadarScope() {
    const canvas = document.getElementById('radar-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const maxR = w / 2 - 22;

    ctx.clearRect(0, 0, w, h);

    // Dark phosphor CRT background
    const bgGrad = ctx.createRadialGradient(cx, cy, 10, cx, cy, maxR);
    bgGrad.addColorStop(0, '#071a16');
    bgGrad.addColorStop(1, '#040a0e');
    ctx.fillStyle = bgGrad;
    ctx.beginPath();
    ctx.arc(cx, cy, maxR, 0, Math.PI * 2);
    ctx.fill();

    // Range rings
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.22)';
    ctx.lineWidth = 1;
    [0.33, 0.66, 1.0].forEach((frac) => {
      ctx.beginPath();
      ctx.arc(cx, cy, maxR * frac, 0, Math.PI * 2);
      ctx.stroke();

      const ringNm = Math.round(state.radiusNm * frac);
      ctx.fillStyle = 'rgba(16, 185, 129, 0.55)';
      ctx.font = '600 10px "JetBrains Mono", monospace';
      ctx.fillText(`${ringNm}nm`, cx + 4, cy - maxR * frac + 12);
    });

    // Crosshairs
    ctx.beginPath();
    ctx.moveTo(cx - maxR, cy);
    ctx.lineTo(cx + maxR, cy);
    ctx.moveTo(cx, cy - maxR);
    ctx.lineTo(cx, cy + maxR);
    ctx.stroke();

    // Cardinal labels
    ctx.fillStyle = '#10b981';
    ctx.font = '700 11px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('N', cx, cy - maxR + 13);
    ctx.fillText('S', cx, cy + maxR - 5);
    ctx.fillText('E', cx + maxR - 9, cy + 4);
    ctx.fillText('W', cx - maxR + 9, cy + 4);

    // Helper: lat/lon -> radar x/y
    const latLonToRadar = (lat, lon) => {
      const dLatNm = (lat - state.observer.lat) * 60.0;
      const dLonNm = (lon - state.observer.lon) * 60.0 * Math.cos((state.observer.lat * Math.PI) / 180);
      const scale = maxR / state.radiusNm;
      return {
        x: cx + dLonNm * scale,
        y: cy - dLatNm * scale,
      };
    };

    // Plot KGRR Airport & Runways (42.8808, -85.5228)
    const kgrrPos = latLonToRadar(42.8808, -85.5228);
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(kgrrPos.x - 8, kgrrPos.y);
    ctx.lineTo(kgrrPos.x + 8, kgrrPos.y); // Rwy 08R/26L
    ctx.moveTo(kgrrPos.x, kgrrPos.y - 6);
    ctx.lineTo(kgrrPos.x, kgrrPos.y + 6); // Rwy 17/35
    ctx.stroke();
    ctx.fillStyle = '#38bdf8';
    ctx.font = '700 9px "JetBrains Mono", monospace';
    ctx.fillText('KGRR', kgrrPos.x + 16, kgrrPos.y + 3);

    // Plot 49418 Home Marker (42.8836, -85.7606)
    const homePos = latLonToRadar(42.8836, -85.7606);
    ctx.fillStyle = '#f59e0b';
    ctx.beginPath();
    ctx.arc(homePos.x, homePos.y, 3.5, 0, Math.PI * 2);
    ctx.fill();

    // Rotating radar sweep line
    state.radarSweepDeg = (state.radarSweepDeg + 1.4) % 360;
    const sweepRad = ((state.radarSweepDeg - 90) * Math.PI) / 180;
    ctx.save();
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.55)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(sweepRad) * maxR, cy + Math.sin(sweepRad) * maxR);
    ctx.stroke();
    ctx.restore();

    // Plot live aircraft blips
    state.blipHitboxes = [];
    state.flights.forEach((f, idx) => {
      const pos = latLonToRadar(f.lat, f.lon);
      const distFromCenter = Math.hypot(pos.x - cx, pos.y - cy);
      if (distFromCenter > maxR - 4) return;

      const isSelected = idx === state.selectedIndex;
      const blipColor =
        f.squawk === '7700'
          ? '#ef4444'
          : isSelected
            ? '#f59e0b'
            : f.dest_iata === 'GRR' || f.origin_iata === 'GRR'
              ? '#38bdf8'
              : '#10b981';

      // Heading velocity vector line
      const trkRad = ((f.track_deg - 90) * Math.PI) / 180;
      const vecLen = Math.min(22, Math.max(8, f.ground_speed_kts / 22));
      ctx.strokeStyle = blipColor;
      ctx.lineWidth = isSelected ? 2 : 1.2;
      ctx.beginPath();
      ctx.moveTo(pos.x, pos.y);
      ctx.lineTo(pos.x + Math.cos(trkRad) * vecLen, pos.y + Math.sin(trkRad) * vecLen);
      ctx.stroke();

      // Aircraft target square / ring
      ctx.fillStyle = blipColor;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, isSelected ? 5 : 3.2, 0, Math.PI * 2);
      ctx.fill();

      if (isSelected) {
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 9, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Callsign label for top or selected flights
      if (isSelected || idx < 6) {
        ctx.fillStyle = isSelected ? '#f59e0b' : '#cbd5e1';
        ctx.font = isSelected ? '700 10px "JetBrains Mono", monospace' : '600 9px "JetBrains Mono", monospace';
        ctx.textAlign = 'left';
        ctx.fillText(f.flight_number, pos.x + 8, pos.y - 3);
      }

      state.blipHitboxes.push({ x: pos.x, y: pos.y, index: idx });
    });
  }

  // --- DOM COMPANION UPDATES ---
  function updateSpotterAndTableUI() {
    const countBadge = document.getElementById('radar-count-badge');
    if (countBadge) countBadge.textContent = `${state.flights.length} ACFT`;

    const current = state.flights[state.selectedIndex];
    const phaseBadge = document.getElementById('spotter-phase-badge');
    const photoImg = document.getElementById('aircraft-photo');
    const photoFallback = document.getElementById('photo-fallback');
    const blueprintLabel = document.getElementById('blueprint-plane-label');
    const fallbackCaption = document.getElementById('photo-fallback-caption');

    // Update active filter tag on housing
    const filterTag = document.getElementById('active-filter-tag');
    if (filterTag) {
      filterTag.textContent = `FILTER: ${OPERATOR_LABELS[state.airlineFilter] || 'ALL AIRLINES'}`;
    }

    // Update live counts on popover chips
    document.querySelectorAll('[data-count-for]').forEach((badge) => {
      const key = badge.dataset.countFor;
      const val = state.operatorCounts[key] ?? 0;
      badge.textContent = String(val);
    });

    // Render table rows
    const tbody = document.getElementById('flight-table-body');
    if (tbody) {
      tbody.innerHTML = '';
      if (state.flights.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td colspan="7" class="empty-cell">No matching aircraft in range for <strong>${OPERATOR_LABELS[state.airlineFilter] || state.airlineFilter}</strong>. Try expanding scan radius or switching to All Traffic.</td>`;
        tbody.appendChild(tr);
      } else {
        state.flights.forEach((f, idx) => {
          const tr = document.createElement('tr');
          if (idx === state.selectedIndex) tr.classList.add('is-selected');

          const isKgrr = f.origin_iata === 'GRR' || f.dest_iata === 'GRR';
          const routeHtml = isKgrr
            ? `<span class="kgrr-pill">${f.origin_iata} &rarr; ${f.dest_iata}</span>`
            : `${f.origin_iata} &rarr; ${f.dest_iata}`;

          const isGa = f.operator_group === 'GA_PRIVATE';
          const opShort = isGa ? 'Private / GA' : (f.airline_name || f.airline_icao).slice(0, 18);
          const freqMhz = f.atc?.frequency_mhz || '128.400';
          const liveAtcUrl = f.atc?.liveatc_url || 'https://www.liveatc.net/search/?icao=KGRR';

          tr.innerHTML = `
            <td><strong>${f.flight_number}</strong></td>
            <td><span class="op-tag ${isGa ? 'ga' : ''}">${opShort}</span></td>
            <td>${routeHtml}</td>
            <td>${f.type_code}</td>
            <td>${f.altitude_ft.toLocaleString()}</td>
            <td><a class="table-freq-link" href="${liveAtcUrl}" target="_blank" rel="noopener noreferrer" aria-label="Listen to ${freqMhz} MHz on LiveATC">🎧 ${freqMhz}</a></td>
            <td>${f.distance_mi} mi • ${f.bearing_cardinal} ${Math.round(f.elevation_deg)}°</td>
          `;
          tr.addEventListener('click', (e) => {
            if (e.target.closest('a')) return;
            state.selectedIndex = idx;
            state.lastCycleTime = performance.now();
            updateSpotterAndTableUI();
          });
          tbody.appendChild(tr);
        });
      }
    }

    if (!current) {
      if (phaseBadge) phaseBadge.textContent = 'IDLE';
      if (photoImg) photoImg.hidden = true;
      if (photoFallback) photoFallback.hidden = false;
      if (blueprintLabel) blueprintLabel.textContent = 'KGRR';
      return;
    }

    if (phaseBadge) phaseBadge.textContent = current.phase_badge;
    document.getElementById('spotter-reg').textContent = `${current.registration} • ${current.airline_name}`;
    document.getElementById('spotter-model').textContent = current.aircraft_model;

    if (current.photo_url) {
      photoImg.src = current.photo_url;
      photoImg.alt = `${current.airline_name} ${current.aircraft_model} (${current.registration})`;
      photoImg.hidden = false;
      photoFallback.hidden = true;
    } else {
      photoImg.hidden = true;
      photoFallback.hidden = false;
      blueprintLabel.textContent = `${current.type_code} // ${current.flight_number}`;
      fallbackCaption.textContent = `${current.airline_name} • ${current.aircraft_model}`;
    }

    document.getElementById('observer-coords-label').textContent = `From ${state.observer.name}`;
    document.getElementById('look-bearing').textContent = `${String(current.bearing_deg).padStart(3, '0')}° ${current.bearing_cardinal}`;
    document.getElementById('look-elevation').textContent = `${current.elevation_deg}° UP`;
    document.getElementById('look-distance').textContent = `${current.distance_mi} MI (${current.distance_nm} NM)`;
    document.getElementById('look-callsign').textContent = current.radio_callsign ? `"${current.radio_callsign}"` : current.callsign;

    if (current.atc) {
      document.getElementById('atc-freq-mhz').textContent = `${current.atc.frequency_mhz} MHz`;
      document.getElementById('atc-uhf-mhz').textContent = `UHF ${current.atc.uhf_mhz}`;
      document.getElementById('atc-agency').textContent = current.atc.agency;
      document.getElementById('atc-handoff').textContent = current.atc.handoff;
      const liveLink = document.getElementById('liveatc-link');
      if (liveLink) {
        liveLink.href = current.atc.liveatc_url;
      }
      const rrLink = document.getElementById('radioref-link');
      if (rrLink) {
        rrLink.href = current.atc.radioref_url;
      }
    }

    document.getElementById('detail-origin').textContent = `${current.origin_iata} (${current.origin_city})`;
    document.getElementById('detail-dest').textContent = `${current.dest_iata} (${current.dest_city})`;
    const vsSign = current.vertical_rate_fpm > 0 ? '+' : '';
    document.getElementById('detail-alt').textContent = `${current.altitude_ft.toLocaleString()} ft (${vsSign}${current.vertical_rate_fpm} fpm)`;
    document.getElementById('detail-spd').textContent = `${current.ground_speed_kts} kts (${current.ground_speed_mph} mph) • ${current.track_deg}°`;
  }

  const BASE_POLL_MS = 5000;
  const MAX_POLL_MS = 60000;
  let pollFailures = 0;
  let pollTimerId = null;

  function scheduleNextPoll(delayMs) {
    if (pollTimerId) clearTimeout(pollTimerId);
    pollTimerId = setTimeout(async () => {
      if (!document.hidden) {
        await fetchFlights();
      } else {
        scheduleNextPoll(BASE_POLL_MS);
      }
    }, delayMs);
  }

  async function fetchFlights() {
    try {
      const params = new URLSearchParams({
        location: state.location,
        airport: state.airport,
        radius_nm: String(state.radiusNm),
        filter_mode: state.filterMode,
        airline_filter: state.airlineFilter,
        sim_mode: state.simMode,
      });
      const res = await fetch(`/api/flights?${params.toString()}`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();

      // Reset exponential backoff on success
      pollFailures = 0;
      const pip = document.getElementById('live-pip');
      if (pip) {
        pip.style.background = '#10b981';
        pip.style.boxShadow = '0 0 10px #10b981';
      }

      // Keep locked aircraft selected by ID if possible
      const prevSelectedId = state.flights[state.selectedIndex]?.id;
      state.flights = data.flights || [];
      state.operatorCounts = data.operator_counts || {};
      state.observer = data.observer || state.observer;

      const headerBadge = document.getElementById('header-sub-badge');
      if (headerBadge && state.observer) {
        const apIcao = state.observer.airport_icao || state.airport;
        headerBadge.textContent = `${state.observer.id} // ${apIcao}`;
      }

      if (prevSelectedId) {
        const foundIdx = state.flights.findIndex((f) => f.id === prevSelectedId);
        if (foundIdx !== -1) {
          state.selectedIndex = foundIdx;
        } else if (state.selectedIndex >= state.flights.length) {
          state.selectedIndex = 0;
        }
      } else {
        state.selectedIndex = 0;
      }

      const statusText = document.getElementById('feed-status-text');
      if (statusText) {
        const filterSuffix = state.airlineFilter !== 'all' ? ` • ${OPERATOR_LABELS[state.airlineFilter]}` : '';
        statusText.textContent = `${data.source} • ${state.flights.length} aircraft (${state.radiusNm} NM)${filterSuffix}`;
      }
      const pillStatus = document.getElementById('floating-pill-status');
      if (pillStatus) {
        pillStatus.textContent = `${state.observer.id} • ${state.flights.length} ACFT`;
      }
      const badge = document.getElementById('last-updated-badge');
      if (badge) {
        badge.textContent = new Date().toLocaleTimeString();
      }

      updateSpotterAndTableUI();
      scheduleNextPoll(BASE_POLL_MS);
    } catch (err) {
      pollFailures += 1;
      const backoffMs = Math.min(MAX_POLL_MS, BASE_POLL_MS * Math.pow(2, pollFailures - 1));
      console.warn(`Flight fetch error (attempt #${pollFailures}, backing off ${backoffMs / 1000}s):`, err);

      const pip = document.getElementById('live-pip');
      if (pip) {
        pip.style.background = '#f59e0b';
        pip.style.boxShadow = '0 0 10px #f59e0b';
      }
      const statusText = document.getElementById('feed-status-text');
      if (statusText) {
        statusText.textContent = `FEED RETRY BACKOFF (${Math.round(backoffMs / 1000)}s) • Showing last known positions`;
      }
      scheduleNextPoll(backoffMs);
    }
  }

  async function fetchWeather() {
    try {
      const res = await fetch(`/api/weather?station=${encodeURIComponent(state.airport)}`);
      if (!res.ok) return;
      const data = await res.json();
      state.weather = data;

      const catBadge = document.getElementById('metar-cat-badge');
      const rawText = document.getElementById('metar-raw-text');
      if (catBadge) {
        catBadge.textContent = data.flight_category;
        catBadge.className = `vfr-badge ${data.flight_category.toLowerCase()}`;
      }
      if (rawText) {
        rawText.textContent = `${data.raw_metar} (${data.temp_f}°F)`;
      }
    } catch (err) {
      console.error('Weather fetch error:', err);
    }
  }

  // Animation loop (30fps for smooth LED ticker & radar sweep)
  function animate(now) {
    if (!state.isLocked && state.flights.length > 1) {
      if (now - state.lastCycleTime >= state.cycleIntervalMs) {
        state.selectedIndex = (state.selectedIndex + 1) % state.flights.length;
        state.lastCycleTime = now;
        updateSpotterAndTableUI();
      }
    }

    composeMatrixFrame(now);
    renderMatrixToCanvas();
    renderRadarScope();
    requestAnimationFrame(animate);
  }

  function setBarCollapsed(collapsed) {
    document.body.classList.toggle('bar-collapsed', collapsed);
    const pill = document.getElementById('floating-kiosk-pill');
    if (pill) {
      pill.hidden = !collapsed;
    }
  }

  function setAirlineFilter(value) {
    state.airlineFilter = value;
    state.selectedIndex = 0;

    const selectEl = document.getElementById('airline-select');
    if (selectEl && selectEl.value !== value) {
      selectEl.value = value;
    }

    document.querySelectorAll('.airline-chip').forEach((chip) => {
      chip.classList.toggle('is-active', chip.dataset.airline === value);
    });

    fetchFlights();
  }

  function bindControls() {
    const zipInput = document.getElementById('zip-input');
    const airportInput = document.getElementById('airport-input');

    // Location preset buttons (49418 vs KGRR)
    document.querySelectorAll('.seg-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.seg-btn').forEach((b) => b.classList.remove('is-active'));
        btn.classList.add('is-active');
        state.location = btn.dataset.loc;
        state.airport = btn.dataset.airport || 'KGRR';
        if (zipInput) zipInput.value = state.location;
        if (airportInput) airportInput.value = state.airport;
        fetchFlights();
        fetchWeather();
      });
    });

    // Editable ZIP / Location and Airport ICAO Form
    const locForm = document.getElementById('location-form');
    locForm?.addEventListener('submit', (e) => {
      e.preventDefault();
      const newLoc = (zipInput?.value || '49418').trim().toUpperCase();
      const newAp = (airportInput?.value || 'KGRR').trim().toUpperCase();
      state.location = newLoc;
      state.airport = newAp;
      state.selectedIndex = 0;
      document.querySelectorAll('.seg-btn').forEach((b) => {
        b.classList.toggle('is-active', b.dataset.loc === newLoc && (b.dataset.airport || 'KGRR') === newAp);
      });
      fetchFlights();
      fetchWeather();
    });

    // Airline / Craft filter (inline select + popover chips)
    document.getElementById('airline-select')?.addEventListener('change', (e) => {
      setAirlineFilter(e.target.value);
    });

    document.querySelectorAll('.airline-chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        setAirlineFilter(chip.dataset.airline);
      });
    });

    // Collapsible Top Bar & Auto-Collapse in Fullscreen Kiosk Mode
    document.getElementById('collapse-bar-btn')?.addEventListener('click', () => {
      setBarCollapsed(true);
    });

    document.getElementById('expand-bar-btn')?.addEventListener('click', () => {
      setBarCollapsed(false);
    });

    document.addEventListener('fullscreenchange', () => {
      const isFs = Boolean(document.fullscreenElement);
      setBarCollapsed(isFs);
      const kioskBtn = document.getElementById('kiosk-btn');
      if (kioskBtn) {
        kioskBtn.textContent = isFs ? 'Exit Fullscreen' : 'Fullscreen Kiosk';
      }
    });

    document.getElementById('radius-select')?.addEventListener('change', (e) => {
      state.radiusNm = Number(e.target.value);
      fetchFlights();
    });

    document.getElementById('filter-select')?.addEventListener('change', (e) => {
      state.filterMode = e.target.value;
      state.selectedIndex = 0;
      fetchFlights();
    });

    document.getElementById('palette-select')?.addEventListener('change', (e) => {
      state.palette = e.target.value;
    });

    document.getElementById('sim-select')?.addEventListener('change', (e) => {
      state.simMode = e.target.value;
      state.selectedIndex = 0;
      fetchFlights();
    });

    document.getElementById('prev-flight-btn')?.addEventListener('click', () => {
      if (!state.flights.length) return;
      state.selectedIndex = (state.selectedIndex - 1 + state.flights.length) % state.flights.length;
      state.lastCycleTime = performance.now();
      updateSpotterAndTableUI();
    });

    document.getElementById('next-flight-btn')?.addEventListener('click', () => {
      if (!state.flights.length) return;
      state.selectedIndex = (state.selectedIndex + 1) % state.flights.length;
      state.lastCycleTime = performance.now();
      updateSpotterAndTableUI();
    });

    const lockBtn = document.getElementById('toggle-lock-btn');
    const cycleInd = document.getElementById('cycle-indicator');
    lockBtn?.addEventListener('click', () => {
      state.isLocked = !state.isLocked;
      lockBtn.classList.toggle('is-locked', state.isLocked);
      lockBtn.textContent = state.isLocked ? 'Unlock Flight' : 'Lock Flight';
      if (cycleInd) {
        cycleInd.textContent = state.isLocked ? 'LOCKED ON TARGET' : 'AUTO-CYCLE: ON (8s)';
      }
    });

    document.getElementById('kiosk-btn')?.addEventListener('click', () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen().catch(() => {});
      }
    });

    // Click aircraft blip on radar canvas to select it
    const radarCanvas = document.getElementById('radar-canvas');
    radarCanvas?.addEventListener('click', (e) => {
      const rect = radarCanvas.getBoundingClientRect();
      const scaleX = radarCanvas.width / rect.width;
      const scaleY = radarCanvas.height / rect.height;
      const clickX = (e.clientX - rect.left) * scaleX;
      const clickY = (e.clientY - rect.top) * scaleY;

      let closest = null;
      let minDist = 18;
      for (const hb of state.blipHitboxes) {
        const d = Math.hypot(clickX - hb.x, clickY - hb.y);
        if (d < minDist) {
          minDist = d;
          closest = hb;
        }
      }
      if (closest) {
        state.selectedIndex = closest.index;
        state.lastCycleTime = performance.now();
        updateSpotterAndTableUI();
      }
    });
  }

  // Initialize
  bindControls();
  fetchFlights();
  fetchWeather();
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      fetchFlights();
    }
  });
  setInterval(fetchWeather, 120000);
  requestAnimationFrame(animate);
})();
