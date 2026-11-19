// Read one rendered slide draft into a shape spec, and list everything that cannot become a native shape.
// Runs in the browser. Every value comes from the rendered draft: this file holds no style of its own.
// Lengths in the spec are fractions of the slide width, so builders can scale them to any page size.
(() => {
  const SVG_SHAPES = new Set(['rect', 'circle', 'ellipse', 'line', 'text', 'image']);
  const SVG_CONTAINERS = new Set(['svg', 'g']);
  const SVG_IGNORED = new Set(['defs', 'marker', 'title', 'desc', 'style', 'tspan']);
  const INLINE = new Set(['inline', 'contents']);

  const paint = document.createElement('canvas').getContext('2d', { willReadFrequently: true });

  /** Any CSS color to {hex, alpha}, using the browser's own parser. */
  function color(css) {
    paint.clearRect(0, 0, 1, 1);
    paint.fillStyle = '#000';
    paint.fillStyle = css;
    paint.fillRect(0, 0, 1, 1);
    const [r, g, b, a] = paint.getImageData(0, 0, 1, 1).data;
    if (a === 0) return null;
    // Canvas stores premultiplied pixels, so read the exact channels back from the normalized string when opaque.
    const hex = '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('').toUpperCase();
    const m = /rgba?\(([^)]+)\)/.exec(paint.fillStyle);
    const alpha = m && m[1].split(',').length === 4 ? parseFloat(m[1].split(',')[3]) : (a === 255 ? 1 : a / 255);
    return { hex: paint.fillStyle.startsWith('#') ? paint.fillStyle.toUpperCase() : hex, alpha };
  }

  function withOpacity(c, opacity) {
    return c && opacity < 1 ? { hex: c.hex, alpha: +(c.alpha * opacity).toFixed(4) } : c;
  }

  /** Product of the opacity of an element and all its ancestors up to the slide. */
  function opacityOf(el, root) {
    let o = 1;
    for (let e = el; e && e !== root.parentElement; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity);
    return o;
  }

  function label(el) {
    const text = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 30);
    const cls = el.getAttribute('class');
    return `<${el.tagName.toLowerCase()}${cls ? '.' + cls.split(/\s+/).join('.') : ''}>${text ? ' "' + text + '"' : ''}`;
  }

  function extractSlide(root) {
    const frame = root.getBoundingClientRect();
    const W = frame.width;
    const problems = [];
    const elements = [];
    const u = v => +(v / W).toFixed(6);
    const box = r => ({ x: u(r.left - frame.left), y: u(r.top - frame.top), w: u(r.width), h: u(r.height) });
    const bad = (el, why) => problems.push(`${why}: ${label(el)}`);

    function fontOf(cs, scale = 1) {
      const family = cs.fontFamily.split(',')[0].trim().replace(/^["']|["']$/g, '');
      const px = parseFloat(cs.fontSize) * scale;
      if (!document.fonts.check(`${cs.fontWeight} ${cs.fontSize} "${family}"`)) problems.push(`font not loaded: ${family} ${cs.fontWeight}`);
      return {
        font: family,
        size: u(px),
        weight: parseInt(cs.fontWeight, 10) || 400,
        italic: cs.fontStyle === 'italic',
        underline: cs.textDecorationLine.includes('underline'),
      };
    }

    /** The font's ascent and descent at this size: the baseline's distance from the top and bottom of its glyph box. */
    function fontMetrics(el, cs, scale = 1) {
      const probe = document.createElement('span');
      probe.textContent = 'Hg';
      probe.style.cssText = `position:absolute;visibility:hidden;white-space:nowrap;line-height:normal;font:${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
      const mark = document.createElement('span');
      mark.style.cssText = 'display:inline-block;width:0;height:0';
      probe.appendChild(mark);
      document.body.appendChild(probe);
      const r = probe.getBoundingClientRect();
      const ascent = mark.getBoundingClientRect().bottom - r.top;
      const metrics = { ascent: u(ascent * scale), descent: u((r.height - ascent) * scale) };
      probe.remove();
      return metrics;
    }

    // ---- HTML ----

    function htmlBox(el, cs, opacity) {
      const fill = withOpacity(color(cs.backgroundColor), opacity);
      const widths = ['Top', 'Right', 'Bottom', 'Left'].map(s => cs[`border${s}Style`] === 'none' ? 0 : parseFloat(cs[`border${s}Width`]));
      const hasBorder = widths.some(w => w > 0);
      if (cs.backgroundImage !== 'none') bad(el, 'background image or gradient');
      if (cs.boxShadow !== 'none') bad(el, 'box shadow');
      if (cs.filter !== 'none' || cs.backdropFilter !== 'none') bad(el, 'filter');
      if (cs.clipPath !== 'none' || cs.maskImage !== 'none') bad(el, 'clip path or mask');
      if (cs.transform !== 'none') bad(el, 'CSS transform');
      if (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) bad(el, 'outline (use border)');
      if (!fill && !hasBorder) return;
      let stroke = null;
      if (hasBorder) {
        const colors = ['Top', 'Right', 'Bottom', 'Left'].map(s => cs[`border${s}Color`]);
        const styles = ['Top', 'Right', 'Bottom', 'Left'].map(s => cs[`border${s}Style`]);
        if (new Set(widths).size > 1 || new Set(colors).size > 1 || new Set(styles).size > 1) bad(el, 'border differs between sides (draw a line instead)');
        if (!['solid', 'dashed', 'dotted'].includes(styles[0])) bad(el, `border style ${styles[0]}`);
        stroke = { ...withOpacity(color(colors[0]), opacity), width: u(widths[0]), dash: styles[0] };
      }
      const r = el.getBoundingClientRect();
      const radii = ['TopLeft', 'TopRight', 'BottomRight', 'BottomLeft'].map(c => cs[`border${c}Radius`]);
      if (new Set(radii).size > 1) bad(el, 'corner radius differs between corners');
      const px = (v, side) => (v.endsWith('%') ? parseFloat(v) / 100 * side : parseFloat(v));
      const parts = radii[0].split(' ');
      const rx = px(parts[0], r.width), ry = px(parts[1] || parts[0], r.height);
      const radius = Math.min(rx, ry, r.width / 2, r.height / 2);
      const round = radius >= Math.min(r.width, r.height) / 2 - 0.01;
      // A CSS border sits inside the box, a native outline is centered on its edge: inset by half the stroke.
      const half = stroke ? widths[0] / 2 : 0;
      const geo = box({ left: r.left + half, top: r.top + half, width: r.width - 2 * half, height: r.height - 2 * half });
      if (round && Math.abs(r.width - r.height) < 0.01 * r.width + 0.5) {
        elements.push({ type: 'ellipse', ...geo, fill, stroke });
      } else {
        elements.push({ type: 'rect', ...geo, radius: u(Math.max(0, radius - half)), fill, stroke });
      }
    }

    /** True when the element lays out its own lines of text (it has inline content with real text). */
    function isTextBlock(el) {
      for (const n of el.childNodes) {
        if (n.nodeType === 3 && n.textContent.trim()) return true;
        if (n.nodeType === 1 && INLINE.has(getComputedStyle(n).display) && n.textContent.trim() && n.namespaceURI === el.namespaceURI && n.tagName !== 'BR') return true;
      }
      return false;
    }

    function htmlText(el, cs, opacity) {
      const words = [];  // {text, top, bottom, left, right, style, spaceBefore}
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      const range = document.createRange();
      let spaceBefore = false;  // whether whitespace separates the next word from the previous one
      for (let node = walker.nextNode(); node; node = walker.nextNode()) {
        const parent = node.parentElement;
        const pcs = getComputedStyle(parent);
        if (pcs.display === 'none' || pcs.visibility === 'hidden') continue;
        if (parent !== el && !INLINE.has(pcs.display)) bad(parent, 'block or inline-block nested inside a text block');
        if (pcs.textTransform !== 'none') bad(parent, 'text-transform (write the final letters)');
        if (parseFloat(pcs.letterSpacing) || 0) bad(parent, 'letter-spacing');
        if (pcs.textShadow !== 'none') bad(parent, 'text shadow');
        if (color(pcs.backgroundColor) && parent !== el) bad(parent, 'background on inline text');
        const style = { ...fontOf(pcs), color: withOpacity(color(pcs.color), opacityOf(parent, root)) };
        const re = /\S+/g;
        for (let m = re.exec(node.textContent); m; m = re.exec(node.textContent)) {
          range.setStart(node, m.index);
          range.setEnd(node, m.index + m[0].length);
          const rects = [...range.getClientRects()].filter(r => r.width > 0);
          if (!rects.length) continue;
          if (rects.length > 1 && Math.abs(rects[0].top - rects[rects.length - 1].top) > 1) bad(parent, `word "${m[0].slice(0, 20)}" breaks across lines`);
          const r = rects[0];
          const glued = words.length > 0 && m.index === 0 && !spaceBefore;
          words.push({ text: m[0], top: r.top, bottom: r.bottom, left: r.left, right: rects[rects.length - 1].right, style, glued });
        }
        if (node.textContent) spaceBefore = /\s$/.test(node.textContent);
      }
      if (!words.length) return;
      // Group words into rendered lines by vertical overlap.
      const lines = [];
      for (const w of words) {
        const mid = (w.top + w.bottom) / 2;
        const last = lines[lines.length - 1];
        if (last && mid > last.top && mid < last.bottom) {
          last.words.push(w); last.top = Math.min(last.top, w.top); last.bottom = Math.max(last.bottom, w.bottom);
        } else lines.push({ top: w.top, bottom: w.bottom, words: [w] });
      }
      const specLines = lines.map(line => {
        const runs = [];
        line.words.forEach((w, i) => {
          const sep = i === 0 || w.glued ? '' : ' ';
          const prev = runs[runs.length - 1];
          if (prev && JSON.stringify(prev.style) === JSON.stringify(w.style)) prev.text += sep + w.text;
          else {
            if (prev && sep) prev.text += sep;
            runs.push({ text: w.text, style: w.style });
          }
        });
        return runs.map(r => ({ text: r.text, ...r.style }));
      });
      const pad = ['Left', 'Right'].map(s => parseFloat(cs[`padding${s}`]) + (cs[`border${s}Style`] === 'none' ? 0 : parseFloat(cs[`border${s}Width`])));
      const er = el.getBoundingClientRect();
      const left = er.left + pad[0], width = er.width - pad[0] - pad[1];
      const first = lines[0], last = lines[lines.length - 1];
      const advance = lines.length > 1 ? (last.top - first.top) / (lines.length - 1) : parseFloat(cs.lineHeight) || (first.bottom - first.top);
      const align = { left: 'start', start: 'start', right: 'end', end: 'end', center: 'center', justify: 'start' }[cs.textAlign] || 'start';
      if (cs.textAlign === 'justify') bad(el, 'justified text');
      if (cs.writingMode !== 'horizontal-tb') bad(el, 'vertical writing mode');
      const inkLeft = Math.min(...words.map(w => w.left)), inkRight = Math.max(...words.map(w => w.right));
      elements.push({
        type: 'text',
        ...box({ left, top: first.top, width, height: last.bottom - first.top }),
        align,
        lineAdvance: u(advance),
        glyphBox: u(first.bottom - first.top),
        ...fontMetrics(el, cs),
        ink: { x: u(inkLeft - frame.left), w: u(inkRight - inkLeft) },
        lines: specLines,
      });
    }

    function htmlImage(el, cs, opacity) {
      if (cs.objectFit !== 'fill' && cs.objectFit !== 'contain' && cs.objectFit !== 'cover') bad(el, `object-fit ${cs.objectFit}`);
      const r = el.getBoundingClientRect();
      const ratio = el.naturalWidth / el.naturalHeight;
      if (el.naturalWidth && Math.abs(ratio - r.width / r.height) > 0.01 * ratio) bad(el, 'image box has a different aspect ratio from the image (crop the file instead)');
      if (parseFloat(cs.borderTopLeftRadius)) bad(el, 'rounded image (round the file instead)');
      if (opacity < 1) bad(el, 'transparent image (bake the opacity into the file)');
      elements.push({ type: 'image', ...box(r), src: el.currentSrc || el.src });
    }

    function html(el) {
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') return;
      const opacity = opacityOf(el, root);
      if (el.tagName === 'IMG') return htmlImage(el, cs, opacity);
      if (el.tagName.toLowerCase() === 'svg') return svg(el);
      if (['CANVAS', 'VIDEO', 'IFRAME', 'OBJECT', 'EMBED', 'INPUT', 'BUTTON', 'SELECT', 'TEXTAREA'].includes(el.tagName)) return bad(el, `<${el.tagName.toLowerCase()}> element`);
      for (const pseudo of ['::before', '::after']) {
        const content = getComputedStyle(el, pseudo).content;
        if (content !== 'none' && content !== 'normal') bad(el, `${pseudo} content (use a real element)`);
      }
      if (cs.overflow !== 'visible' && el !== root && el.scrollWidth > el.clientWidth + 1) bad(el, 'content clipped by overflow');
      if (el !== root) htmlBox(el, cs, opacity);
      if (isTextBlock(el)) return htmlText(el, cs, opacity);
      const kids = [...el.children];
      const z = k => { const c = getComputedStyle(k); return c.position === 'static' || c.zIndex === 'auto' ? 0 : parseInt(c.zIndex, 10); };
      if (kids.some(k => z(k) !== 0)) bad(el, 'z-index (order elements in the source instead)');
      kids.forEach(html);
    }

    // ---- SVG ----

    function svgPaint(el, cs, opacity) {
      const fillOpacity = parseFloat(cs.fillOpacity), strokeOpacity = parseFloat(cs.strokeOpacity);
      if (/url\(/.test(cs.fill) || /url\(/.test(cs.stroke)) bad(el, 'gradient or pattern paint');
      if (cs.filter !== 'none') bad(el, 'filter');
      const fill = cs.fill === 'none' ? null : withOpacity(color(cs.fill), opacity * fillOpacity);
      const scale = Math.hypot(el.getScreenCTM().a, el.getScreenCTM().b);
      const sw = parseFloat(cs.strokeWidth) * scale;
      let stroke = null;
      if (cs.stroke !== 'none' && sw > 0) {
        const c = withOpacity(color(cs.stroke), opacity * strokeOpacity);
        const dash = cs.strokeDasharray === 'none' ? 'solid' : (parseFloat(cs.strokeDasharray) <= parseFloat(cs.strokeWidth) * 1.5 ? 'dotted' : 'dashed');
        stroke = c && { ...c, width: u(sw), dash };
      }
      return { fill, stroke, scale };
    }

    function svgShape(el) {
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') return;
      const tag = el.tagName.toLowerCase();
      const opacity = opacityOf(el, root);
      const m = el.getScreenCTM();
      const skewed = Math.abs(m.a * m.c + m.b * m.d) > 1e-6 || Math.abs(Math.hypot(m.a, m.b) - Math.hypot(m.c, m.d)) > 1e-6;
      const rotated = Math.abs(m.b) > 1e-6;
      if (skewed) bad(el, 'skewed or unevenly scaled SVG transform');
      const pt = (x, y) => { const p = new DOMPoint(x, y).matrixTransform(m); return { x: u(p.x - frame.left), y: u(p.y - frame.top) }; };
      const num = name => el[name].baseVal.value;

      if (tag === 'line') {
        const { stroke } = svgPaint(el, cs, opacity);
        if (!stroke) return;
        const a = pt(num('x1'), num('y1')), b = pt(num('x2'), num('y2'));
        const len = Math.hypot(b.x - a.x, b.y - a.y) || 1;
        // A draft arrowhead starts where the line ends, a native one ends there: stretch the line to the head's tip.
        const arrow = (v, end, sign) => {
          if (v === 'none') return null;
          const marker = document.querySelector(/url\(["']?(#[^"')]+)/.exec(v)?.[1] || 'none');
          if (!marker) { bad(el, 'arrow marker not found'); return null; }
          const vb = marker.viewBox.baseVal, mw = marker.markerWidth.baseVal.value;
          const perUnit = marker.markerUnits.baseVal === 1 ? 1 / W : stroke.width;  // 1 = userSpaceOnUse
          const tip = (vb.width ? (vb.width - marker.refX.baseVal.value) / vb.width : 1) * mw * perUnit * (marker.markerUnits.baseVal === 1 ? Math.hypot(m.a, m.b) : 1);
          end.x = +(end.x + sign * (b.x - a.x) / len * tip).toFixed(6);
          end.y = +(end.y + sign * (b.y - a.y) / len * tip).toFixed(6);
          return 'arrow';
        };
        const arrowStart = arrow(cs.markerStart, a, -1), arrowEnd = arrow(cs.markerEnd, b, 1);
        if (!['butt', 'round', 'square'].includes(cs.strokeLinecap)) bad(el, 'line cap');
        elements.push({ type: 'line', x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke, arrowStart, arrowEnd });
        return;
      }
      if (rotated) bad(el, 'rotated shape (only lines may be at an angle)');
      if (cs.markerStart !== 'none' || cs.markerEnd !== 'none') bad(el, 'marker on a shape that is not a line');
      const r = el.getBoundingClientRect();
      if (tag === 'rect') {
        const { fill, stroke, scale } = svgPaint(el, cs, opacity);
        if (!fill && !stroke) return;
        // getBoundingClientRect covers the fill box only in SVG, so rebuild it from the geometry.
        const a = pt(num('x'), num('y')), b = pt(num('x') + num('width'), num('y') + num('height'));
        const rx = el.rx.baseVal.value, ry = el.ry.baseVal.value;
        if (rx && ry && Math.abs(rx - ry) > 0.01) bad(el, 'rx differs from ry');
        const w = b.x - a.x, h = b.y - a.y;
        elements.push({ type: 'rect', x: a.x, y: a.y, w: +w.toFixed(6), h: +h.toFixed(6), radius: Math.min(u((rx || ry) * scale), w / 2, h / 2), fill, stroke });
      } else if (tag === 'circle' || tag === 'ellipse') {
        const { fill, stroke } = svgPaint(el, cs, opacity);
        if (!fill && !stroke) return;
        const rx = tag === 'circle' ? num('r') : num('rx'), ry = tag === 'circle' ? num('r') : num('ry');
        const a = pt(num('cx') - rx, num('cy') - ry), b = pt(num('cx') + rx, num('cy') + ry);
        elements.push({ type: 'ellipse', x: a.x, y: a.y, w: +(b.x - a.x).toFixed(6), h: +(b.y - a.y).toFixed(6), fill, stroke });
      } else if (tag === 'image') {
        if (opacity < 1) bad(el, 'transparent image (bake the opacity into the file)');
        elements.push({ type: 'image', ...box(r), src: new URL(el.href.baseVal, document.baseURI).href });
      } else if (tag === 'text') {
        svgText(el, cs, opacity, Math.hypot(m.a, m.b));
      }
    }

    function svgText(el, cs, opacity, scale) {
      if (cs.stroke !== 'none' && parseFloat(cs.strokeWidth) > 0) bad(el, 'stroked text');
      if (parseFloat(cs.letterSpacing) || 0) bad(el, 'letter-spacing');
      if ([...el.querySelectorAll('tspan')].some(t => t.hasAttribute('x') || t.hasAttribute('y') || t.hasAttribute('dy'))) bad(el, 'positioned <tspan> (use one <text> per line)');
      if (el.querySelector('textPath')) bad(el, 'text on a path');
      const runs = [];
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      for (let node = walker.nextNode(); node; node = walker.nextNode()) {
        const pcs = getComputedStyle(node.parentElement);
        const text = node.textContent.replace(/\s+/g, ' ');
        if (text) runs.push({ text, ...fontOf(pcs, scale), color: withOpacity(color(pcs.fill), opacityOf(node.parentElement, root) * parseFloat(pcs.fillOpacity)) });
      }
      if (!runs.length) return;
      runs[0].text = runs[0].text.trimStart();
      runs[runs.length - 1].text = runs[runs.length - 1].text.trimEnd();
      const r = el.getBoundingClientRect();
      const align = { start: 'start', middle: 'center', end: 'end' }[cs.textAnchor] || 'start';
      const h = u(r.height);
      elements.push({
        type: 'text', ...box(r), align, lineAdvance: h, glyphBox: h, ...fontMetrics(el, cs, scale),
        ink: { x: u(r.left - frame.left), w: u(r.width) }, lines: [runs.filter(x => x.text)], single: true,
      });
    }

    function svg(el) {
      const tag = el.tagName.toLowerCase();
      if (SVG_IGNORED.has(tag)) return;
      if (SVG_CONTAINERS.has(tag)) {
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') return;
        if (cs.filter !== 'none') bad(el, 'filter');
        if (cs.clipPath !== 'none' || cs.maskImage !== 'none' || el.hasAttribute('mask')) bad(el, 'clip path or mask');
        return [...el.children].forEach(svg);
      }
      if (SVG_SHAPES.has(tag)) return svgShape(el);
      bad(el, `<${tag}> is not in the shape vocabulary`);
    }

    const rcs = getComputedStyle(root);
    if (rcs.backgroundImage !== 'none') bad(root, 'slide background image or gradient (use an <img> or a flat color)');
    html(root);
    return {
      spec: {
        id: root.dataset.slide || null,
        draft: root.dataset.draft || null,
        notes: root.dataset.notes || '',
        aspect: +(frame.height / frame.width).toFixed(6),
        background: color(rcs.backgroundColor) || { hex: '#FFFFFF', alpha: 1 },
        elements,
      },
      problems: [...new Set(problems)],
    };
  }

  /** Layout problems a reviewer would notice: text off the slide, text on text, text spilling out of its card. */
  function layoutProblems(spec, rules) {
    const out = [];
    const minPad = rules.minPad || 0;
    const texts = spec.elements.filter(e => e.type === 'text');
    const name = t => '"' + t.lines.map(l => l.map(r => r.text).join('')).join(' ').slice(0, 24) + '"';
    const ink = t => ({ x: t.ink.x, y: t.y, w: t.ink.w, h: t.h });
    const eps = 0.0005;
    texts.forEach((t, i) => {
      const a = ink(t);
      for (const run of t.lines.flat()) {
        if (rules.minText && run.size < rules.minText - 1e-5) out.push(`text below the deck's minimum size: ${name(t)}`);
        for (const ch of rules.banned || []) if (run.text.includes(ch)) out.push(`banned character ${JSON.stringify(ch)}: ${name(t)}`);
      }
      if (a.x < -eps || a.y < -eps || a.x + a.w > 1 + eps || a.y + a.h > spec.aspect + eps) out.push(`text off the slide: ${name(t)}`);
      for (const s of texts.slice(i + 1)) {
        const b = ink(s);
        if (a.x < b.x + b.w - eps && b.x < a.x + a.w - eps && a.y < b.y + b.h - eps && b.y < a.y + a.h - eps) out.push(`text overlaps text: ${name(t)} and ${name(s)}`);
      }
      // The smallest filled box holding the text's center is its card: the text must stay inside it, with padding.
      const cx = a.x + a.w / 2, cy = a.y + a.h / 2;
      const cards = spec.elements.slice(0, spec.elements.indexOf(t))
        .filter(e => (e.type === 'rect' || e.type === 'ellipse') && e.fill && cx > e.x && cx < e.x + e.w && cy > e.y && cy < e.y + e.h)
        .sort((p, q) => p.w * p.h - q.w * q.h);
      if (cards.length) {
        const c = cards[0];
        const gap = Math.min(a.x - c.x, c.x + c.w - a.x - a.w);
        if (gap < -eps) out.push(`text spills out of its box: ${name(t)}`);
        else if (gap < minPad - eps) out.push(`text too close to its box edge: ${name(t)}`);
      }
    });
    return out;
  }

  window.deckBuilder = {
    slides: () => [...document.querySelectorAll('.slide')],
    extract: i => extractSlide(window.deckBuilder.slides()[i]),
    // rules come from the deck's own plan: {minPad, minText} as fractions of slide width, {banned} as characters.
    check: (rules = {}) => window.deckBuilder.slides().map((el, i) => {
      const { spec, problems } = extractSlide(el);
      return { index: i, id: spec.id, draft: spec.draft, problems: [...new Set(problems.concat(layoutProblems(spec, rules)))], spec };
    }),
  };
})();
