// Cloudflare Worker: /api/vt och /api/sl hanteras av lib/, allt annat serveras från public/.
import * as vt from "./lib/vt.mjs";
import * as sl from "./lib/sl.mjs";

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    if (pathname === "/api/vt") return vt.handle(request, env);
    if (pathname === "/api/sl") return sl.handle(request, env);
    return env.ASSETS.fetch(request);
  },
};
