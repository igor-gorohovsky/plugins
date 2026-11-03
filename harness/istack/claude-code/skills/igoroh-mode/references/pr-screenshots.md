# PR screenshots

GitHub has no API to attach images. Upload each screenshot to Cloudflare R2 and put the public link in the PR body.

```sh
key="<branch>/$(openssl rand -hex 4).png"
bunx wrangler r2 object put "github-screenshots/$key" --file=<path> --content-type=image/png --remote
```

- Public URL: `https://pub-07cc2e1863834d319b66aa5802c66ea3.r2.dev/<key>`.
- `--remote` is necessary. Without it, wrangler writes to the local simulator.
- The key must have the random part. The bucket is public with no listing, so a key that nobody can guess is the only protection.
- Fetch each URL once and make sure that it returns `200` before you use it in the body.

Put screenshots in a markdown table, never as bare images. Select columns that fit the change, such as Before/After or one column per screen:

```
| Before | After |
| --- | --- |
| ![before](https://pub-07cc2e1863834d319b66aa5802c66ea3.r2.dev/ag-51/a1b2c3d4.png) | ![after](https://pub-07cc2e1863834d319b66aa5802c66ea3.r2.dev/ag-51/e5f6a7b8.png) |
```

When the UI changes after the PR opens, take the screenshots again and replace them.
