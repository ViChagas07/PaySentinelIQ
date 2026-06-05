// ============================================================
// PaySentinelIQ — AI Aura Background
// Premium futuristic animated background system
// Layers: dark base → floating blobs → AI network → grid → noise
// ============================================================

"use client";

import { useMemo, useRef, useState, useEffect, useCallback } from "react";
import { motion, useAnimationFrame } from "framer-motion";

// ── Constants ── //
const NODE_COUNT = 42;
const CONNECTION_MAX_DIST = 220; // in VIEWBOX units
const VIEWBOX_SIZE = 1000;
const PULSE_INTERVAL_MIN = 4000; // ms
const PULSE_INTERVAL_MAX = 8000; // ms
const PULSE_PROPAGATION_DELAY = 120; // ms per hop
const NODE_GLOW_DURATION = 1800; // ms

// ── Seeded pseudo-random (deterministic across renders) ── //
function createRng(seed: number) {
  let s = seed | 0;
  return () => {
    s = (s * 1664525 + 1013904223) | 0;
    return (s >>> 0) / 4294967296;
  };
}

// ── Generate node positions ── //
interface Node {
  x: number;
  y: number;
  r: number;
  baseOpacity: number;
}

function generateNodes(count: number): Node[] {
  const rand = createRng(137);
  return Array.from({ length: count }, () => ({
    x: rand() * VIEWBOX_SIZE,
    y: rand() * VIEWBOX_SIZE,
    r: 1.2 + rand() * 2.2,
    baseOpacity: 0.12 + rand() * 0.28,
  }));
}

// ── Generate connections (edges) between nearby nodes ── //
interface Edge {
  from: number;
  to: number;
}

function generateConnections(nodes: Node[], maxDist: number): Edge[] {
  const edges: Edge[] = [];
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const dx = nodes[i].x - nodes[j].x;
      const dy = nodes[i].y - nodes[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < maxDist) {
        edges.push({ from: i, to: j });
      }
    }
  }
  return edges;
}

// ── Build adjacency list for BFS ── //
function buildAdjacency(edges: Edge[], nodeCount: number): number[][] {
  const adj: number[][] = Array.from({ length: nodeCount }, () => []);
  for (const e of edges) {
    adj[e.from].push(e.to);
    adj[e.to].push(e.from);
  }
  return adj;
}

// ── BFS to compute distances from a source node ── //
function computeDistances(adj: number[][], source: number): number[] {
  const dist = new Array<number>(adj.length).fill(-1);
  const queue: number[] = [source];
  dist[source] = 0;
  for (let idx = 0; idx < queue.length; idx++) {
    const u = queue[idx];
    for (const v of adj[u]) {
      if (dist[v] === -1) {
        dist[v] = dist[u] + 1;
        // Limit propagation depth for visual clarity
        if (dist[v] < 6) queue.push(v);
      }
    }
  }
  return dist;
}

// ── Active pulse structure ── //
interface Pulse {
  source: number;
  startTime: number; // performance.now() at start
  distances: number[]; // pre-computed distances from source
}

// ── Blob configuration ── //
const BLOBS = [
  { color: "rgba(59, 130, 246,", size: 700, x: "15%", y: "10%", duration: 28, delay: 0 },
  { color: "rgba(6, 182, 212,", size: 550, x: "75%", y: "70%", duration: 32, delay: 3 },
  { color: "rgba(124, 58, 237,", size: 450, x: "60%", y: "15%", duration: 26, delay: 6 },
  { color: "rgba(16, 185, 129,", size: 300, x: "25%", y: "75%", duration: 35, delay: 9 },
  { color: "rgba(59, 130, 246,", size: 600, x: "50%", y: "45%", duration: 30, delay: 2 },
] as const;

// ── Animation variants for blobs ── //
function blobPath(index: number) {
  // Each blob follows a unique Lissajous-like path
  const paths = [
    { x: [0, 80, 40, -40, 0], y: [0, -60, 80, 20, 0] },
    { x: [0, -70, 30, 60, 0], y: [0, 50, -80, -30, 0] },
    { x: [0, 60, -50, -20, 0], y: [0, -40, 60, -70, 0] },
    { x: [0, -30, 70, -50, 0], y: [0, -70, -20, 60, 0] },
    { x: [0, 40, -60, 80, 0], y: [0, 60, 30, -50, 0] },
  ];
  return paths[index % paths.length];
}

// ── Component ── //
export function AIAuraBackground() {
  // ── Static graph (computed once) ── //
  const graph = useMemo(() => {
    const nodes = generateNodes(NODE_COUNT);
    const edges = generateConnections(nodes, CONNECTION_MAX_DIST);
    const adj = buildAdjacency(edges, NODE_COUNT);
    return { nodes, edges, adj };
  }, []);

  // ── Pulse state (ref-based for performance) ── //
  const pulsesRef = useRef<Pulse[]>([]);
  const nextPulseTimeRef = useRef(0);
  const [pulseTick, setPulseTick] = useState(0); // increment to trigger re-render

  // ── Reduced motion detection ── //
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const checkMotion = () => {
      const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const classReduced = document.documentElement.classList.contains("reduced-motion");
      setReducedMotion(prefersReduced || classReduced);
    };
    checkMotion();

    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const handler = () => checkMotion();
    mq.addEventListener("change", handler);

    const observer = new MutationObserver(checkMotion);
    observer.observe(document.documentElement, { attributeFilter: ["class"] });

    return () => {
      mq.removeEventListener("change", handler);
      observer.disconnect();
    };
  }, []);

  // ── Pulse management via animation frame ── //
  useAnimationFrame((time, delta) => {
    if (reducedMotion) return;

    const now = performance.now();

    // Start new pulse if enough time has elapsed
    if (now >= nextPulseTimeRef.current) {
      const source = Math.floor(Math.random() * graph.nodes.length);
      const distances = computeDistances(graph.adj, source);
      pulsesRef.current.push({ source, startTime: now, distances });

      // Schedule next pulse
      const interval = PULSE_INTERVAL_MIN + Math.random() * (PULSE_INTERVAL_MAX - PULSE_INTERVAL_MIN);
      nextPulseTimeRef.current = now + interval;

      // Trim old pulses
      if (pulsesRef.current.length > 5) {
        pulsesRef.current = pulsesRef.current.slice(-5);
      }
    }

    // Trigger re-render at ~15 fps for pulse updates (no need for 60fps)
    setPulseTick((t) => t + 1);
  });

  // ── Determine node glow intensities ── //
  const nodeGlows = useMemo(() => {
    const now = performance.now();
    const glows = new Float32Array(graph.nodes.length);

    for (const pulse of pulsesRef.current) {
      const elapsed = now - pulse.startTime;
      if (elapsed > NODE_GLOW_DURATION + 3000) continue; // pulse expired

      for (let i = 0; i < graph.nodes.length; i++) {
        const d = pulse.distances[i];
        if (d < 0) continue;
        const nodePeakTime = d * PULSE_PROPAGATION_DELAY;
        const localTime = elapsed - nodePeakTime;
        if (localTime < 0) continue; // not reached yet
        if (localTime > NODE_GLOW_DURATION) continue; // faded

        // Cosine ease-out glow
        const intensity = 0.5 + 0.5 * Math.cos((localTime / NODE_GLOW_DURATION) * Math.PI);
        glows[i] = Math.max(glows[i], intensity);
      }
    }

    return glows;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pulseTick, graph.nodes.length, graph.adj]);

  // ── Determine edge glow intensities (average of connected nodes) ── //
  const edgeGlows = useMemo(() => {
    const glows = new Float32Array(graph.edges.length);
    for (let i = 0; i < graph.edges.length; i++) {
      const e = graph.edges[i];
      glows[i] = Math.max(nodeGlows[e.from], nodeGlows[e.to]);
    }
    return glows;
  }, [nodeGlows, graph.edges]);

  // ── Edge glow color blending ── //
  const edgeColor = useCallback(
    (glow: number) => {
      if (glow < 0.01) return `rgba(59,130,246,0.06)`;
      // Transition from blue to cyan to emerald as glow intensifies
      const r = Math.round(59 + (6 - 59) * glow);
      const g = Math.round(130 + (182 - 130) * glow);
      const b = Math.round(246 + (212 - 246) * glow);
      return `rgba(${r},${g},${b},${0.06 + glow * 0.5})`;
    },
    []
  );

  // ── Node glow color ── //
  const nodeColor = useCallback(
    (glow: number, baseOpacity: number) => {
      if (glow < 0.01) return `rgba(148,163,184,${baseOpacity})`;
      // Glowing nodes shift toward electric blue / cyan
      return `rgba(147,197,253,${baseOpacity + glow * 0.7})`;
    },
    []
  );

  // ── Render ── //
  return (
    <div
      className="fixed inset-0 pointer-events-none overflow-hidden"
      aria-hidden="true"
      style={{ zIndex: 0 }}
    >
      {/* ─── Layer 2: Aura Blobs ─── */}
      {!reducedMotion &&
        BLOBS.map((blob, i) => {
          const path = blobPath(i);
          return (
            <motion.div
              key={i}
              className="absolute rounded-full will-change-transform"
              style={{
                width: blob.size,
                height: blob.size,
                left: `calc(${blob.x} - ${blob.size / 2}px)`,
                top: `calc(${blob.y} - ${blob.size / 2}px)`,
                background: `${blob.color} 0.08)`,
                filter: "blur(100px)",
              }}
              animate={{
                x: path.x,
                y: path.y,
              }}
              transition={{
                duration: blob.duration,
                delay: blob.delay,
                repeat: Infinity,
                ease: "easeInOut",
                repeatType: "mirror",
              }}
            />
          );
        })}

      {/* ─── Layer 3: AI Network ─── */}
      <svg
        className="absolute inset-0 w-full h-full"
        viewBox={`0 0 ${VIEWBOX_SIZE} ${VIEWBOX_SIZE}`}
        preserveAspectRatio="xMidYMid slice"
        aria-hidden="true"
      >
        <defs>
          <radialGradient id="node-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(147,197,253,0.8)" />
            <stop offset="100%" stopColor="rgba(147,197,253,0)" />
          </radialGradient>
        </defs>

        {/* Connection lines */}
        {graph.edges.map((edge, i) => {
          const from = graph.nodes[edge.from];
          const to = graph.nodes[edge.to];
          const glow = edgeGlows[i];
          return (
            <line
              key={`e-${edge.from}-${edge.to}`}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke={edgeColor(glow)}
              strokeWidth={0.8 + glow * 1.5}
              style={{ transition: "stroke 0.15s ease" }}
            />
          );
        })}

        {/* Nodes */}
        {graph.nodes.map((node, i) => {
          const glow = nodeGlows[i];
          const isGlowing = glow > 0.01;
          return (
            <g key={`n-${i}`}>
              {/* Glow halo */}
              {isGlowing && (
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={node.r * 5}
                  fill="url(#node-glow)"
                  style={{ opacity: glow * 0.6 }}
                />
              )}
              {/* Core dot */}
              <circle
                cx={node.x}
                cy={node.y}
                r={isGlowing ? node.r * 1.6 : node.r}
                fill={nodeColor(glow, node.baseOpacity)}
                style={{ transition: "r 0.15s ease, fill 0.15s ease" }}
              />
            </g>
          );
        })}
      </svg>

      {/* ─── Layer 4: Subtle Grid ─── */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: [
            "linear-gradient(rgba(59,130,246,0.06) 1px, transparent 1px)",
            "linear-gradient(90deg, rgba(59,130,246,0.06) 1px, transparent 1px)",
          ].join(", "),
          backgroundSize: "60px 60px",
          maskImage: "radial-gradient(ellipse at center, black 30%, transparent 70%)",
          WebkitMaskImage: "radial-gradient(ellipse at center, black 30%, transparent 70%)",
        }}
      />

      {/* ─── Layer 5: Noise Texture ─── */}
      <div
        className="absolute inset-0"
        style={{
          opacity: 0.025,
          backgroundImage: [
            "repeating-conic-gradient(rgba(255,255,255,0.008) 0% 25%, transparent 0% 50%)",
          ].join(", "),
          backgroundSize: "3px 3px",
          mixBlendMode: "overlay",
        }}
      />

      {/* ─── Static fallback for reduced motion ─── */}
      {reducedMotion && (
        <div
          className="absolute inset-0"
          style={{
            background: [
              "radial-gradient(ellipse 70% 60% at 20% 20%, rgba(59,130,246,0.06) 0%, transparent 70%)",
              "radial-gradient(ellipse 50% 50% at 80% 80%, rgba(6,182,212,0.04) 0%, transparent 60%)",
              "radial-gradient(ellipse 40% 40% at 60% 30%, rgba(124,58,237,0.04) 0%, transparent 50%)",
            ].join(", "),
          }}
        />
      )}
    </div>
  );
}
