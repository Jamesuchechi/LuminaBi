# Dashboard Design System Reference Guide

## Quick Reference: Design Patterns Used

### 1. Glass Panel Component
Used for all card-like containers throughout dashboards.

```html
<div class="glass-panel rounded-2xl p-6 border border-white/10 hover:border-neonBlue/50 transition-all group">
    <!-- Content -->
</div>
```

**Characteristics:**
- Rounded corners (2xl = 16px)
- Padding (6 = 1.5rem)
- Semi-transparent white border
- Hover effect with neon border
- Smooth transition
- Group for child hover effects

---

### 2. Header Section Pattern
Used for page titles and section headers.

```html
<div class="flex items-center gap-3 mb-2">
    <i class="fas fa-[icon-name] text-neonBlue text-2xl"></i>
    <h1 class="text-4xl md:text-5xl font-bold text-white">Title</h1>
</div>
<p class="text-gray-400 text-lg">Subtitle or description</p>
```

**Characteristics:**
- Icon with neonBlue color
- Large bold white heading
- Secondary text in gray-400
- Responsive text sizes
- Icon-text alignment

---

### 3. Status Badge Pattern
Used for published/draft indicators.

```html
<!-- Published -->
<span class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-neonBlue/20 border border-neonBlue/50">
    <i class="fas fa-check-circle text-neonBlue text-xs"></i>
    <span class="text-xs font-mono text-neonBlue">Published</span>
</span>

<!-- Draft -->
<span class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gray-600/30 border border-gray-500/50">
    <i class="fas fa-circle text-gray-500 text-xs"></i>
    <span class="text-xs font-mono text-gray-400">Draft</span>
</span>
```

**Characteristics:**
- Color-coded background
- Matching border color
- Icon + text layout
- Small, rounded pill shape
- Monospace font for tech feel

---

### 4. Action Button Pattern
Used for primary and secondary actions.

```html
<!-- Primary Button (Gradient) -->
<a href="/" class="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-neonBlue to-neonPurple text-white font-bold rounded-xl hover:scale-105 transition-transform duration-300 shadow-lg shadow-neonBlue/30">
    <i class="fas fa-plus text-sm"></i> Create
</a>

<!-- Secondary Button -->
<button class="inline-flex items-center gap-2 px-4 py-2 bg-neonBlue/20 hover:bg-neonBlue/40 border border-neonBlue/50 text-neonBlue text-sm font-mono rounded-lg transition">
    <i class="fas fa-pen text-xs"></i> Edit
</button>

<!-- Danger Button -->
<a href="/" class="inline-flex items-center gap-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/40 border border-red-500/50 text-red-400 text-sm font-mono rounded-lg transition">
    <i class="fas fa-trash text-xs"></i> Delete
</a>
```

**Characteristics:**
- Primary: Gradient with shadow and scale on hover
- Secondary: Semi-transparent with border
- Icon + text inside
- Rounded corners (xl = 12px for primary, lg = 8px for secondary)
- Smooth transitions

---

### 5. Form Input Pattern
Used for form fields in create/edit pages.

```html
<label class="block text-sm font-mono uppercase tracking-wider text-gray-400 mb-3">
    <i class="fas fa-heading text-neonBlue mr-2"></i>Label Text
</label>
<input type="text" class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:bg-neonBlue/5 focus:border-neonBlue/50 focus:ring-0 focus:shadow-lg focus:shadow-neonBlue/10 text-white placeholder-gray-500/60 transition" placeholder="Placeholder text">
```

**Characteristics:**
- Icon-enhanced labels
- Semi-transparent backgrounds
- White borders with low opacity
- Neon glow on focus
- Smooth color transitions

---

### 6. Empty State Pattern
Used when no data is available.

```html
<div class="glass-panel rounded-2xl p-16 text-center border border-white/10">
    <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-neonBlue/10 mb-6">
        <i class="fas fa-[icon-name] text-3xl text-neonBlue"></i>
    </div>
    <p class="text-gray-300 text-lg font-mono mb-2">Empty State Title</p>
    <p class="text-gray-500 text-sm mb-6">Description of what to do</p>
    <a href="/" class="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-neonBlue to-neonPurple text-white font-bold rounded-xl hover:scale-105 transition">
        <i class="fas fa-plus"></i> Call to Action
    </a>
</div>
```

**Characteristics:**
- Center-aligned content
- Large icon in colored circle
- Title and description
- Call-to-action button

---

### 7. Icon Badge Pattern
Used for visual indicators with numbers.

```html
<div class="w-16 h-16 rounded-full bg-neonBlue/10 flex items-center justify-center group-hover:bg-neonBlue/20 transition text-neonBlue text-2xl">
    <i class="fas fa-[icon-name]"></i>
</div>
```

**Characteristics:**
- Circular container
- Semi-transparent background
- Icon centered inside
- Hover effect
- Smooth transitions

---

### 8. Sidebar Section Pattern
Used for information and quick actions in sidebars.

```html
<div class="glass-panel rounded-2xl p-6 border border-white/10">
    <div class="flex items-center gap-2 mb-4 pb-4 border-b border-white/10">
        <i class="fas fa-[icon-name] text-neonBlue"></i>
        <h2 class="text-lg font-bold text-white">Section Title</h2>
    </div>
    <div class="space-y-4">
        <!-- Content -->
    </div>
</div>
```

**Characteristics:**
- Glass-panel container
- Icon + title header
- Bottom border separator
- Spaced content area

---

## Color Palette Quick Reference

| Color | Hex | Use Case |
|-------|-----|----------|
| Neon Blue | #00f3ff | Primary actions, icons, hover states |
| Neon Purple | #bd00ff | Secondary actions, accents |
| Neon Pink | #ff00aa | Tertiary accents, highlights |
| Success | #00ff9d | Published status, confirmations |
| Warning | #ffc800 | Warnings, cautions |
| Error | #ff004d | Delete, errors, danger states |
| Gray 400 | #a0aec0 | Secondary text |
| Gray 500 | #718096 | Tertiary text |
| White/10 | rgba(255,255,255,0.1) | Subtle borders |
| White/20 | rgba(255,255,255,0.2) | Slightly more visible borders |

---

## Typography Reference

### Headings
- **H1**: `text-4xl md:text-5xl font-bold text-white`
- **H2**: `text-2xl md:text-3xl font-bold text-white`
- **H3**: `text-lg font-bold text-white`

### Body Text
- **Primary**: `text-base text-white`
- **Secondary**: `text-sm text-gray-400`
- **Tertiary**: `text-xs text-gray-500`

### Monospace (Technical)
- **Labels**: `text-sm font-mono uppercase tracking-wider text-gray-400`
- **Badges**: `text-xs font-mono`

---

## Spacing Reference

- **Gaps**: `gap-2`, `gap-3`, `gap-4`, `gap-6`
- **Padding**: `p-3`, `p-4`, `p-6`, `p-8`, `p-12`, `p-16`
- **Margins**: `mb-2`, `mb-4`, `mb-6`, `mb-8`, `mb-12`

---

## Rounded Corners Reference

- **Small**: `rounded-lg` (8px)
- **Medium**: `rounded-xl` (12px)
- **Large**: `rounded-2xl` (16px)

---

## Shadow Reference

Only used on primary gradient buttons:
```
shadow-lg shadow-neonBlue/30
```

---

## Transition Reference

- **Default**: `transition` (150ms)
- **Fast**: `transition-transform duration-300` (with scale)
- **All properties**: `transition-all`

---

## Icon Usage Guide

### Common Icons by Category

**Navigation**
- Back: `fas fa-arrow-left`
- Forward: `fas fa-arrow-right`
- Menu: `fas fa-bars`
- X/Close: `fas fa-times`

**Actions**
- Create: `fas fa-plus`
- Edit: `fas fa-pen`
- Delete: `fas fa-trash`
- Save: `fas fa-save`
- View: `fas fa-eye`
- Hide: `fas fa-eye-slash`

**Data/Charts**
- Dashboard: `fas fa-layer-group`
- Chart: `fas fa-chart-bar`
- Bar Chart: `fas fa-chart-line`
- Pie Chart: `fas fa-chart-pie`
- Graph: `fas fa-graph`

**Status**
- Check: `fas fa-check-circle`
- Circle: `fas fa-circle`
- Alert: `fas fa-alert-circle`
- Warning: `fas fa-exclamation-triangle`

**UI**
- Clock: `fas fa-clock`
- Inbox: `fas fa-inbox`
- Settings: `fas fa-cogs`
- Grid: `fas fa-th`

---

## Mobile Responsiveness

All templates use responsive patterns:

```html
<!-- Flex layout that stacks on mobile -->
<div class="flex flex-col md:flex-row gap-6">
    <!-- Stacks vertically on mobile, horizontally on medium+ -->
</div>

<!-- Grid that changes columns -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <!-- 1 column on mobile, 2 on tablet, 3 on desktop -->
</div>

<!-- Text that scales -->
<h1 class="text-4xl md:text-5xl">Title</h1>
<!-- 4xl on mobile, 5xl on tablet+ -->
```

---

## Best Practices

1. **Always use glass-panel for containers** - Maintains consistency
2. **Use neonBlue for primary actions** - Matches brand color
3. **Include icons in buttons** - Visual clarity
4. **Maintain spacing hierarchy** - Creates visual rhythm
5. **Use gradients for emphasis** - Draws attention to important buttons
6. **Provide hover states** - Improves UX feedback
7. **Use Font Awesome icons consistently** - Professional appearance
8. **Follow typography hierarchy** - Clear information flow
9. **Use monospace for technical content** - Distinguishes data
10. **Test on mobile** - Ensure responsive design works

---

## File References

- **Color definitions**: Tailwind CSS theme in `tailwind.config.js`
- **Glass-panel class**: CSS in `base.html` or `static/css/tailwind.css`
- **Icon library**: Font Awesome 6.4.0 CDN in `base.html`
- **Layout templates**: `/templates/dashboards/dashboard/`

---

*This guide ensures consistency across all dashboard templates and serves as a reference for future UI updates.*
