/**
 * agent.js — Vana Sethu Global AI Assistant
 * Floating chat widget present on every panel.
 * Understands natural language, answers questions about the platform,
 * navigates to the correct page, and spotlights Bengaluru localities on the map.
 */

(function () {
  "use strict";

  // ── Bengaluru places database (100+ localities with coordinates + description) ─
  const BLR_PLACES = [
    // Central
    { name: "Indiranagar",        lat: 12.9784, lng: 77.6408, info: "Trendy residential & commercial hub on 100ft Road, known for cafes, pubs and boutiques." },
    { name: "Koramangala",        lat: 12.9352, lng: 77.6245, info: "Bengaluru's startup capital — dense, vibrant, home to many IT firms and restaurants." },
    { name: "MG Road",            lat: 12.9752, lng: 77.6093, info: "The iconic commercial spine of central Bengaluru — shopping malls, offices and metro." },
    { name: "Brigade Road",       lat: 12.9719, lng: 77.6090, info: "Prime shopping and entertainment street in central Bengaluru." },
    { name: "Cubbon Park",        lat: 12.9763, lng: 77.5929, info: "120-acre green lung of Bengaluru — century-old trees, jogging trails, museums." },
    { name: "Lalbagh",            lat: 12.9507, lng: 77.5848, info: "240-acre botanical garden founded by Hyder Ali — famous glasshouse and tree heritage." },
    { name: "UB City",            lat: 12.9718, lng: 77.5967, info: "Luxury mixed-use complex in the heart of Bengaluru's CBD." },
    { name: "Vidhana Soudha",     lat: 12.9794, lng: 77.5908, info: "Seat of the Karnataka state legislature — iconic granite neo-Dravidian architecture." },
    { name: "Shivajinagar",       lat: 12.9850, lng: 77.6010, info: "Major commercial and bus terminus area in central Bengaluru." },
    { name: "Vasanth Nagar",      lat: 12.9890, lng: 77.5943, info: "Upscale residential neighbourhood adjacent to Cubbon Park." },

    // North
    { name: "Yelahanka",          lat: 13.1007, lng: 77.5963, info: "Satellite town in north Bengaluru — fast-growing residential corridor near airport." },
    { name: "Hebbal",             lat: 13.0358, lng: 77.5970, info: "Major junction in north Bengaluru known for the Hebbal flyover and Nagavara Lake." },
    { name: "Jakkur",             lat: 13.0695, lng: 77.5940, info: "Residential area in north Bengaluru near Jakkur aerodrome." },
    { name: "Sahakara Nagar",     lat: 13.0570, lng: 77.5810, info: "Planned residential layout in north Bengaluru with good green cover." },
    { name: "Bangalore Airport",  lat: 13.1979, lng: 77.7063, info: "Kempegowda International Airport — main aviation gateway to Bengaluru." },
    { name: "Devanahalli",        lat: 13.2457, lng: 77.7169, info: "Historic town north of Bengaluru, birthplace of Tipu Sultan, near the airport." },
    { name: "Byatarayanapura",    lat: 13.0716, lng: 77.5577, info: "Densely populated area in north Bengaluru." },
    { name: "RT Nagar",           lat: 13.0220, lng: 77.5940, info: "Raghavendra Nagar — mixed residential and commercial area in north Bengaluru." },
    { name: "Dollars Colony",     lat: 13.0450, lng: 77.5820, info: "Premium residential area in Bengaluru's north corridor." },
    { name: "MS Ramaiah",         lat: 13.0133, lng: 77.5588, info: "Education hub in north Bengaluru — home to MS Ramaiah Institute and hospitals." },

    // South
    { name: "Jayanagar",          lat: 12.9252, lng: 77.5831, info: "One of Asia's largest planned residential areas — famous for Jayanagar 4th Block shopping street." },
    { name: "JP Nagar",           lat: 12.9077, lng: 77.5856, info: "Janapada Pura — large south Bengaluru residential township with parks and malls." },
    { name: "Banashankari",       lat: 12.9256, lng: 77.5465, info: "Named after the Banashankari temple — well-established south Bengaluru neighbourhood." },
    { name: "BTM Layout",         lat: 12.9166, lng: 77.6101, info: "Byrasandra, Tavarekere, Madiwala — densely populated south Bengaluru area popular with techies." },
    { name: "HSR Layout",         lat: 12.9116, lng: 77.6474, info: "Handsome, well-planned south-east Bengaluru suburb — popular startup neighbourhood." },
    { name: "Electronic City",    lat: 12.8399, lng: 77.6770, info: "Bengaluru's oldest IT park — hosts Infosys, Wipro, TCS and hundreds of tech firms." },
    { name: "Bommanahalli",       lat: 12.8910, lng: 77.6395, info: "South-east Bengaluru suburb — rapidly urbanizing with many IT campuses." },
    { name: "Begur",              lat: 12.8692, lng: 77.6346, info: "South Bengaluru area with historical Begur fort and Panchayat." },
    { name: "Gottigere",          lat: 12.8572, lng: 77.5962, info: "South Bengaluru locality near NICE Road." },
    { name: "Kanakapura Road",    lat: 12.8903, lng: 77.5523, info: "Major arterial road in south Bengaluru lined with new gated communities." },
    { name: "Kumaraswamy Layout", lat: 12.9079, lng: 77.5570, info: "South Bengaluru residential area adjacent to Banashankari." },
    { name: "Padmanabhanagar",    lat: 12.9183, lng: 77.5587, info: "Residential area in south Bengaluru with good civic infrastructure." },
    { name: "Bilekahalli",        lat: 12.8966, lng: 77.6141, info: "South Bengaluru suburb along Bannerghatta Road." },
    { name: "Arekere",            lat: 12.8812, lng: 77.6179, info: "South Bengaluru area near NICE Road and Bannerghatta Road junction." },

    // East
    { name: "Whitefield",         lat: 12.9698, lng: 77.7499, info: "Major IT and residential suburb in east Bengaluru — ITPL, Prestige tech parks." },
    { name: "ITPL",               lat: 12.9856, lng: 77.7272, info: "International Tech Park — one of Bengaluru's first and largest IT campuses." },
    { name: "Marathahalli",       lat: 12.9591, lng: 77.6974, info: "Busy east Bengaluru junction — commercial hub serving many IT corridors." },
    { name: "KR Puram",           lat: 13.0063, lng: 77.6916, info: "Krishna Rajendra Puram — east Bengaluru junction with major railway station." },
    { name: "Varthur",            lat: 12.9397, lng: 77.7472, info: "East Bengaluru area known for Varthur Lake and rapid IT-driven development." },
    { name: "Sarjapur Road",      lat: 12.9075, lng: 77.6879, info: "South-east Bengaluru growth corridor — many tech campuses and residential projects." },
    { name: "Bellandur",          lat: 12.9254, lng: 77.6763, info: "East Bengaluru area on Outer Ring Road — major tech hub and residential zone." },
    { name: "Carmelaram",         lat: 12.9177, lng: 77.7120, info: "East Bengaluru residential area near Sarjapur Road." },
    { name: "Hagadur",            lat: 12.9889, lng: 77.7336, info: "East Bengaluru locality near Whitefield." },
    { name: "Mahadevapura",       lat: 12.9982, lng: 77.6987, info: "East Bengaluru suburb — major IT zone on Outer Ring Road." },
    { name: "Brookefield",        lat: 12.9797, lng: 77.7147, info: "East Bengaluru residential area popular with IT professionals." },

    // West
    { name: "Rajajinagar",        lat: 12.9918, lng: 77.5520, info: "West Bengaluru residential neighbourhood known for shopping and temples." },
    { name: "Malleswaram",        lat: 13.0035, lng: 77.5712, info: "One of Bengaluru's oldest neighbourhoods — heritage lanes, Mantri Mall, Sankey Tank." },
    { name: "Yeshwanthpur",       lat: 13.0291, lng: 77.5399, info: "Major junction in west Bengaluru — ISRO HQ, Orion Mall, railway terminal." },
    { name: "Peenya",             lat: 13.0310, lng: 77.5172, info: "Major industrial estate in west Bengaluru — largest in South Asia." },
    { name: "Vijayanagar",        lat: 12.9718, lng: 77.5313, info: "West Bengaluru residential area with large population and good connectivity." },
    { name: "Nagarbhavi",         lat: 12.9627, lng: 77.5137, info: "West Bengaluru area near NIMHANS — housing layouts and educational institutions." },
    { name: "Kengeri",            lat: 12.9074, lng: 77.4820, info: "West Bengaluru satellite town — terminus of the metro's west line." },
    { name: "Mysore Road",        lat: 12.9500, lng: 77.5050, info: "Major arterial road heading west from Bengaluru towards Mysuru." },
    { name: "Nayandahalli",       lat: 12.9510, lng: 77.5203, info: "West Bengaluru industrial and residential area." },
    { name: "Basaveshwara Nagar", lat: 12.9916, lng: 77.5313, info: "West Bengaluru residential area with good parks and civic amenities." },

    // Outer Ring Road & Tech Corridor
    { name: "Outer Ring Road",    lat: 12.9549, lng: 77.7001, info: "ORR — Bengaluru's outer expressway ring housing hundreds of IT campuses." },
    { name: "Manyata Tech Park",  lat: 13.0481, lng: 77.6228, info: "Largest tech park in Bengaluru — 10,000+ employees from dozens of MNCs." },
    { name: "Bagmane Tech Park",  lat: 12.9980, lng: 77.6472, info: "Major IT campus on CV Raman Nagar Road, east of central Bengaluru." },
    { name: "RMZ Ecospace",       lat: 12.9329, lng: 77.6961, info: "Premium IT park on Sarjapur–Marathahalli Outer Ring Road." },

    // Lakes
    { name: "Ulsoor Lake",        lat: 12.9825, lng: 77.6213, info: "Central Bengaluru lake — boating, jogging and picnicking. Area: ~120 acres." },
    { name: "Hebbal Lake",        lat: 13.0427, lng: 77.5918, info: "North Bengaluru lake — flamingo sightings, bird sanctuary status." },
    { name: "Sankey Tank",        lat: 13.0054, lng: 77.5751, info: "Historic 1882 reservoir in Malleswaram — popular jogging trail." },
    { name: "Bellandur Lake",     lat: 12.9272, lng: 77.6701, info: "Largest lake in Bengaluru — severely stressed by urban runoff." },
    { name: "Varthur Lake",       lat: 12.9376, lng: 77.7391, info: "Second-largest lake in Bengaluru — connected to Bellandur Lake." },
    { name: "Agara Lake",         lat: 12.9076, lng: 77.6473, info: "Rejuvenated lake in HSR Layout with walking path and birdlife." },
    { name: "Kaikondrahalli Lake",lat: 12.9204, lng: 77.6763, info: "Sarjapur Road lake — community-led restoration success story." },
    { name: "Jakkur Lake",        lat: 13.0697, lng: 77.5953, info: "North Bengaluru lake popular with migratory birds." },

    // Institutions & Landmarks
    { name: "IISc",               lat: 13.0211, lng: 77.5680, info: "Indian Institute of Science — Asia's top research university, sprawling green campus." },
    { name: "ISRO",               lat: 13.0330, lng: 77.5651, info: "Indian Space Research Organisation HQ — Bengaluru's most iconic science institution." },
    { name: "HAL",                lat: 12.9627, lng: 77.6688, info: "Hindustan Aeronautics Limited — Bengaluru's aerospace hub and heritage airfield." },
    { name: "Namma Metro",        lat: 12.9777, lng: 77.5918, info: "Bengaluru's rapid transit network — Purple and Green lines criss-cross the city." },
    { name: "City Railway Station",lat: 12.9775, lng: 77.5713, info: "Krantivira Sangolli Rayanna Station — Bengaluru's main railway terminus." },
    { name: "BMTC",               lat: 12.9772, lng: 77.5918, info: "Bengaluru Metropolitan Transport Corporation — 6,000+ buses serving the city." },
    { name: "Kanteerava Stadium", lat: 12.9713, lng: 77.5944, info: "Main multi-sport stadium in Bengaluru — athletics, football and cricket." },
    { name: "Bangalore Palace",   lat: 12.9988, lng: 77.5922, info: "Tudor-style royal palace built in 1878 — concerts, exhibitions and history tours." },
    { name: "Tipu Sultan's Fort", lat: 12.9607, lng: 77.5760, info: "18th-century fort built by Hyder Ali and expanded by Tipu Sultan in Bengaluru." },

    // More popular areas
    { name: "Frazer Town",        lat: 12.9870, lng: 77.6165, info: "Multicultural neighbourhood in central-east Bengaluru — food, churches and mosques." },
    { name: "Cox Town",           lat: 12.9893, lng: 77.6213, info: "Residential area in central-east Bengaluru, adjacent to Frazer Town." },
    { name: "Richmond Town",      lat: 12.9568, lng: 77.6049, info: "Upscale area in central Bengaluru — consulates, bungalows and cafes." },
    { name: "Sadashivanagar",     lat: 13.0031, lng: 77.5802, info: "Elite residential area next to Sankey Tank — embassy zone and bungalows." },
    { name: "Seshadripuram",      lat: 12.9970, lng: 77.5731, info: "Central Bengaluru residential area near City Railway Station." },
    { name: "Gandhinagar",        lat: 12.9777, lng: 77.5700, info: "Commercial area near City Railway Station known for wholesale markets." },
    { name: "Chamrajpet",         lat: 12.9607, lng: 77.5603, info: "South-west of central Bengaluru — mixed residential and commercial." },
    { name: "Basavanagudi",       lat: 12.9426, lng: 77.5751, info: "One of Bengaluru's oldest localities — Dodda Ganesha temple, Bull Temple Road." },
    { name: "Gavipuram",          lat: 12.9358, lng: 77.5722, info: "South Bengaluru residential area adjacent to Basavanagudi." },
    { name: "Mysuru",             lat: 12.2958, lng: 76.6394, info: "City of palaces — 160 km SW of Bengaluru, heritage, culture and silk." },
    { name: "Tumkur",             lat: 13.3379, lng: 77.1173, info: "Satellite city 70 km north of Bengaluru — industrial and agricultural hub." },
  ];

  // ── Build a place lookup (longest-match, full-name priority) ──────────────
  // Words that are common English/platform words — never treat as place names
  const PLACE_STOP_WORDS = new Set([
    "show", "find", "locate", "mark", "map", "here", "this", "that", "tree",
    "ward", "open", "page", "scan", "help", "about", "what", "where", "health",
    "home", "list", "data", "site", "info", "park", "road", "nagar", "layout",
  ]);

  const PLACE_INDEX = new Map();
  BLR_PLACES.forEach(p => {
    PLACE_INDEX.set(p.name.toLowerCase(), p);          // full name always indexed
    p.name.toLowerCase().split(/[\s\-–\/]+/).forEach(word => {
      // Only index single words that are ≥5 chars and not stop-words
      if (word.length >= 5 && !PLACE_STOP_WORDS.has(word)) {
        PLACE_INDEX.set(word, p);
      }
    });
  });

  function detectPlace(text) {
    const t = text.toLowerCase();
    // Sort keys longest-first so "Cubbon Park" beats "park"
    const sorted = [...PLACE_INDEX.keys()].sort((a, b) => b.length - a.length);
    for (const key of sorted) {
      if (t.includes(key)) return PLACE_INDEX.get(key);
    }
    return null;
  }

  // ── Page navigation map ────────────────────────────────────────────────────
  const PAGE_ALIASES = {
    home:      ["home page", "go home", "dashboard page", "main page", "start page", "overview page"],
    map:       ["green cover", "green map", "ward map", "coverage map", "vegetation map", "ndvi", "deficient wards", "green space map"],
    inventory: ["inventory", "tree list", "tree registry", "tree count", "ward trees"],
    health:    ["health scanner", "scan a tree", "diagnose tree", "upload image", "analyse tree", "analyze tree"],
    metrics:   ["metrics", "ai dashboard", "performance dashboard", "rag metrics", "agentic metrics", "guardrail metrics", "llm dashboard"],
    approvals: ["approvals", "pending approvals", "officer approvals"],
  };

  // Explicit navigation verbs that must be present to trigger page nav
  const NAV_VERBS = [
    "go to", "open", "show me the", "navigate to", "take me to",
    "switch to", "i want to see", "bring me to", "head to",
  ];

  // ── Quick answers ──────────────────────────────────────────────────────────
  const QUICK_ANSWERS = [
    {
      match: ["what is vana sethu", "about vana sethu", "what does this do", "explain this app", "what is this"],
      answer: "**Vana Sethu** (ವನ ಸೇತು) means *Bridge to the Forest* in Kannada. It's an AI-powered Smart Urban Tree Platform for Bengaluru that helps BBMP officers, NGOs and citizens monitor, protect and grow the city's urban tree canopy in real time using 4 specialised AI agents and 9 safety guardrail layers.",
    },
    {
      match: ["how many agents", "ai agents", "what agents"],
      answer: "Vana Sethu has **4 AI Agents**:\n1. **Health Agent** — diagnoses tree diseases from images\n2. **Inventory Agent** — manages the full tree registry\n3. **Mapping Agent** — calculates ward-level green cover %\n4. **Dashboard Agent** — orchestrates all agents and answers queries\n\nAll agents run through 9 guardrail layers for safety.",
    },
    {
      match: ["guardrail", "guardrails", "how safe"],
      answer: "Vana Sethu applies **9 guardrail layers** on every request:\n• Input validation & PII masking\n• Tool-call safety checks\n• Output content filtering\n• Data access controls (RBAC)\n• Human-in-the-Loop (HITL) for critical actions\n• Ethics & bias checks\n• Multi-agent loop detection\n• Operational rate limiting\n• Security injection prevention",
    },
    {
      match: ["login", "how to login", "credentials", "demo user", "password"],
      answer: "**Demo credentials:**\n\n👤 Citizen: `citizen@vanasethu.in` / `citizen123`\n🏛️ Officer: `officer@bbmp.gov.in` / `officer123`\n👑 Admin: `admin@bbmp.gov.in` / `admin123`\n\nOfficers and admins can approve health flagging actions.",
    },
    {
      match: ["ward", "how many wards", "bengaluru wards", "bbmp wards"],
      answer: "Vana Sethu monitors **10 key BBMP wards** across Bengaluru, including Yelahanka, Hebbal, Cubbon Park, Electronic City, Jayanagar, Whitefield, Lalbagh, Marathahalli, Malleswaram and Koramangala. Each ward has a live green cover score updated every 30 minutes.",
    },
  ];

  // ── Detect navigation intent — requires a nav verb ────────────────────────
  function detectNavIntent(text) {
    const t = text.toLowerCase();
    const hasVerb = NAV_VERBS.some(v => t.includes(v));
    if (!hasVerb) return null;   // never navigate without an explicit verb
    for (const [panel, aliases] of Object.entries(PAGE_ALIASES)) {
      for (const alias of aliases) {
        if (t.includes(alias)) return panel;
      }
    }
    // Handle plain "go to map / inventory / health / metrics / approvals / home"
    const plainPanels = { map: "map", inventory: "inventory", health: "health", metrics: "metrics", approvals: "approvals", home: "home" };
    for (const [word, panel] of Object.entries(plainPanels)) {
      if (hasVerb && t.includes(word)) return panel;
    }
    return null;
  }

  // ── Detect quick answer ────────────────────────────────────────────────────
  function detectQuickAnswer(text) {
    const t = text.toLowerCase();
    for (const qa of QUICK_ANSWERS) {
      if (qa.match.some(m => t.includes(m))) return qa.answer;
    }
    return null;
  }

  // ── Markdown → HTML (with proper ul/ol wrapping) ──────────────────────────
  function mdToHtml(text) {
    // Bold, italic, code
    let html = text
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/`(.+?)`/g, "<code>$1</code>");

    // Split into lines and process bullets / numbered lists
    const lines = html.split("\n");
    const out = [];
    let inUl = false, inOl = false;

    for (const line of lines) {
      const bullet  = line.match(/^[•\-]\s+(.*)/);
      const numbered = line.match(/^(\d+)\.\s+(.*)/);
      if (bullet) {
        if (!inUl) { out.push("<ul>"); inUl = true; }
        if (inOl)  { out.push("</ol>"); inOl = false; }
        out.push(`<li>${bullet[1]}</li>`);
      } else if (numbered) {
        if (!inOl) { out.push("<ol>"); inOl = true; }
        if (inUl)  { out.push("</ul>"); inUl = false; }
        out.push(`<li>${numbered[2]}</li>`);
      } else {
        if (inUl) { out.push("</ul>"); inUl = false; }
        if (inOl) { out.push("</ol>"); inOl = false; }
        out.push(line ? `<p style="margin:3px 0">${line}</p>` : "");
      }
    }
    if (inUl) out.push("</ul>");
    if (inOl) out.push("</ol>");
    return out.join("");
  }

  // ── Build the widget DOM ───────────────────────────────────────────────────
  function buildWidget() {
    const wrap = document.createElement("div");
    wrap.id = "vs-agent-wrap";
    wrap.innerHTML = `
      <button id="vs-agent-fab" aria-label="Open AI Assistant" title="Ask the Vana Sethu AI">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a9 9 0 0 1 9 9c0 4.6-3.4 8.4-7.8 9.0L12 22l-1.2-2C6.4 19.4 3 15.6 3 11a9 9 0 0 1 9-9z"/>
          <circle cx="9" cy="11" r="1" fill="currentColor" stroke="none"/>
          <circle cx="12" cy="11" r="1" fill="currentColor" stroke="none"/>
          <circle cx="15" cy="11" r="1" fill="currentColor" stroke="none"/>
        </svg>
        <span class="vs-fab-badge" id="vs-fab-badge" style="display:none">1</span>
      </button>

      <div id="vs-agent-panel" role="dialog" aria-label="Vana Sethu AI Assistant" style="display:none">
        <div id="vs-agent-header">
          <div class="vs-header-left">
            <div class="vs-avatar">🌳</div>
            <div>
              <div class="vs-agent-name">Vana Sethu AI</div>
              <div class="vs-agent-status" id="vs-status-dot">● Online</div>
            </div>
          </div>
          <div class="vs-header-actions">
            <button id="vs-clear-btn" title="Clear chat">🗑</button>
            <button id="vs-close-btn" title="Close">✕</button>
          </div>
        </div>

        <div id="vs-messages"></div>

        <div id="vs-suggestions">
          <button class="vs-chip" data-q="Take me to the Green Cover map">🗺 Green Cover Map</button>
          <button class="vs-chip" data-q="Show me Indiranagar on the map">📍 Indiranagar</button>
          <button class="vs-chip" data-q="Show me Cubbon Park on the map">🌳 Cubbon Park</button>
          <button class="vs-chip" data-q="Open the health scanner">🩺 Health Scanner</button>
          <button class="vs-chip" data-q="What is Vana Sethu?">ℹ️ About</button>
          <button class="vs-chip" data-q="Show me Electronic City on the map">💻 Electronic City</button>
        </div>

        <div id="vs-input-row">
          <input id="vs-input" type="text" placeholder="Ask anything or try "show Whitefield on map"…" autocomplete="off" maxlength="300"/>
          <button id="vs-send-btn" aria-label="Send">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(wrap);
  }

  // ── Append a message bubble ────────────────────────────────────────────────
  function appendMsg(role, html, action) {
    const msgs = document.getElementById("vs-messages");
    const div = document.createElement("div");
    div.className = `vs-msg vs-msg-${role}`;

    const bubble = document.createElement("div");
    bubble.className = "vs-bubble";
    bubble.innerHTML = html;

    if (action) {
      const btn = document.createElement("button");
      btn.className = "vs-nav-btn";

      if (action.type === "place") {
        // Place spotlight button — triggers map pin
        btn.textContent = `📍 Show ${action.place.name} on map`;
        btn.onclick = () => {
          closePanel();
          window.spotlightPlace &&
            window.spotlightPlace(action.place.name, action.place.lat, action.place.lng, action.place.info);
        };
      } else {
        // Page navigation button
        const labels = { home: "Home", map: "Green Cover Map", inventory: "Tree Inventory", health: "Health Scanner", metrics: "AI Dashboard", approvals: "Approvals" };
        btn.textContent = `→ Go to ${labels[action.panel] || action.panel}`;
        btn.onclick = () => {
          window.switchPanel && window.switchPanel(action.panel);
          closePanel();
        };
      }
      bubble.appendChild(btn);
    }

    div.appendChild(bubble);
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function appendTyping() {
    const msgs = document.getElementById("vs-messages");
    const div = document.createElement("div");
    div.className = "vs-msg vs-msg-agent";
    div.id = "vs-typing-indicator";
    div.innerHTML = `<div class="vs-bubble vs-typing"><span></span><span></span><span></span></div>`;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function removeTyping() {
    const el = document.getElementById("vs-typing-indicator");
    if (el) el.remove();
  }

  // ── Open / close ───────────────────────────────────────────────────────────
  function openPanel() {
    const panel = document.getElementById("vs-agent-panel");
    panel.style.display = "flex";
    panel.classList.add("vs-panel-open");
    document.getElementById("vs-fab-badge").style.display = "none";
    document.getElementById("vs-input").focus();
  }

  function closePanel() {
    const panel = document.getElementById("vs-agent-panel");
    panel.style.display = "none";
    panel.classList.remove("vs-panel-open");
  }

  // ── Core send logic ────────────────────────────────────────────────────────
  async function sendMessage(text) {
    text = text.trim();
    if (!text) return;

    document.getElementById("vs-input").value = "";
    document.getElementById("vs-suggestions").style.display = "none";
    appendMsg("user", text);
    appendTyping();

    const t = text.toLowerCase();

    // ── 1. Place spotlight — explicit trigger required ─────────────────────
    const PLACE_TRIGGERS = [
      "show me", "where is", "where's", "locate", "find", "point to",
      "mark", "highlight", "map of", "on the map", "on map",
      "in bangalore", "in bengaluru", "show on map",
    ];
    const hasPlaceTrigger = PLACE_TRIGGERS.some(tr => t.includes(tr));
    const place = hasPlaceTrigger ? detectPlace(t) : null;

    if (place) {
      await new Promise(r => setTimeout(r, 500));
      removeTyping();
      appendMsg("agent",
        `Sure! Here's <strong>${place.name}</strong> on the map.<br><em style="font-size:12px;color:#617849">${place.info || ""}</em>`,
        { type: "place", place }
      );
      closePanel();
      window.spotlightPlace && window.spotlightPlace(place.name, place.lat, place.lng, place.info);
      return;
    }

    // ── 2. Quick answers ───────────────────────────────────────────────────
    const quick = detectQuickAnswer(t);
    if (quick) {
      await new Promise(r => setTimeout(r, 600));
      removeTyping();
      const navPanel = detectNavIntent(t);
      appendMsg("agent", mdToHtml(quick), navPanel ? { type: "panel", panel: navPanel } : null);
      return;
    }

    // ── 3. Pure page navigation intent ────────────────────────────────────
    const navPanel = detectNavIntent(t);
    if (navPanel && t.split(" ").length <= 8) {
      await new Promise(r => setTimeout(r, 400));
      removeTyping();
      const labels = { home: "Home", map: "Green Cover Map", inventory: "Tree Inventory", health: "Health Scanner", metrics: "AI Dashboard", approvals: "Approvals" };
      appendMsg("agent", `Taking you to the <strong>${labels[navPanel]}</strong> page!`, { type: "panel", panel: navPanel });
      return;
    }

    // ── 4. Backend /api/assistant for live data ────────────────────────────
    try {
      const res = await fetch(`${window.API || "http://127.0.0.1:5001/api"}/assistant`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text }),
      });
      const data = await res.json();
      removeTyping();

      const reply = data.reply || data.message || "I couldn't find an answer to that.";
      const detectedNav = data.navigate_to || navPanel;
      appendMsg("agent", mdToHtml(reply), detectedNav ? { type: "panel", panel: detectedNav } : null);
    } catch {
      removeTyping();
      appendMsg("agent", "Sorry, I couldn't reach the server right now. Try refreshing the page.", null);
    }
  }

  // ── Wire events ────────────────────────────────────────────────────────────
  function init() {
    buildWidget();

    appendMsg("agent", "Hello! 👋 I'm the <strong>Vana Sethu AI Assistant</strong>.<br>I can answer questions, navigate pages, and <strong>point out any place in Bengaluru on the map</strong> — just ask something like <em>\"show me Indiranagar\"</em> or <em>\"where is Cubbon Park?\"</em>");

    document.getElementById("vs-agent-fab").addEventListener("click", () => {
      const panel = document.getElementById("vs-agent-panel");
      panel.style.display === "none" ? openPanel() : closePanel();
    });

    document.getElementById("vs-close-btn").addEventListener("click", closePanel);

    document.getElementById("vs-clear-btn").addEventListener("click", () => {
      document.getElementById("vs-messages").innerHTML = "";
      document.getElementById("vs-suggestions").style.display = "flex";
      appendMsg("agent", "Chat cleared! Ask me anything, or try <em>\"show Whitefield on the map\"</em>.");
    });

    document.getElementById("vs-send-btn").addEventListener("click", () => {
      sendMessage(document.getElementById("vs-input").value);
    });

    document.getElementById("vs-input").addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage(document.getElementById("vs-input").value);
      }
    });

    document.querySelectorAll(".vs-chip").forEach(chip => {
      chip.addEventListener("click", () => sendMessage(chip.dataset.q));
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
