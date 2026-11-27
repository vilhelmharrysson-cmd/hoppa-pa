// Cloudflare Worker: /api/vt och /api/sl (realtid) samt resenärernas bidrag och statistik (lib/ugc.mjs)
// hanteras av lib/, allt annat serveras från public/.
import * as vt from "./lib/vt.mjs";
import * as sl from "./lib/sl.mjs";
import * as ugc from "./lib/ugc.mjs";

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    if (pathname === "/api/vt") return vt.handle(request, env);
    if (pathname === "/api/sl") return sl.handle(request, env);
    if (["/api/feedback", "/api/ugc", "/api/hit", "/api/admin"].includes(pathname)) return ugc.handle(request, env);
    return env.ASSETS.fetch(request);
  },
};
