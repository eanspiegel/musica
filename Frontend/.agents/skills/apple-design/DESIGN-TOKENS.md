# Design Tokens — Spotify-inspired Dark Theme

> Aesthetic reference: Spotify. Principle reference: Apple Design (fluid, physical, intentional).
> Stack: Vue 3 + Tailwind CSS v3 + CSS custom properties.

---

## 1. Color Palette

All colors are registered as CSS custom properties in `:root` and mapped to Tailwind via `tailwind.config.js`.

### Brand

| Token | Hex | Usage |
|---|---|---|
| `--color-brand` | `#1DB954` | Primary CTA, progress fills, active states |
| `--color-brand-hover` | `#1ed760` | Hover on brand elements |
| `--color-brand-muted` | `#158a3e` | Pressed / active depressed state |
| `--color-brand-subtle` | `#1DB95420` | Ghost backgrounds, chip highlights |

### Surface (dark layers — Spotify depth model)

| Token | Hex | Usage |
|---|---|---|
| `--color-base` | `#000000` | App root background |
| `--color-surface-0` | `#0d0d0d` | Primary content area background |
| `--color-surface-1` | `#121212` | Cards, panels, sidebar |
| `--color-surface-2` | `#181818` | Hover card, elevated chip |
| `--color-surface-3` | `#242424` | Modal surface, drawer |
| `--color-surface-overlay` | `rgba(0,0,0,0.72)` | Scrim behind modals |

### Chrome (nav, toolbar, player bar)

| Token | Value | Usage |
|---|---|---|
| `--color-chrome` | `rgba(18,18,18,0.85)` | Nav bar, bottom player — translucent |
| `--color-chrome-border` | `rgba(255,255,255,0.06)` | Top edge highlight (light catching material) |

### Text

| Token | Hex | Usage |
|---|---|---|
| `--color-text-primary` | `#FFFFFF` | Body copy, primary labels |
| `--color-text-secondary` | `#B3B3B3` | Subtitles, metadata, placeholders |
| `--color-text-muted` | `#535353` | Disabled, hints, timestamps |
| `--color-text-on-brand` | `#000000` | Text on green brand background |
| `--color-text-link` | `#FFFFFF` | Underline links; hover → brand |

### Feedback / Semantic

| Token | Hex | Usage |
|---|---|---|
| `--color-success` | `#1DB954` | Reuses brand — success is brand |
| `--color-warning` | `#F59B23` | Warnings, caution |
| `--color-error` | `#E53935` | Errors, destructive actions |
| `--color-info` | `#2196F3` | Informational badges |

### Border / Divider

| Token | Value | Usage |
|---|---|---|
| `--color-border` | `rgba(255,255,255,0.08)` | Card borders, section dividers |
| `--color-border-focus` | `#1DB954` | Focus ring color (brand) |

---

## 2. Typography

Font stack: `'Circular Std', 'Circular', ui-sans-serif, system-ui, -apple-system, sans-serif`
Fallback if Circular is unavailable: system-ui (Apple/Android system font — already optically sized).

### Type Scale

| Role | CSS Class | Size | Weight | Line-height | Letter-spacing |
|---|---|---|---|---|---|
| Display | `.text-display` | `clamp(2rem, 5vw, 3.5rem)` | 700 | 1.05 | `-0.03em` |
| Heading 1 | `.text-h1` | `1.75rem` (28px) | 700 | 1.1 | `-0.02em` |
| Heading 2 | `.text-h2` | `1.375rem` (22px) | 700 | 1.2 | `-0.01em` |
| Heading 3 | `.text-h3` | `1.125rem` (18px) | 600 | 1.3 | `0` |
| Body | `.text-body` | `0.875rem` (14px) | 400 | 1.5 | `0` |
| Caption | `.text-caption` | `0.75rem` (12px) | 400 | 1.4 | `+0.01em` |
| Label | `.text-label` | `0.6875rem` (11px) | 700 | 1.0 | `+0.08em` uppercase |

> **Rule (from Apple Typography WWDC 2020)**: tracking is size-specific.
> Large text → tighten. Small text → loosen slightly. Never one fixed value across all sizes.

---

## 3. Spacing

Follows an 8px base grid. All spacing tokens are multiples of 4px for micro-adjustments.

```
4px  → xs  (padding inside badges, tight gaps)
8px  → sm  (gap between icon and label)
12px → md  (inner card padding, vertical rhythm)
16px → lg  (section gutter)
24px → xl  (card padding)
32px → 2xl (section separator)
48px → 3xl (page section gap)
```

---

## 4. Border Radius

| Token | Value | Usage |
|---|---|---|
| `--radius-sm` | `4px` | Badges, chips |
| `--radius-md` | `8px` | Buttons, inputs |
| `--radius-lg` | `12px` | Cards |
| `--radius-xl` | `16px` | Modals, drawers |
| `--radius-full` | `9999px` | Pill buttons, avatars |

---

## 5. Buttons

### Variants

| Variant | Background | Text | Hover bg | Active bg |
|---|---|---|---|---|
| `primary` | `--color-brand` (#1DB954) | `--color-text-on-brand` (#000) | `--color-brand-hover` | `--color-brand-muted` |
| `secondary` | `--color-surface-3` | `--color-text-primary` | `--color-surface-2`+border | — |
| `ghost` | transparent | `--color-text-primary` | `rgba(255,255,255,0.08)` | — |
| `danger` | `--color-error` | `#fff` | `#c62828` | — |

### Interaction (Apple Design — respond on pointer-down)

```css
.btn:active {
  transform: scale(0.97);
  transition: transform 80ms ease-out;
}
```

- Feedback is instant on `pointerdown` (visual highlight before `click` fires).
- Disabled: `opacity: 0.4`, `cursor: not-allowed`.
- Loading: spinner replaces icon, button stays the same size (no layout shift).

### Sizes

| Size | Padding | Font size | Min-height |
|---|---|---|---|
| `sm` | `8px 16px` | 12px (label) | 32px |
| `md` (default) | `12px 24px` | 14px (body) | 40px |
| `lg` | `16px 32px` | 16px | 48px |

---

## 6. Inputs & Selects

### Input

- Background: `--color-surface-2` (`#181818`)
- Border: `--color-border` at rest, `--color-border-focus` on focus
- Text: `--color-text-primary`
- Placeholder: `--color-text-muted`
- Focus ring: `0 0 0 2px var(--color-brand)` (no default browser outline)
- Radius: `--radius-md` (8px)
- Height: 40px (same as `md` button for visual alignment)

### Select

Same as Input. Custom arrow icon in `--color-text-secondary`.
Dropdown panel: `--color-surface-3`, border `--color-border`, radius `--radius-md`.
Hover item: `--color-surface-2`. Selected item: text `--color-brand`.

---

## 7. Animations & Transitions

> Principle: springs for gesture-driven UI; simple easing for state changes.
> Always interruptible. Never lock out input.

### Easing Curves

| Name | CSS | Usage |
|---|---|---|
| `ease-out-smooth` | `cubic-bezier(0.25, 0.46, 0.45, 0.94)` | Page transitions, drawers entering |
| `ease-in-smooth` | `cubic-bezier(0.55, 0.06, 0.68, 0.19)` | Drawers exiting |
| `ease-standard` | `cubic-bezier(0.4, 0, 0.2, 1)` | Generic state changes (color, opacity) |
| `ease-spring` | Use Motion/Framer Motion spring — NOT CSS | Drag, drop, momentum UI |

### Duration Scale

| Role | Duration | Property |
|---|---|---|
| Micro (feedback) | `80ms` | Button press scale, icon swap |
| Fast | `150ms` | Color/opacity changes, tooltip appear |
| Standard | `250ms` | Panel open, card expand |
| Deliberate | `350ms` | Modal enter/exit |
| Page | `400ms` | Route transitions |

### Spring Defaults (Motion/Framer Motion)

| Interaction | `bounce` | `duration` | Notes |
|---|---|---|---|
| Default UI | `0` | `0.35` | Critically damped, no overshoot |
| Drawer/sheet | `0.1` | `0.3` | Slight ease into position |
| Momentum flick | `0.2` | `0.4` | Overshoot only after user flick |
| Drag reposition | `0` | `0.4` | Smooth settle |

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  /* Replace slides/springs with cross-fades */
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 150ms !important;
    transition-property: opacity !important;
  }
}
```

---

## 8. Shadows & Elevation

| Level | Value | Usage |
|---|---|---|
| `0` | none | Flat — inline cards on dark bg |
| `1` | `0 2px 8px rgba(0,0,0,0.4)` | Tooltips, small chips |
| `2` | `0 4px 16px rgba(0,0,0,0.5)` | Cards on hover elevation |
| `3` | `0 8px 32px rgba(0,0,0,0.7)` | Modals, drawers, player bar |

---

## 9. Badges / Tags

- Background: semantic surface (e.g., `rgba(29,185,84,0.15)` for green)
- Text: semantic color (`--color-brand` for green)
- No solid color fill — use low-opacity background + matching text
- Radius: `--radius-sm` (4px) for rectangular tags, `--radius-full` for pill chips

---

## 10. Focus & Accessibility

- Focus ring: `outline: 2px solid var(--color-brand); outline-offset: 2px`
- Never remove `:focus-visible` ring for keyboard users
- All interactive elements: min touch target 44×44px (Apple HIG)
- Color contrast: text on surface must meet WCAG AA (4.5:1 for body, 3:1 for large text)

---

## 11. Scrollbars

```css
/* Thin, Spotify-style custom scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.3); }
```

---

## 12. How to Use in Components

```vue
<!-- Use Tailwind token classes mapped from CSS vars -->
<button class="btn-primary">Download</button>

<!-- Reference tokens directly in inline-critical styles only -->
<div style="background: var(--color-surface-1)"></div>
```

All tokens flow from `tailwind.config.js` → Tailwind utilities → component classes.
Never hardcode hex values in components. Use the token names from this document.
