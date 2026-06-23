/**
 * PaySentinelIQ — WebSocket Browser Test Script
 *
 * Instructions:
 * 1. Open Chrome/Firefox DevTools (F12)
 * 2. Go to the Console tab
 * 3. Copy and paste the function below
 * 4. Run: testWS()
 *
 * The script will:
 * - Connect to the WebSocket with your stored JWT token
 * - Test ping/pong
 * - Display all received messages
 * - Show connection status
 */

async function testWS(wsUrl) {
  const WS_URL =
    wsUrl ||
    window.__NEXT_PUBLIC_WS_URL ||
    "wss://paysentineliq-production.up.railway.app/ws/notifications";

  // Get JWT from Zustand store (localStorage)
  const getToken = () => {
    try {
      const stored = localStorage.getItem("psi-auth");
      if (stored) {
        const parsed = JSON.parse(stored);
        const { state } = parsed;
        return state?.token || null;
      }
    } catch {}
    return null;
  };

  const token = getToken();
  const url = token ? `${WS_URL}?token=${encodeURIComponent(token)}` : WS_URL;

  console.log("=".repeat(60));
  console.log("📡 PaySentinelIQ WebSocket Test");
  console.log("=".repeat(60));
  console.log(`URL:     ${url.slice(0, 100)}...`);
  console.log(`Token:   ${token ? "✅ Present" : "❌ Missing"}`);
  console.log(`Time:    ${new Date().toISOString()}`);
  console.log("");

  return new Promise((resolve) => {
    const ws = new WebSocket(url);
    const results = [];
    let startTime = Date.now();

    function log(emoji, msg, data) {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      console.log(`[+${elapsed}s] ${emoji} ${msg}`);
      if (data) {
        console.log("       ", data);
        results.push({ time: elapsed, type: msg, data });
      }
    }

    // --- Connection opened ---
    ws.onopen = () => {
      log("✅", "CONNECTED — WebSocket handshake successful");
      log("📤", "Sending ping...");
      ws.send("ping");
    };

    // --- Message received ---
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        switch (msg.type) {
          case "connected":
            log("🔗", `CONNECTED to channel: ${msg.channel} (user: ${msg.user_id})`, msg);
            break;
          case "pong":
            log("🏓", "PONG received — heartbeat OK", msg);
            // After successful ping/pong, wait 2s then close
            setTimeout(() => {
              log("🔒", "Closing connection gracefully...");
              ws.close(1000, "Test completed");
            }, 2000);
            break;
          case "new_notification":
            log("🔔", "NEW NOTIFICATION received!", msg);
            break;
          case "fraud_alert":
            log("🚨", "FRAUD ALERT received!", msg);
            break;
          default:
            log("📨", `Message: ${msg.type}`, msg);
        }
      } catch (e) {
        log("⚠️", `Raw message (non-JSON): ${event.data}`);
      }
    };

    // --- Error ---
    ws.onerror = (err) => {
      log("❌", "WebSocket error", err);
    };

    // --- Connection closed ---
    ws.onclose = (event) => {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      console.log("");
      console.log("=".repeat(60));
      console.log(`📊 Test Results (${elapsed}s)`);
      console.log("=".repeat(60));
      console.log(`Code:   ${event.code}`);
      console.log(`Reason: ${event.reason || "(none)"}`);
      console.log(`Clean:  ${event.wasClean ? "✅" : "❌"}`);

      if (event.code === 4001) {
        console.log(
          "❌ AUTH FAILED — The server rejected the connection with code 4001.\n" +
            "   This means your JWT token is missing, expired, or invalid.\n" +
            "   Try logging out and logging back in to get a fresh token."
        );
      } else if (event.code === 1000) {
        console.log("✅ TEST PASSED — WebSocket connection successful!");
      } else if (event.code === 1006) {
        console.log(
          "❌ ABNORMAL CLOSURE (code 1006) — Possible causes:\n" +
            "   1. RateLimitMiddleware blocking the Upgrade handshake\n" +
            "   2. Multiple Uvicorn workers routing to wrong process\n" +
            "   3. Network/proxy issue (check Railway logs)"
        );
      }

      resolve(results);
    };
  });
}

// Auto-run hint:
console.log('Run: testWS()');
console.log('Or with custom URL: testWS("wss://paysentineliq-production.up.railway.app/ws/notifications")');
