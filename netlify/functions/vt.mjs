// Netlify-variant av /api/vt. Själva logiken finns i lib/vt.mjs (delas med Cloudflare Pages).
import { handle } from "../../lib/vt.mjs";
export default (req) => handle(req, process.env);
export const config = { path: "/api/vt" };
