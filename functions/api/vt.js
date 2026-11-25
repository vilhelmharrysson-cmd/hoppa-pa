// Cloudflare Pages Function för /api/vt. Själva logiken finns i lib/vt.mjs.
import { handle } from "../../lib/vt.mjs";
export const onRequest = ({ request, env }) => handle(request, env);
