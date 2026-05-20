# SmartPark Design System

## Product direction

The interface follows the supplied design concept: blue SmartPark branding, left sidebar navigation, top search/header bar, white cards on a soft background, operational dashboard panels, visual slot grid, management forms, configuration pages, payment modal, and receipt view. The rebuild improves the concept by making every visible action persist through the backend.

## Colors

| Token | Value | Use |
|---|---:|---|
| Ink | `#102033` | Main text and headings. |
| Muted | `#667085` | Secondary copy and metadata. |
| Surface | `#FFFFFF` | Cards, panels, login form. |
| Background | `#F5F8FC` | App canvas. |
| Line | `#E5EAF1` | Borders and dividers. |
| Brand blue | `#2563EB` | Primary actions, logo, active navigation. |
| Brand blue soft | `#EAF2FF` | Selected nav, info surfaces. |
| Success | `#15803D` / `#EAF8EF` | Available, paid, completed, healthy. |
| Warning | `#B54708` / `#FFF4E5` | Reserved, pending, operational attention. |
| Danger | `#B42318` / `#FDECEC` | Occupied, unpaid, failed, destructive actions. |
| Slate | `#475467` / `#EEF2F6` | Maintenance, disabled, inactive states. |
| Purple | `#6D28D9` / `#F1EAFE` | Supporting metric accent. |

## Typography

The Flet app uses a pragmatic hierarchy rather than decorative fonts. Page titles are large and heavy, section titles are medium and bold, table text stays compact, and helper text is muted. This keeps the UI readable on a classroom projector.

## Spacing and radius

Spacing uses 4, 8, 12, 16, 24, and 32 pixel increments. Primary cards use an 18 pixel radius, form inputs use a 12 pixel radius, small chips use fully rounded pills, and panels use soft shadows with low opacity.

## Component rules

| Component | Rule |
|---|---|
| Sidebar | Persistent, left aligned, product-first, no generic developer tabs. |
| Topbar | Page title, environment note, search box, refresh action. |
| Cards | White surface, border, soft shadow, icon block, title/value/subtitle. |
| Buttons | Primary blue for main action, outlined neutral for secondary, red for destructive. |
| Forms | Labels, helper text, validation, selected defaults, save/cancel actions. |
| Tables | Used for dense records only, never as the only screen content. |
| Slot tiles | Status-colored, clickable, tooltip-enabled, slot code plus slot type cue. |
| Drawer | Operational details and actions in one place; not just a read-only record view. |
| Alerts | Severity-colored surfaces with icon and practical text. |
| Empty states | Icon, title, plain explanation, and no raw JSON. |

## Slot status colors

| Status | Meaning |
|---|---|
| Available | Green; may be assigned. |
| Occupied | Red; active use or sensor-occupied. |
| Reserved | Amber; intentionally blocked. |
| Maintenance | Slate; blocked for service. |
| Disabled | Dark slate; unavailable by policy. |

## UX stance

SmartPark should feel like a small professional SaaS console. The UI avoids random colors, oversized novelty controls, emoji, placeholder lorem ipsum, and dead buttons. A judge can click through core workflows without being dumped into raw API artifacts.
