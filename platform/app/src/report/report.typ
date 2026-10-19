// The EV-SIENT report as a tagged PDF (Typst 0.14 writes PDF structure tags by default).
// Every word and number comes from /report.json, which report/reportBlocks.ts reads from the
// rendered report; this file only lays it out. Text from the JSON is always placed as a string,
// never parsed as Typst markup.

#let data = json("/report.json")
#let theme = data.theme
#let ink = rgb(theme.text)
#let muted = rgb(theme.secondary)
#let rule = rgb(theme.separator)
#let accent = rgb(theme.link)
#let anchors = data.anchors

#set document(title: data.title, author: data.creator, keywords: ("EV charging", "site readiness", "planning"))
#set text(font: "Source Sans 3", size: 10pt, lang: data.lang, fill: ink)
#set par(leading: 0.55em, spacing: 0.85em)
#let side-margin = 0.8in
#let text-width = 8.5in - 2 * side-margin
#set page(
  paper: "us-letter",
  margin: (x: side-margin, top: 0.75in, bottom: 0.85in),
  footer: context {
    set text(size: 8pt, fill: muted)
    data.title
    h(1fr)
    [Page #counter(page).display() of #counter(page).final().first()]
  },
)
#set list(indent: 0.4em, body-indent: 0.6em, spacing: 0.6em)
#set enum(indent: 0.4em, body-indent: 0.6em)
#set terms(separator: [: ], tight: true, hanging-indent: 1.2em, spacing: 0.55em)
#show link: set text(fill: accent)
#show raw: set text(font: "Source Code Pro")

#show heading: set text(weight: "semibold")
#show heading.where(level: 1): set text(size: 24pt, weight: "bold")
#show heading.where(level: 1): set block(above: 0.4em, below: 0.6em)
#show heading.where(level: 2): it => block(
  width: 100%, above: 1.8em, below: 0.9em, inset: (bottom: 4pt), stroke: (bottom: 0.6pt + rule),
  text(size: 15pt, weight: "bold", it),
)
#show heading.where(level: 3): set text(size: 12.5pt)
#show heading.where(level: 3): set block(above: 1.4em, below: 0.6em)
#show heading.where(level: 4): set text(size: 10.5pt)
#show heading.where(level: 4): set block(above: 1.2em, below: 0.5em)

#show figure: set block(breakable: true, above: 1em, below: 1.1em)
#show figure.caption: set align(start)
#show figure.caption: set text(size: 8.5pt, fill: muted)

// ---------- Inline content ----------

#let tier-mark(shape, color) = {
  let s = 6.6pt
  let mark = if shape == "tier1" { circle(radius: s / 2, fill: color) }
    else if shape == "tier2" { rect(width: s, height: s, radius: 1pt, fill: color) }
    else if shape == "tier3" { rect(width: s, height: 2.6pt, radius: 1pt, fill: color) }
    else if shape == "high-review" { polygon(fill: color, (s / 2, 0pt), (s, s / 2), (s / 2, s), (0pt, s / 2)) }
    else if shape == "special" { polygon(fill: color, (s / 2, 0pt), (s, s), (0pt, s)) }
    else { rect(width: s, height: s, fill: color) }
  box(height: s, pdf.artifact(align(horizon, mark)))
}

#let bar(i) = {
  let w = 48pt
  let h = 6pt
  box(width: w, height: h, pdf.artifact({
    if i.track > 0 {
      place(rect(
        width: i.track * w, height: h, radius: 1.5pt,
        fill: if i.absent { none } else { rgb(i.trackColor) },
        stroke: (paint: rgb(i.edge), thickness: 0.5pt, dash: if i.absent { "dashed" } else { none }),
      ))
    }
    if not i.absent and i.fill > 0 { place(rect(width: i.fill * w, height: h, radius: 1.5pt, fill: rgb(i.color))) }
  }))
}

#let inl(items) = for i in items {
  if i.t == "text" { if i.at("bold", default: false) { strong(i.s) } else { i.s } }
  else if i.t == "link" { if i.to in anchors { link(label(i.to), i.s) } else { i.s } }
  else if i.t == "br" { linebreak() }
  else if i.t == "tier" { tier-mark(i.shape, rgb(i.color)); h(3pt); i.s }
  else if i.t == "bar" { h(4pt); bar(i) }
}

// ---------- Blocks ----------

#let para(b) = {
  let body = inl(b.c)
  if b.style == "eyebrow" { text(size: 11pt, weight: "semibold", fill: muted, body); parbreak() }
  else if b.style == "meta" { text(size: 8.5pt, fill: muted, body); parbreak() }
  else if b.style == "note" { text(size: 8.5pt, fill: muted, body); parbreak() }
  else if b.style == "lead" { text(size: 11.5pt, body); parbreak() }
  else if b.style == "callout" { block(width: 100%, inset: 8pt, radius: 4pt, stroke: 0.6pt + rule, body) }
  else if b.style == "claims" {
    block(width: 100%, inset: (x: 9pt, y: 7pt), radius: 5pt, fill: rgb(theme.soft), body)
  }
  else { body; parbreak() }
}

// Column widths as a browser sizes an auto-width table: each column's widest cell when there is
// room, shrunk toward its longest word when there is not. A word never breaks, so a file hash keeps
// a column wide enough for it.
#let table-block(b) = {
  let n = b.head.len()
  let rows = b.groups.map(g => g.rows).join(default: ()).filter(r => r.len() == n)
  let size = if n >= 10 { 7.5pt } else { 8.5pt }
  let pad = if b.compact { 3pt } else { 4pt }
  let inset = 4pt
  let body(c, head: false) = {
    let x = inl(c.c)
    if c.mono { x = text(font: "Source Code Pro", size: size - 1pt, x) }
    if c.bold { x = strong(x) }
    if head { x = text(weight: "semibold", fill: muted, x) }
    x
  }
  let longest(c) = c.c.filter(i => "s" in i).map(i => i.s.split(" ")).join(default: ()).sorted(key: w => w.len()).at(-1, default: "")
  set text(size: size)
  set par(leading: 0.45em)
  context {
    let natural = ()
    let least = ()
    for x in range(n) {
      let most = 0pt
      let min = 0pt
      for (c, head) in ((b.head.at(x), true),) + rows.map(r => (r.at(x), false)) {
        let w = measure(body(c, head: head)).width
        most = calc.max(most, w)
        min = calc.max(min, if c.num or c.c.any(i => i.t == "bar" or i.t == "tier") { w } else {
          measure(body((..c, c: ((t: "text", s: longest(c)),)), head: head)).width
        })
      }
      natural.push(most + 2 * inset)
      least.push(min + 2 * inset)
    }
    let room = text-width
    let (sn, sm) = (natural.sum(), least.sum())
    let flexible = range(n).filter(x => not b.head.at(x).num)
    let widths = if sn <= room {
      // Spare room goes to the text columns, as in the preview's full-width tables.
      let grow = if flexible.len() > 0 { flexible } else { range(n) }
      let base = grow.map(x => natural.at(x)).sum()
      range(n).map(x => natural.at(x) + if x in grow { (room - sn) * (natural.at(x) / base) } else { 0pt })
    } else if sm >= room { least }
    else { range(n).map(x => least.at(x) + (natural.at(x) - least.at(x)) * ((room - sm) / (sn - sm))) }

    figure(
      kind: table, supplement: none, numbering: none,
      caption: if b.caption.len() > 0 { figure.caption(position: top, inl(b.caption)) },
      table(
        columns: widths,
        inset: (x: inset, y: pad),
        stroke: (x, y) => (bottom: if y == 0 { 0.9pt + ink } else { 0.4pt + rule }),
        table.header(..b.head.map(h => table.cell(align: if h.num { right + bottom } else { left + bottom }, body(h, head: true)))),
        ..b.groups.map(g => {
          let out = ()
          if g.label != none {
            out.push(table.cell(colspan: n, inset: (x: inset, top: 7pt, bottom: pad), text(weight: "semibold", inl(g.label.c))))
          }
          for r in g.rows { out += r.map(c => table.cell(colspan: c.span, align: if c.num { right } else { left }, body(c))) }
          out
        }).join(default: ()),
      ),
    )
  }
}

#let totals(b) = grid(
  columns: (1fr,) * calc.min(4, b.items.len()), column-gutter: 8pt, row-gutter: 8pt,
  ..b.items.map(it => block(width: 100%, inset: (x: 9pt, y: 8pt), radius: 5pt, stroke: 0.6pt + rule, {
    text(size: 8.5pt, fill: muted, inl(it.term))
    linebreak()
    text(size: 18pt, weight: "bold", inl(it.desc))
  })),
)

#let render(blocks) = {
  let first-profile = blocks.position(b => b.b == "group" and b.style == "profile")
  for (k, b) in blocks.enumerate() {
    if b.b == "heading" {
      let h = heading(level: b.level, outlined: b.outlined, bookmarked: b.level <= 3, b.s)
      if b.id != "" and b.id in anchors { [#h #label(b.id)] } else { h }
    }
    else if b.b == "para" { para(b) }
    else if b.b == "list" {
      if b.ordered { enum(..b.items.map(inl)) } else { list(..b.items.map(inl)) }
    }
    else if b.b == "terms" {
      if b.style == "totals" { totals(b) }
      else { terms(..b.items.map(it => terms.item(inl(it.term), inl(it.desc)))) }
    }
    else if b.b == "table" { table-block(b) }
    else if b.b == "figure" {
      figure(
        image(bytes(b.svg), format: "svg", alt: b.alt, width: 100%),
        kind: image, supplement: none, numbering: none,
        caption: figure.caption(inl(b.caption)),
      )
    }
    else if b.b == "contents" {
      heading(level: 2, outlined: false, bookmarked: true, b.title)
      outline(title: none, depth: 2, target: selector.or(..b.items.filter(i => i.to in anchors).map(i => label(i.to))))
    }
    else if b.b == "group" {
      if b.style == "cover" {
        block(width: 100%, inset: (bottom: 10pt), stroke: (bottom: 1.2pt + ink), render(b.c))
      } else if b.style == "panel" {
        block(width: 100%, inset: 12pt, radius: 6pt, stroke: 0.6pt + rule, above: 1.4em, render(b.c))
      } else if b.style == "columns" {
        block(breakable: false, grid(columns: (1fr,) * b.c.len(), column-gutter: 18pt, ..b.c.map(c => render(c.c))))
      } else if b.style == "profile" {
        if k != first-profile { pagebreak(weak: true) }
        // The site's name, its summary and its score breakdown start on one page.
        let lead = b.c.position(x => x.b == "para" and x.style == "lead")
        let first-table = b.c.position(x => x.b == "table")
        let cut = calc.min(if first-table != none { first-table + 1 } else if lead != none { lead + 1 } else { 1 }, b.c.len())
        block(breakable: false, render(b.c.slice(0, cut)))
        render(b.c.slice(cut))
      } else { render(b.c) }
    }
  }
}

#render(data.blocks)
