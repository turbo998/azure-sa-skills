---
name: wechat-article
description: Generate WeChat public account (微信公众号) compatible HTML articles. Use when the user wants to write a WeChat article, create gzh content, or convert Markdown or notes into WeChat-compatible HTML.
license: MIT
---

# WeChat Article Skill

Generate a self-contained HTML article that can be pasted into the WeChat public account editor with minimal manual cleanup.

## When to Use

Use this skill when the user asks to:

- write or polish a WeChat public account article
- convert Markdown into WeChat-compatible HTML
- create a long-form Chinese article for sharing in WeChat
- generate a publish-ready article from notes, bullets, or a topic

Typical triggers:

- `用 /wechat-article 写一篇公众号文章`
- `把这段 markdown 转成微信公众号 HTML`
- `生成一篇适合微信排版的技术文章`
- `create a WeChat article from this draft`

## Core Output Requirement

Produce a full HTML document or, if the user explicitly asks for paste-ready content only, produce the `<body>` inner HTML. Default to the full HTML document.

The output must be compatible with the WeChat editor's restrictive HTML sanitizer.

## WeChat Compatibility Rules

### Must do

- Put **all styles inline** with `style=""` on each relevant element.
- Prefer `<section>` instead of `<div>`.
- Keep the body width mobile-friendly with `max-width:680px`.
- Use the font stack `-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",Roboto,sans-serif`.
- Use `line-height:1.8` for body text.
- Use simple, resilient HTML structures.
- If the user provides local image files, embed them only when you can safely convert them to base64; otherwise clearly leave placeholders.

### Must not

- No `<script>` tags.
- No external CSS or `<style>` blocks.
- No flexbox or grid layouts.
- No `position: fixed` or `position: sticky`.
- No `<iframe>`, `<video>`, or `<audio>`.
- No SVG.
- No reliance on CSS classes or IDs for styling.

## Writing Style

- Conversational, warm, and readable on mobile.
- Accurate for technical topics, but not stiff.
- Paragraphs should be short.
- Use emoji sparingly and only when they improve scanability.
- Default to Chinese unless the user asks for English.

## Design System

### Color palette

- Primary green: `#07c160`
- Text primary: `#1a1a1a`
- Text body: `#333333`
- Text secondary: `#555555`
- Muted text: `#888888`
- Background: `#ffffff`
- Light background: `#f7f7f7`
- Border: `#e5e5e5`

### Title block

```html
<h1 style="font-size:22px;font-weight:bold;color:#1a1a1a;text-align:center;margin:30px 0 10px;line-height:1.4;">Title</h1>
<p style="text-align:center;color:#888;font-size:14px;margin-bottom:30px;">Subtitle or tagline</p>
```

### H2 section heading

```html
<h2 style="font-size:18px;font-weight:bold;color:#1a1a1a;margin:35px 0 15px;padding-left:12px;border-left:4px solid #07c160;">
  <span style="display:inline-block;background:#07c160;color:#fff;width:24px;height:24px;line-height:24px;text-align:center;border-radius:50%;font-size:13px;font-weight:bold;margin-right:8px;">1</span>
  Section Title
</h2>
```

### H3 subsection heading

```html
<h3 style="font-size:16px;font-weight:bold;color:#333;margin:25px 0 10px;">Subsection</h3>
```

### Abstract / lead block

```html
<section style="font-size:15px;color:#555;background:#f7f7f7;padding:15px 20px;border-radius:8px;margin:20px 0;line-height:1.9;">
  content here
</section>
```

### Info box

```html
<section style="background:#f0f9ff;border-left:4px solid #3b82f6;padding:15px 20px;margin:20px 0;border-radius:0 8px 8px 0;font-size:14px;">
  content here
</section>
```

### Warning box

```html
<section style="background:#fff7ed;border-left:4px solid #f59e0b;padding:15px 20px;margin:20px 0;border-radius:0 8px 8px 0;font-size:14px;">
  content here
</section>
```

### Success box

```html
<section style="background:#f0fdf4;border-left:4px solid #07c160;padding:15px 20px;margin:20px 0;border-radius:0 8px 8px 0;font-size:14px;">
  content here
</section>
```

### Table style

```html
<table style="width:100%;border-collapse:collapse;margin:15px 0;font-size:14px;">
  <tr>
    <th style="background:#f3f4f6;padding:10px 12px;text-align:left;font-weight:bold;border:1px solid #e5e5e5;">Header</th>
  </tr>
  <tr>
    <td style="padding:10px 12px;border:1px solid #e5e5e5;">Cell</td>
  </tr>
</table>
```

### Inline elements

- Bold: `<strong style="color:#1a1a1a;">text</strong>`
- Positive tag: `<span style="background:#e8f5e9;color:#2e7d32;padding:2px 6px;border-radius:4px;font-size:12px;">tag</span>`
- Warning tag: `<span style="background:#fce4ec;color:#c62828;padding:2px 6px;border-radius:4px;font-size:12px;">warning</span>`

### Footer

```html
<section style="margin-top:30px;padding:20px 25px;background:#f7f7f7;border-radius:8px;text-align:center;line-height:1.9;">
  <p style="font-size:15px;color:#333;margin:0 0 8px;">如果这篇文章对你有帮助，欢迎<strong style="color:#07c160;">点赞、在看、转发</strong>三连。</p>
  <p style="font-size:14px;color:#666;margin:0;">关注我，持续分享 AI 时代的技术实战与深度思考。</p>
</section>
```

## Conversion Rules

If the user provides Markdown or asks for a conversion, map content like this:

- `#` -> title block
- `##` -> numbered H2 section heading
- `###` -> H3 subsection heading
- paragraphs -> `<p>` with inline spacing and color
- blockquotes -> choose info, warning, or abstract blocks based on meaning
- tables -> inline-styled HTML tables
- code blocks -> dark styled `<section>` blocks, not raw fenced Markdown in final output
- lists -> readable bullet paragraphs or stacked `<section>` blocks

## Recommended HTML Skeleton

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Article Title</title>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei','Segoe UI',Roboto,sans-serif;line-height:1.8;color:#333;max-width:680px;margin:0 auto;padding:20px;background:#fff;">
  ...
</body>
</html>
```

## Working Process

1. Determine whether the user gave a topic, rough notes, or an existing draft.
2. If the user gave rough content, write or rewrite the article first.
3. Convert the final content into WeChat-compatible HTML.
4. Keep the structure easy to paste into the WeChat editor.
5. If a title is missing, create a practical, publishable one.

## Output Rules

1. Default to a complete article, not just a fragment.
2. Prioritize readability over decorative layout.
3. Keep all styling inline.
4. Avoid unsupported HTML even if it would look better elsewhere.
5. If the user asks for final delivery, provide the HTML artifact directly or write it to a file when requested.
