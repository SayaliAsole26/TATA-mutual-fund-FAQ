---
name: Obsidian Finance Assistant
colors:
  surface: '#0e1513'
  surface-dim: '#0e1513'
  surface-bright: '#343b39'
  surface-container-lowest: '#090f0e'
  surface-container-low: '#161d1b'
  surface-container: '#1a211f'
  surface-container-high: '#252b2a'
  surface-container-highest: '#2f3634'
  on-surface: '#dde4e1'
  on-surface-variant: '#bbcac6'
  inverse-surface: '#dde4e1'
  inverse-on-surface: '#2b3230'
  outline: '#859490'
  outline-variant: '#3c4947'
  surface-tint: '#4fdbc8'
  primary: '#4fdbc8'
  on-primary: '#003731'
  primary-container: '#14b8a6'
  on-primary-container: '#00423b'
  inverse-primary: '#006b5f'
  secondary: '#ffb95f'
  on-secondary: '#472a00'
  secondary-container: '#ee9800'
  on-secondary-container: '#5b3800'
  tertiary: '#ffb59e'
  on-tertiary: '#5e1800'
  tertiary-container: '#f38764'
  on-tertiary-container: '#6c2106'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#71f8e4'
  primary-fixed-dim: '#4fdbc8'
  on-primary-fixed: '#00201c'
  on-primary-fixed-variant: '#005048'
  secondary-fixed: '#ffddb8'
  secondary-fixed-dim: '#ffb95f'
  on-secondary-fixed: '#2a1700'
  on-secondary-fixed-variant: '#653e00'
  tertiary-fixed: '#ffdbd0'
  tertiary-fixed-dim: '#ffb59e'
  on-tertiary-fixed: '#3a0b00'
  on-tertiary-fixed-variant: '#7c2d11'
  background: '#0e1513'
  on-background: '#dde4e1'
  surface-variant: '#2f3634'
typography:
  headline-xl:
    fontFamily: Geist
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-md:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.1em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  container-max: 800px
  gutter: 16px
---

## Brand & Style
The design system is centered on a "Dark-First" philosophy, specifically tailored for a fintech FAQ assistant where focus and data density are paramount. The brand personality is authoritative yet approachable, utilizing a **Minimalist** style with high-contrast elements to ensure maximum legibility in low-light environments.

The aesthetic avoids unnecessary ornamentation, favoring structural integrity and clear information hierarchy. By using a deep charcoal foundation, we reduce eye strain for users managing complex financial queries, while muted teal accents provide a sense of technological precision and calm. The emotional response should be one of "controlled expertise"—the UI feels like a high-end financial terminal that is nonetheless easy for a layperson to navigate.

## Colors
The palette is engineered for a premium dark-mode experience. 
- **Core Surfaces:** The true-black background (#0A0A0A) provides the ultimate canvas for high-contrast text. Secondary surfaces (#1A1A1A) create depth without the need for heavy shadows.
- **Accents:** Muted Teal serves as the primary action color, signifying utility and progress. Warm Amber is reserved strictly for legal disclaimers, financial risks, or "caution" states.
- **Semantic States:** Instead of bright, jarring banners, the design system uses "Tinted Surfaces." Success and error states are communicated via subtle background washes with high-saturation left-border accents to maintain a professional, subdued tone.

## Typography
This design system utilizes **Geist** for all primary communication. Geist’s technical, geometric structure aligns with the fintech context, offering exceptional clarity in tabular data and long-form FAQ answers. 

**JetBrains Mono** is introduced as a secondary label font to denote metadata, timestamps, and financial tickers, reinforcing the "system-level" precision of the assistant. All headlines feature slightly negative letter-spacing to maintain a tight, modern appearance, while body text uses generous line-heights to improve readability against the dark background.

## Layout & Spacing
The layout follows a **Fixed Grid** model for the central FAQ content to ensure focus. On desktop, the main conversation/assistant feed is capped at 800px to maintain optimal line lengths for reading.

A strictly linear, 4px-based scaling system is used for all margins and padding. 
- **Mobile:** Uses a single-column view with 16px side margins.
- **Tablet/Desktop:** The assistant occupies the center of the screen, with auxiliary links or history potentially appearing in a sidebar that adheres to the 16px gutter rule. 
- **Spacing Rhythm:** Use `xl` (40px) to separate major sections of the assistant's response, and `md` (16px) for internal card padding.

## Elevation & Depth
Depth is achieved through **Tonal Layers** rather than traditional shadows. 
- **Level 0:** Background (#0A0A0A) - The "Void" layer where the main canvas sits.
- **Level 1:** Surface (#1A1A1A) - Card elements, input containers, and navigation bars.
- **Level 2:** Hover/Active (#262626) - Slightly lighter gray to indicate interactivity.

To provide a sense of "premium" build, use 1px solid borders for all surface elements. Border colors should be `#262626` (low contrast) for inactive states and the primary teal (#14B8A6) for active or focused states. Shadows, if used at all, should be limited to a very subtle 10% black blur to slightly lift cards off the background.

## Shapes
The shape language is "Soft" (0.25rem / 4px). This minimal rounding maintains the professional, precise feel of a financial tool while avoiding the aggressive sharpness of pure brutalism. 

- **Standard Elements:** 4px radius for buttons, input fields, and small cards.
- **Large Containers:** Use `rounded-lg` (8px) for primary assistant response bubbles or modal containers to subtly distinguish them from smaller UI components.
- **Icons:** Should be stroke-based (not filled) with a 1.5px or 2px weight to match the clean lines of the typography.

## Components
- **Buttons:** 
  - *Primary:* Solid Teal background with black text for maximum contrast.
  - *Secondary:* Transparent background with a Teal 1px border.
- **Input Fields:** 
  - Background: `#1A1A1A`. 
  - Border: 1px solid `#262626`. 
  - On Focus: Border changes to Teal with a subtle Teal outer glow (2px blur).
- **Cards (Assistant Responses):** 
  - Use a subtle left-accent bar (4px wide) to color-code responses: Teal for General Info, Amber for Disclaimers, and White for User Queries.
- **Chips:** 
  - Use for "Suggested Questions." These should have a `#1A1A1A` background and a `#262626` border, turning Teal on hover.
- **Lists:** 
  - Use 1px bottom borders (`#1A1A1A`) to separate FAQ items in a list view.
- **Checkboxes/Radios:** 
  - Custom Teal-filled states with a white checkmark. The unselected state is a simple `#262626` ring.