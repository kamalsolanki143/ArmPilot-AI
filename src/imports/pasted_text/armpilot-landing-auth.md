# Figma Make Prompt — ArmPilot Landing Page + Auth Flow

Copy-paste everything below into Figma Make.

---

## Prompt

Design a 3-screen flow for **ArmPilot**, a dark-themed AI inference monitoring dashboard product for Arm-based servers. Match the existing dashboard's visual language exactly: near-black background (#0A0B0D range), slightly lighter card surfaces (#14161A range), subtle 1px borders, orange brand accent (#F97316-ish), monospace/tabular numerals for stats, and muted gray secondary text. Sidebar-and-topbar dashboard already exists — these 3 screens must feel like they belong to the same product.

### Screen 1 — Landing Page

**Header (sticky, transparent-to-dark on scroll):**
- Left: ArmPilot logo mark (orange square with "A") + wordmark "ArmPilot" + small "AI · v2.4.1" caption, same as dashboard sidebar
- Right: nav links (Product, Benchmarks, Docs, Pricing) in muted gray, plus a **"Log In"** button (ghost/outline style) and a **"Get Started"** button (solid orange, primary CTA)
- Both Log In and Get Started route to Screen 2 (Login), just pre-select different default tabs (Log In → sign-in tab active, Get Started → sign-up tab active)

**Hero section:**
- Large headline (e.g., "Inference monitoring built for Arm silicon") in bold white
- Subheadline in muted gray, 1-2 lines, describing real-time TTFT/throughput/latency tracking on Arm Neoverse
- Primary CTA button "Start Free" (orange, solid) → routes to Login/Signup screen
- Secondary CTA "View Live Demo" (ghost button)
- Below the fold of the hero: an embedded, non-interactive preview/screenshot mockup of the actual dashboard (System Overview cards + charts), slightly scaled down, with a subtle drop shadow and rounded corners, floating over the dark background — this visually promises what's behind the login wall

**Social proof strip:** thin row of grayscale/muted partner or "works with" logos (e.g., llama.cpp, Arm Neoverse, ONNX) with label "Compatible with" — low visual weight, small caps label like the dashboard's "SYSTEM STATUS" labels

**Feature grid (3-4 columns):** mirror the dashboard's card style exactly — dark cards, subtle border, small-caps label at top (like "TTFT", "THROUGHPUT"), icon in orange/cyan/green/purple accent, short feature title, 1-sentence description. Features: Real-Time Benchmarking, Latency Percentile Tracking (P50/P95/P99), One-Click Optimization, AI-Powered Recommendations — tie back to the actual nav items in the dashboard (Inference, Benchmark, Optimization, AI Recommend)

**Metrics/stats band:** reuse the big monospace-number style from the dashboard stat cards to show product credibility numbers, e.g. "-62% TTFT", "2.7× throughput", "12 active integrations" — same font treatment as dashboard for visual continuity

**Footer CTA:** centered, "Ready to optimize your inference stack?" + "Get Started Free" button → Login/Signup screen

**Footer:** standard dark footer, muted gray links, ArmPilot logo mark small, copyright line

---

### Screen 2 — Login / Sign Up (single screen, tabbed)

- Centered card (max-width ~420px) on the same dark background as the dashboard, card style matches dashboard cards (dark surface, subtle border, rounded corners)
- ArmPilot logo mark centered above the card
- **Tab switcher** at top of card: "Log In" | "Sign Up" (underline or pill style, orange active state — same treatment as the dashboard's active nav item, but simplified to just a bottom border in orange, not the triple-signaled fill+bar+ring from the dashboard nav)

**Log In tab fields:**
- Email input
- Password input (with show/hide toggle icon)
- "Forgot password?" link, right-aligned, muted gray, small text
- Primary button: "Log In" (solid orange, full width)
- Divider with "or continue with"
- Secondary auth buttons: "Continue with Google", "Continue with GitHub" (outline style, icon + label)
- Below card: "Don't have an account? Sign Up" — switches tab

**Sign Up tab fields:**
- Name input
- Email input
- Password input (with strength indicator bar — reuse the dashboard's color logic: red/orange/green states)
- "Create Account" button (solid orange, full width)
- Same social auth options
- Small terms-of-service checkbox + text
- Below card: "Already have an account? Log In" — switches tab

**Both tabs:** on successful submit, route directly to Screen 3 (Dashboard) — no intermediate confirmation screen, no email verification step shown in this flow (assume instant auth for prototype purposes)

**Error/loading states:** include a disabled/loading state on the primary button (spinner + "Logging in..." text) since this is a real interaction, not just a static screen

---

### Screen 3 — Dashboard (already built)

- This is the existing "System Overview" dashboard screen (sidebar nav: Dashboard, Inference, Benchmark, Optimization, AI Recommend, Reports, History, Settings; stat cards; throughput/latency charts; recent benchmark runs table)
- On first load after signup/login, optionally show a brief "Welcome, [Name]" toast/banner at the top that auto-dismisses — otherwise identical to current design
- No changes needed to this screen's existing layout

---

### Prototype connections (interactions to wire up in Figma Make)

1. Landing header "Log In" → Screen 2, Login tab active
2. Landing header "Get Started" → Screen 2, Sign Up tab active
3. Hero "Start Free" → Screen 2, Sign Up tab active
4. Footer CTA "Get Started Free" → Screen 2, Sign Up tab active
5. Screen 2 Login tab "Log In" button → Screen 3 (Dashboard)
6. Screen 2 Sign Up tab "Create Account" button → Screen 3 (Dashboard)
7. Screen 2 "Sign Up"/"Log In" tab labels → toggle within Screen 2
8. Screen 2 "Forgot password?" → can stub as a non-functional link or omit from prototype flow

### Design consistency checklist
- Reuse exact color tokens from the dashboard (orange accent, cyan/green/orange/purple stat colors, dark surfaces, border colors)
- Reuse the same font pairing (bold sans-serif for headings/body, monospace/tabular numerals for any stat display)
- Keep corner radius, border weight, and shadow style consistent with existing dashboard cards
- Keep spacing/padding rhythm consistent (the dashboard uses generous card padding — match it on landing feature cards and the auth card)