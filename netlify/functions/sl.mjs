// Netlify-variant av /api/sl. Själva logiken finns i lib/sl.mjs (delas med Cloudflare Pages).
import { handle } from "../../lib/sl.mjs";
export default (req) => handle(req, process.env);
export const config = { path: "/api/sl" };
