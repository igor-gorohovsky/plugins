# PR screenshots

GitHub has no API to attach images. Upload each screenshot to the Cloudflare R2 bucket `github-screenshots` and put its public link in the PR body.

The key is `<branch>/<8 random hex chars>.png`. It must have the random part: the bucket is public with no listing, so a key nobody can guess is the only protection.

## With the Cloudflare MCP (`cloudflare` server, Claude Code)

Upload from a REPL script, so the image bytes never pass through your context. Read the file to base64 in the script and send it with the `execute` tool, which runs code against the Cloudflare API:

```js
const key = `<branch>/${(await $`openssl rand -hex 4`.text()).trim()}.png`;
const b64 = (await $`base64 -w0 <path>`.text()).trim();
await tools.mcp__cloudflare__execute({code: `async () => {
  const body = Uint8Array.from(atob('${b64}'), c => c.charCodeAt(0));
  const r = await cloudflare.request({method: 'PUT', path: \`/accounts/\${accountId}/r2/buckets/github-screenshots/objects/${key}\`, headers: {'Content-Type': 'image/png'}, body});
  return r.success;
}`});
```

Never paste base64 into a tool call by hand. Use `video/mp4` as the content type for a recording.

## With curl (an exe.dev VM with the `r2-screenshots` integration)

Works from any process, pi and Codex included, with no credential on the VM: the integration adds the token.

```sh
key="<branch>/$(openssl rand -hex 4).png"
curl -sf -X PUT -H 'Content-Type: image/png' --data-binary @<path> \
  "https://r2-screenshots.int.exe.xyz/client/v4/accounts/78246d281fab6812694376558beb43fa/r2/buckets/github-screenshots/objects/$key"
```

## With wrangler (no MCP, logged in to Cloudflare)

```sh
bunx wrangler r2 object put "github-screenshots/$key" --file=<path> --content-type=image/png --remote
```

`--remote` is necessary. Without it, wrangler writes to the local simulator.

## In the PR

- Public URL: `https://pub-07cc2e1863834d319b66aa5802c66ea3.r2.dev/<key>`.
- Fetch each URL once and make sure that it returns `200` before you use it in the body.

Put screenshots in a markdown table, never as bare images. Select columns that fit the change, such as Before/After or one column per screen:

```
| Before | After |
| --- | --- |
| ![before](https://pub-07cc2e1863834d319b66aa5802c66ea3.r2.dev/ag-51/a1b2c3d4.png) | ![after](https://pub-07cc2e1863834d319b66aa5802c66ea3.r2.dev/ag-51/e5f6a7b8.png) |
```

When the UI changes after the PR opens, take the screenshots again and replace them.
